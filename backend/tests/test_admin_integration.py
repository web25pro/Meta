"""Integration + security tests for the admin panel (Overall_Admin only)."""
import asyncio
import uuid

import httpx
from httpx import ASGITransport

from app.main import app
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password, create_access_token
from app.models import User, UserRole, UserType

PASSED, FAILED = 0, 0


def check(name, cond, detail=""):
    global PASSED, FAILED
    if cond:
        PASSED += 1; print(f"  PASS  {name}")
    else:
        FAILED += 1; print(f"  FAIL  {name}  {detail}")


async def make_user(role: UserRole, points=0.0):
    async with AsyncSessionLocal() as db:
        u = User(
            name="Admin" if role == UserRole.OVERALL_ADMIN else "User",
            email=f"{role.value}_{uuid.uuid4().hex[:8]}@mj.test",
            username=f"u_{uuid.uuid4().hex[:8]}", password_hash=hash_password("Password123!"),
            role=role, user_type=UserType.COMMUNITY_USER, email_verified=True, is_active=True, points=points,
        )
        db.add(u); await db.commit(); await db.refresh(u)
        return u, create_access_token(str(u.id), u.role.value, u.user_type.value)


async def main():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        admin, atoken = await make_user(UserRole.OVERALL_ADMIN)
        user, utoken = await make_user(UserRole.COMMUNITY_USER, points=100)
        A = {"Authorization": f"Bearer {atoken}"}
        U = {"Authorization": f"Bearer {utoken}"}

        print("\n[Security] admin gate")
        r = await c.get("/api/v1/admin/overview")
        check("no token -> denied", r.status_code in (401, 403), f"got {r.status_code}")
        r = await c.get("/api/v1/admin/overview", headers=U)
        check("non-admin -> 403", r.status_code == 403, f"got {r.status_code}")
        r = await c.get("/api/v1/admin/overview", headers=A)
        check("admin -> 200", r.status_code == 200, r.text[:160])
        check("overview has metrics", "total_users" in r.json() and "pp_issued" in r.json(), str(r.json())[:160])

        print("\n[Users]")
        r = await c.get("/api/v1/admin/users", headers=A)
        check("list users 200", r.status_code == 200 and r.json()["total"] >= 2, str(r.json().get("total")))
        r = await c.patch(f"/api/v1/admin/users/{user.id}", json={"is_active": False}, headers=A)
        check("ban user 200", r.status_code == 200 and r.json()["is_banned"] is True, r.text[:160])
        r = await c.post(f"/api/v1/admin/users/{user.id}/points", json={"amount": 500, "reason": "grant"}, headers=A)
        check("credit PP 200", r.status_code == 200, r.text[:160])
        r = await c.post(f"/api/v1/admin/users/{user.id}/points", json={"amount": -200, "reason": "clawback"}, headers=A)
        check("debit PP 200", r.status_code == 200, r.text[:160])

        print("\n[Quests]")
        r = await c.post("/api/v1/admin/quests", json={"title": "Admin test quest", "pp_reward": 75, "category": "social"}, headers=A)
        check("create quest 200", r.status_code == 200, r.text[:160])
        qid = r.json()["id"]
        # user-facing list should now include it
        r = await c.get("/api/v1/quests", headers=U)
        check("quest visible to users", any(q["id"] == qid for q in r.json()["quests"]), "not found")
        r = await c.patch(f"/api/v1/admin/quests/{qid}", json={"pp_reward": 120, "is_active": False}, headers=A)
        check("update quest 200", r.status_code == 200 and r.json()["pp_reward"] == 120, r.text[:160])
        r = await c.delete(f"/api/v1/admin/quests/{qid}", headers=A)
        check("delete quest 200", r.status_code == 200, r.text[:160])

        print("\n[Partners & campaigns]")
        r = await c.post("/api/v1/admin/partners", json={"name": "TestBrand", "tier": "gold"}, headers=A)
        check("create partner 200", r.status_code == 200, r.text[:160])
        pid = r.json()["id"]
        r = await c.post("/api/v1/admin/campaigns", json={"partner_id": pid, "title": "Test campaign", "pp_budget": 10000, "pp_per_task": 100, "days": 10}, headers=A)
        check("create campaign 200", r.status_code == 200 and r.json().get("brand") == "TestBrand", r.text[:160])
        camp_id = r.json()["id"]
        r = await c.patch(f"/api/v1/admin/campaigns/{camp_id}", json={"status": "paused"}, headers=A)
        check("pause campaign 200", r.status_code == 200 and r.json()["status"] == "paused", r.text[:160])

        print("\n[NFT grant]")
        r = await c.post("/api/v1/admin/nft/grant", json={"user_id": str(user.id), "tier": "epic", "daily_pp_rate": 40}, headers=A)
        check("grant NFT 200", r.status_code == 200 and r.json()["tier"] == "epic", r.text[:160])
        r = await c.get("/api/v1/nft", headers=U)
        check("NFT shows in user vault", r.json()["total"] == 1 and r.json()["total_daily_yield"] == 40, str(r.json()))

        print("\n[Security] write also gated")
        r = await c.post("/api/v1/admin/quests", json={"title": "x", "pp_reward": 1}, headers=U)
        check("non-admin cannot create quest", r.status_code == 403, f"got {r.status_code}")

    print(f"\n==== ADMIN RESULTS: {PASSED} passed, {FAILED} failed ====")
    return FAILED


if __name__ == "__main__":
    raise SystemExit(1 if asyncio.run(main()) else 0)
