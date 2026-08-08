"""Integration tests for the campaign domain — earn loop, budget, targeting.

Run against a live Postgres with migrations applied:
    python -m tests.test_campaign_integration
"""
import asyncio
import uuid

import httpx
from httpx import ASGITransport
from sqlalchemy import select

from app.main import app
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password, create_access_token
from app.models import User, UserRole, UserType, Partner, Campaign, CampaignTask

PASSED, FAILED = 0, 0


def check(name, cond, detail=""):
    global PASSED, FAILED
    if cond:
        PASSED += 1; print(f"  PASS  {name}")
    else:
        FAILED += 1; print(f"  FAIL  {name}  {detail}")


async def make_user(role: UserRole, points=0.0, region=None):
    async with AsyncSessionLocal() as db:
        u = User(
            name="Admin" if role == UserRole.OVERALL_ADMIN else "User",
            email=f"camp_{uuid.uuid4().hex[:8]}@mj.test",
            username=f"c_{uuid.uuid4().hex[:8]}", password_hash=hash_password("Password123!"),
            role=role, user_type=UserType.COMMUNITY_USER, email_verified=True,
            is_active=True, points=points, region=region,
        )
        db.add(u); await db.commit(); await db.refresh(u)
        return u, create_access_token(str(u.id), u.role.value, u.user_type.value)


async def user_points(user_id) -> float:
    async with AsyncSessionLocal() as db:
        u = (await db.execute(select(User).where(User.id == user_id))).scalar_one()
        return float(u.points)


async def campaign_row(campaign_id):
    async with AsyncSessionLocal() as db:
        return (await db.execute(
            select(Campaign).where(Campaign.id == uuid.UUID(str(campaign_id)))
        )).scalar_one()


async def main():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        admin, atoken = await make_user(UserRole.OVERALL_ADMIN)
        user, utoken = await make_user(UserRole.COMMUNITY_USER, region="NG")
        A = {"Authorization": f"Bearer {atoken}"}
        U = {"Authorization": f"Bearer {utoken}"}

        # ── Setup: partner + campaign ───────────────────────────────────────
        r = await c.post("/api/v1/admin/partners", json={"name": "CampBrand", "tier": "gold"}, headers=A)
        pid = r.json()["id"]

        r = await c.post("/api/v1/admin/campaigns", json={
            "partner_id": pid, "title": "Earn loop campaign", "pp_budget": 1000,
            "pp_per_task": 100, "days": 10,
        }, headers=A)
        check("create campaign 200", r.status_code == 200, r.text[:200])
        camp = r.json()
        cid = camp["id"]
        check("campaign starts as draft", camp["status"] == "draft", camp.get("status"))
        check("campaign has a slug", bool(camp.get("slug")), camp.get("slug"))
        check("pp_reserved starts at 0", camp["pp_reserved"] == 0, camp.get("pp_reserved"))

        print("\n[Lifecycle] draft campaigns are not joinable")
        r = await c.post(f"/api/v1/campaigns/{cid}/join", headers=U)
        check("join draft 400", r.status_code == 400, r.text[:160])
        r = await c.get("/api/v1/campaigns", headers=U)
        check("draft hidden from list", all(x["id"] != cid for x in r.json()["campaigns"]), r.text[:160])

        r = await c.patch(f"/api/v1/admin/campaigns/{cid}/status", json={"status": "active"}, headers=A)
        check("activate campaign 200", r.status_code == 200 and r.json()["status"] == "active", r.text[:160])

        print("\n[Tasks]")
        r = await c.post(f"/api/v1/admin/campaigns/{cid}/tasks", json={
            "title": "Auto task", "pp_reward": 100, "verification_type": "webhook", "daily_limit": 1,
        }, headers=A)
        check("create auto task 200", r.status_code == 200, r.text[:200])
        auto_task = r.json()["id"]

        r = await c.post(f"/api/v1/admin/campaigns/{cid}/tasks", json={
            "title": "Manual task", "pp_reward": 200, "verification_type": "manual", "daily_limit": 1,
        }, headers=A)
        manual_task = r.json()["id"]

        print("\n[Earn loop] must join before completing")
        r = await c.post(f"/api/v1/campaigns/{cid}/tasks/{auto_task}/complete",
                         json={"proof": {"verified": True}}, headers=U)
        check("complete before join 400", r.status_code == 400, r.text[:160])

        r = await c.post(f"/api/v1/campaigns/{cid}/join", headers=U)
        check("join active 200", r.status_code == 200, r.text[:160])
        r = await c.post(f"/api/v1/campaigns/{cid}/join", headers=U)
        check("double join 400", r.status_code == 400, r.text[:160])

        print("\n[Earn loop] auto-approved task credits PP and pp_claimed")
        before = await user_points(user.id)
        r = await c.post(f"/api/v1/campaigns/{cid}/tasks/{auto_task}/complete",
                         json={"proof": {"verified": True}}, headers=U)
        check("complete auto task 200", r.status_code == 200, r.text[:200])
        body = r.json() if r.status_code == 200 else {}
        check("auto task approved", body.get("status") == "approved", body.get("status"))
        after = await user_points(user.id)
        check("PP balance increased", after > before, f"{before} -> {after}")
        row = await campaign_row(cid)
        check("pp_claimed incremented", row.pp_claimed > 0, row.pp_claimed)

        print("\n[Earn loop] bad proof is rejected")
        r = await c.post(f"/api/v1/campaigns/{cid}/tasks/{auto_task}/complete", json={}, headers=U)
        check("webhook task without proof 400", r.status_code == 400, r.text[:160])

        print("\n[Earn loop] daily limit")
        r = await c.post(f"/api/v1/campaigns/{cid}/tasks/{auto_task}/complete",
                         json={"proof": {"verified": True}}, headers=U)
        check("second completion hits daily limit", r.status_code == 400, r.text[:160])

        print("\n[Billing] manual task reserves rather than credits")
        before = await user_points(user.id)
        r = await c.post(f"/api/v1/campaigns/{cid}/tasks/{manual_task}/complete",
                         json={"proof": {"note": "done"}}, headers=U)
        check("complete manual task 200", r.status_code == 200, r.text[:200])
        completion_id = r.json().get("id") if r.status_code == 200 else None
        check("manual task pending", r.json().get("status") == "pending" if r.status_code == 200 else False)
        check("no PP credited yet", await user_points(user.id) == before, "balance moved on pending")
        row = await campaign_row(cid)
        check("pp_reserved incremented", row.pp_reserved > 0, row.pp_reserved)

        print("\n[Billing] approval settles reserved -> claimed")
        reserved_before = row.pp_reserved
        claimed_before = row.pp_claimed
        r = await c.post(f"/api/v1/admin/campaigns/review-queue/{completion_id}",
                         json={"approve": True}, headers=A)
        check("approve completion 200", r.status_code == 200, r.text[:200])
        row = await campaign_row(cid)
        check("pp_reserved released", row.pp_reserved < reserved_before, row.pp_reserved)
        check("pp_claimed settled", row.pp_claimed > claimed_before, row.pp_claimed)
        check("PP credited on approval", await user_points(user.id) > before)

        r = await c.post(f"/api/v1/admin/campaigns/review-queue/{completion_id}",
                         json={"approve": True}, headers=A)
        check("double review 404/400", r.status_code in (400, 404), r.text[:160])

        print("\n[Security] review queue is admin-only")
        r = await c.get("/api/v1/admin/campaigns/review-queue", headers=U)
        check("review queue blocked for user", r.status_code == 403, r.text[:160])

        print("\n[Targeting] region")
        r = await c.post("/api/v1/admin/campaigns", json={
            "partner_id": pid, "title": "NG only", "pp_budget": 500, "pp_per_task": 50,
            "days": 5, "status": "active", "target_regions": ["NG"],
        }, headers=A)
        ng_id = r.json()["id"]

        no_region_user, nrtoken = await make_user(UserRole.COMMUNITY_USER, region=None)
        NR = {"Authorization": f"Bearer {nrtoken}"}
        r = await c.get(f"/api/v1/campaigns/{ng_id}/eligibility", headers=U)
        check("NG user eligible", r.json().get("eligible") is True, r.text[:160])
        r = await c.get(f"/api/v1/campaigns/{ng_id}/eligibility", headers=NR)
        check("region-less user ineligible", r.json().get("eligible") is False, r.text[:160])
        r = await c.post(f"/api/v1/campaigns/{ng_id}/join", headers=NR)
        check("region-less join blocked", r.status_code == 400, r.text[:160])

        print("\n[Billing] budget guard")
        r = await c.post("/api/v1/admin/campaigns", json={
            "partner_id": pid, "title": "Tiny budget", "pp_budget": 10, "pp_per_task": 5,
            "days": 5, "status": "active",
        }, headers=A)
        tiny_id = r.json()["id"]
        r = await c.post(f"/api/v1/admin/campaigns/{tiny_id}/tasks", json={
            "title": "Big reward", "pp_reward": 100, "verification_type": "webhook", "daily_limit": 5,
        }, headers=A)
        tiny_task = r.json()["id"]
        await c.post(f"/api/v1/campaigns/{tiny_id}/join", headers=U)
        r = await c.post(f"/api/v1/campaigns/{tiny_id}/tasks/{tiny_task}/complete",
                         json={"proof": {"verified": True}}, headers=U)
        check("award clamped to budget", r.status_code == 200 and float(r.json()["pp_awarded"]) <= 10, r.text[:200])
        row = await campaign_row(tiny_id)
        check("never overspends budget", row.pp_claimed + row.pp_reserved <= row.pp_budget,
              f"{row.pp_claimed}+{row.pp_reserved} > {row.pp_budget}")
        r = await c.post(f"/api/v1/campaigns/{tiny_id}/tasks/{tiny_task}/complete",
                         json={"proof": {"verified": True}}, headers=U)
        check("exhausted budget blocks completion", r.status_code == 400, r.text[:160])

        print("\n[Lifecycle] paused campaigns reject completions")
        await c.patch(f"/api/v1/admin/campaigns/{cid}/status", json={"status": "paused"}, headers=A)
        r = await c.post(f"/api/v1/campaigns/{cid}/tasks/{auto_task}/complete",
                         json={"proof": {"verified": True}}, headers=U)
        check("paused campaign blocks completion", r.status_code == 400, r.text[:160])

        print("\n[Delete] soft delete releases budget and clears the queue")
        r = await c.post("/api/v1/admin/campaigns", json={
            "partner_id": pid, "title": "Doomed campaign", "pp_budget": 1000,
            "pp_per_task": 100, "days": 5, "status": "active",
        }, headers=A)
        del_id = r.json()["id"]
        r = await c.post(f"/api/v1/admin/campaigns/{del_id}/tasks", json={
            "title": "Manual work", "pp_reward": 100, "verification_type": "manual",
        }, headers=A)
        del_task = r.json()["id"]

        deleter, dtoken = await make_user(UserRole.COMMUNITY_USER, region="NG")
        D = {"Authorization": f"Bearer {dtoken}"}
        await c.post(f"/api/v1/campaigns/{del_id}/join", headers=D)
        await c.post(f"/api/v1/campaigns/{del_id}/tasks/{del_task}/complete",
                     json={"proof": {"note": "pending work"}}, headers=D)
        row = await campaign_row(del_id)
        check("pending reserved before delete", row.pp_reserved > 0, row.pp_reserved)

        r = await c.get("/api/v1/admin/campaigns/review-queue", headers=A)
        in_queue_before = any(x["campaign_id"] == del_id for x in r.json()["completions"])
        check("pending completion is in the queue", in_queue_before)

        balance_before = await user_points(deleter.id)
        r = await c.delete(f"/api/v1/admin/campaigns/{del_id}", headers=A)
        check("delete campaign 200", r.status_code == 200, r.text[:200])
        check("reports rejected pending", r.json().get("rejected_pending") == 1, r.text[:160])

        row = await campaign_row(del_id)
        check("deleted_at set", row.deleted_at is not None)
        check("pp_reserved released", row.pp_reserved == 0, row.pp_reserved)
        check("no PP credited by delete", await user_points(deleter.id) == balance_before)

        r = await c.get("/api/v1/admin/campaigns/review-queue", headers=A)
        check("queue cleared of deleted campaign",
              all(x["campaign_id"] != del_id for x in r.json()["completions"]))

        r = await c.get("/api/v1/campaigns", headers=D)
        check("deleted campaign hidden from users",
              all(x["id"] != del_id for x in r.json()["campaigns"]))
        r = await c.get("/api/v1/admin/campaigns", headers=A)
        check("deleted campaign hidden from admin list",
              all(x["id"] != del_id for x in r.json()))
        r = await c.post(f"/api/v1/campaigns/{del_id}/join", headers=U)
        check("join deleted campaign 400", r.status_code == 400, r.text[:160])
        r = await c.post(f"/api/v1/campaigns/{del_id}/tasks/{del_task}/complete",
                         json={"proof": {"verified": True}}, headers=D)
        check("complete on deleted campaign 400", r.status_code == 400, r.text[:160])
        r = await c.delete(f"/api/v1/admin/campaigns/{del_id}", headers=A)
        check("double delete 404", r.status_code == 404, r.text[:160])

        print("\n[Security] delete is admin-only")
        r = await c.delete(f"/api/v1/admin/campaigns/{cid}", headers=U)
        check("delete blocked for non-admin", r.status_code == 403, r.text[:160])

    print(f"\n{'='*46}\n  {PASSED} passed, {FAILED} failed\n{'='*46}")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
