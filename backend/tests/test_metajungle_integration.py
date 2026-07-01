"""End-to-end integration + security tests for the Meta-Jungle endpoints.

Runs against a live Postgres + the real ASGI app (httpx ASGITransport).
Requires DATABASE_URL/SECRET_KEY/JWT_SECRET_KEY env + `alembic upgrade head`
and `python -m scripts.seed_metajungle` already run.

    python -m tests.test_metajungle_integration
"""
import asyncio
import uuid

import httpx
from httpx import ASGITransport
from sqlalchemy import select

from app.main import app
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password, create_access_token
from app.models import User, UserRole, UserType, Quest, Campaign, Course, PointsTransaction


PASSED, FAILED = 0, 0


def check(name, cond, detail=""):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"  PASS  {name}")
    else:
        FAILED += 1
        print(f"  FAIL  {name}  {detail}")


async def make_user(points=0.0, email=None) -> tuple[User, str]:
    email = email or f"tester_{uuid.uuid4().hex[:8]}@mj.test"
    async with AsyncSessionLocal() as db:
        u = User(
            name="Tester", email=email, username=f"u_{uuid.uuid4().hex[:8]}",
            password_hash=hash_password("Password123!"),
            role=UserRole.COMMUNITY_USER, user_type=UserType.COMMUNITY_USER,
            email_verified=True, is_active=True, points=points,
        )
        db.add(u)
        await db.commit()
        await db.refresh(u)
        token = create_access_token(str(u.id), u.role.value, u.user_type.value)
        return u, token


async def balance(user_id) -> float:
    async with AsyncSessionLocal() as db:
        u = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
        return float(u.points)


async def main():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        user, token = await make_user(points=5000)
        H = {"Authorization": f"Bearer {token}"}

        # ── Security: auth required ──────────────────────────────────────────
        print("\n[Security] auth required")
        for path in ["/api/v1/reputation/me", "/api/v1/quests", "/api/v1/nft",
                     "/api/v1/staking", "/api/v1/marketplace/catalog"]:
            r = await c.get(path)
            check(f"auth enforced (no token): {path}", r.status_code in (401, 403), f"got {r.status_code}")

        r = await c.get("/api/v1/quests", headers={"Authorization": "Bearer garbage.token.x"})
        check("401 with invalid token", r.status_code == 401, f"got {r.status_code}")

        # ── Reputation ───────────────────────────────────────────────────────
        print("\n[Reputation]")
        r = await c.get("/api/v1/reputation/me", headers=H)
        check("reputation 200", r.status_code == 200, r.text[:200])
        rep = r.json()
        check("3 scores in 0..1000", all(0 <= rep[k] <= 1000 for k in
              ["activity_score", "reputation_score", "influence_score"]), str(rep))
        check("role present", rep.get("role") in
              ["Explorer", "Tracker", "Hunter", "Whitelist", "OG Panda", "Alpha OG"], str(rep))

        # ── Quests: list + complete + balance + daily limit ──────────────────
        print("\n[Quests]")
        r = await c.get("/api/v1/quests", headers=H)
        check("quests list 200", r.status_code == 200)
        quests = r.json()["quests"]
        check("quests seeded", len(quests) >= 6, str(len(quests)))
        daily = next(q for q in quests if q["title"] == "Daily check-in")
        before = await balance(user.id)
        r = await c.post(f"/api/v1/quests/{daily['id']}/complete", json={}, headers=H)
        check("complete quest 200", r.status_code == 200, r.text[:200])
        awarded = r.json()["pp_awarded"]
        after = await balance(user.id)
        check("PP credited to balance", abs((after - before) - awarded) < 0.01,
              f"before={before} after={after} awarded={awarded}")
        # daily_limit = 1 -> second attempt rejected
        r = await c.post(f"/api/v1/quests/{daily['id']}/complete", json={}, headers=H)
        check("daily limit enforced (400)", r.status_code == 400, f"got {r.status_code}")

        # ── Marketplace: catalog + redeem + insufficient + balance debit ─────
        print("\n[Marketplace]")
        r = await c.get("/api/v1/marketplace/catalog", headers=H)
        check("catalog 200", r.status_code == 200)
        check("catalog has 16 products", len(r.json()["products"]) == 16)
        before = await balance(user.id)
        r = await c.post("/api/v1/marketplace/redeem",
                         json={"product_id": "air-100", "destination": "+2348000000000"}, headers=H)
        check("redeem 200", r.status_code == 200, r.text[:200])
        red = r.json()
        check("voucher code returned", red["voucher_code"].startswith("MJ-"), str(red))
        after = await balance(user.id)
        check("PP debited 200", abs((before - after) - 200) < 0.01, f"before={before} after={after}")
        r = await c.post("/api/v1/marketplace/redeem",
                         json={"product_id": "gc-amazon-25"}, headers=H)  # 2700 PP, likely insufficient
        # build a poor user to guarantee insufficiency
        poor, ptoken = await make_user(points=10)
        r = await c.post("/api/v1/marketplace/redeem", json={"product_id": "air-100"},
                         headers={"Authorization": f"Bearer {ptoken}"})
        check("insufficient PP rejected (400)", r.status_code == 400, f"got {r.status_code}")
        r = await c.post("/api/v1/marketplace/redeem", json={"product_id": "does-not-exist"}, headers=H)
        check("unknown product rejected (400)", r.status_code == 400, f"got {r.status_code}")

        # ── Staking: create locks PP, list, claim ────────────────────────────
        print("\n[Staking]")
        before = await balance(user.id)
        r = await c.post("/api/v1/staking", json={"pp_amount": 1000, "lock_days": 90}, headers=H)
        check("stake 200", r.status_code == 200, r.text[:200])
        check("stake multiplier 1.5", abs(float(r.json()["multiplier"]) - 1.5) < 0.01, str(r.json()))
        after = await balance(user.id)
        check("PP locked (debited 1000)", abs((before - after) - 1000) < 0.01, f"{before}->{after}")
        r = await c.get("/api/v1/staking", headers=H)
        check("staking list reflects stake", r.json()["total_staked"] >= 1000, str(r.json()))
        r = await c.post("/api/v1/staking", json={"pp_amount": 1000, "lock_days": 45}, headers=H)
        check("invalid lock duration rejected (400)", r.status_code == 400, f"got {r.status_code}")

        # ── P2P: create (escrow fee), list ───────────────────────────────────
        print("\n[P2P]")
        before = await balance(user.id)
        r = await c.post("/api/v1/p2p/orders",
                         json={"side": "sell", "pp_amount": 500, "price": 925, "currency": "NGN",
                               "payment_method": "Bank"}, headers=H)
        check("create sell order 200", r.status_code == 200, r.text[:200])
        after = await balance(user.id)
        check("50 PP listing fee charged", abs((before - after) - 50) < 0.01, f"{before}->{after}")
        r = await c.get("/api/v1/p2p/orders?side=sell", headers=H)
        check("order book lists sell order", any(o["pp_amount"] == 500 for o in r.json()["orders"]), str(r.json())[:200])
        r = await c.post("/api/v1/p2p/orders",
                         json={"side": "invalid", "pp_amount": 1, "price": 1, "payment_method": "x"}, headers=H)
        check("invalid side rejected (422)", r.status_code == 422, f"got {r.status_code}")

        # ── Campaigns: list (with brand) + join + duplicate ──────────────────
        print("\n[Campaigns]")
        r = await c.get("/api/v1/campaigns", headers=H)
        check("campaigns 200", r.status_code == 200)
        camps = r.json()["campaigns"]
        check("campaigns seeded with brand", len(camps) >= 4 and camps[0].get("brand"), str(camps[0]) if camps else "none")
        cid = camps[0]["id"]
        r = await c.post(f"/api/v1/campaigns/{cid}/join", headers=H)
        check("join campaign 200", r.status_code == 200, r.text[:200])
        r = await c.post(f"/api/v1/campaigns/{cid}/join", headers=H)
        check("duplicate join rejected (400)", r.status_code == 400, f"got {r.status_code}")

        # ── Learn: list + quiz pass awards PP once ───────────────────────────
        print("\n[Learn]")
        r = await c.get("/api/v1/learn/courses", headers=H)
        check("courses 200", r.status_code == 200)
        courses = r.json()["courses"]
        check("courses seeded", len(courses) >= 4, str(len(courses)))
        course = courses[0]
        before = await balance(user.id)
        r = await c.post(f"/api/v1/learn/courses/{course['id']}/quiz", json={"answers": [1]}, headers=H)
        check("quiz submit 200", r.status_code == 200, r.text[:200])
        res = r.json()
        check("quiz passed + awarded", res["passed"] and res["pp_awarded"] > 0, str(res))
        after = await balance(user.id)
        check("course PP credited", after > before, f"{before}->{after}")
        r = await c.post(f"/api/v1/learn/courses/{course['id']}/quiz", json={"answers": [1]}, headers=H)
        check("repeat course not re-awarded", r.json()["pp_awarded"] == 0, str(r.json()))

        # ── NFT vault (empty for new user) ───────────────────────────────────
        print("\n[NFT]")
        r = await c.get("/api/v1/nft", headers=H)
        check("nft 200", r.status_code == 200)
        check("nft empty for new user", r.json()["total"] == 0, str(r.json()))

    print(f"\n==== RESULTS: {PASSED} passed, {FAILED} failed ====")
    return FAILED


if __name__ == "__main__":
    rc = asyncio.run(main())
    raise SystemExit(1 if rc else 0)
