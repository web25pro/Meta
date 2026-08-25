"""Admin panel service layer (Overall_Admin only)."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func, desc, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    User, UserRole, PointsTransaction, TransactionType,
    Quest, QuestCompletion, NFTHolding, Partner, Campaign, Redemption, Course,
    TaskSubmission, SubmissionFile, CampaignParticipation, CampaignTask,
    CampaignTaskCompletion, CampaignRanking, P2POrder, Stake,
    LeaderboardCache, Schedule, Announcement,
    PPLedgerEntry, IdempotencyKey, AuditLog, DeadlinePenaltyApplied,
)
from app.services.points_service import PointsService


class AdminService:
    # ── Overview ─────────────────────────────────────────────────────────────
    @staticmethod
    async def overview(db: AsyncSession) -> dict:
        async def count(model, *where):
            q = select(func.count()).select_from(model)
            for w in where:
                q = q.where(w)
            return int((await db.execute(q)).scalar() or 0)

        pp_issued = float((await db.execute(
            select(func.coalesce(func.sum(PointsTransaction.amount), 0)).where(PointsTransaction.amount > 0)
        )).scalar() or 0)
        pp_spent = float((await db.execute(
            select(func.coalesce(func.sum(PointsTransaction.amount), 0)).where(PointsTransaction.amount < 0)
        )).scalar() or 0)

        return {
            "total_users": await count(User, User.deleted_at.is_(None)),
            "banned_users": await count(User, User.is_active.is_(False)),
            "pp_issued": pp_issued,
            "pp_spent": abs(pp_spent),
            "redemptions": await count(Redemption),
            "active_campaigns": await count(Campaign, Campaign.status == "active"),
            "quests": await count(Quest, Quest.deleted_at.is_(None)),
            "quest_completions": await count(QuestCompletion),
            "nfts_held": await count(NFTHolding),
        }

    # ── Users ────────────────────────────────────────────────────────────────
    @staticmethod
    async def list_users(db: AsyncSession, page: int, page_size: int, q: Optional[str]):
        query = select(User).where(User.deleted_at.is_(None))
        if q:
            like = f"%{q}%"
            query = query.where((User.email.ilike(like)) | (User.username.ilike(like)) | (User.name.ilike(like)))
        total = int((await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0)
        rows = (await db.execute(
            query.order_by(desc(User.created_at)).offset((page - 1) * page_size).limit(page_size)
        )).scalars().all()
        users = []
        for u in rows:
            users.append({
                "id": u.id, "name": u.name, "username": u.username, "email": u.email,
                "role": u.role.value if hasattr(u.role, "value") else u.role,
                "user_type": u.user_type.value if hasattr(u.user_type, "value") else u.user_type,
                "points": float(u.points or 0), "is_banned": not u.is_active,
                "is_active": u.is_active, "email_verified": u.email_verified, "created_at": u.created_at,
            })
        return users, total

    @staticmethod
    async def update_user(db: AsyncSession, user_id: uuid.UUID, role: Optional[str], is_active: Optional[bool]):
        u = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not u:
            raise ValueError("User not found")
        if role is not None:
            try:
                u.role = UserRole(role)
            except ValueError:
                raise ValueError("Invalid role")
        if is_active is not None:
            u.is_active = is_active
        await db.flush()
        await db.refresh(u)
        return u

    @staticmethod
    async def adjust_points(db: AsyncSession, user_id: uuid.UUID, amount: float, reason: str):
        u = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
        if not u:
            raise ValueError("User not found")
        tx_type = TransactionType.ADMIN_BONUS if amount >= 0 else TransactionType.ADMIN_PENALTY
        await PointsService.create_transaction(db, user_id, float(amount), tx_type, reason)
        return u

    # ── Quests ───────────────────────────────────────────────────────────────
    @staticmethod
    async def list_quests(db: AsyncSession):
        return list((await db.execute(
            select(Quest).where(Quest.deleted_at.is_(None)).order_by(desc(Quest.created_at))
        )).scalars().all())

    @staticmethod
    async def create_quest(db: AsyncSession, data) -> Quest:
        quest = Quest(**data.model_dump())
        # Default starts_at to now if not provided
        if quest.starts_at is None:
            quest.starts_at = datetime.now(timezone.utc)
        db.add(quest)
        await db.flush()
        await db.refresh(quest)
        return quest

    @staticmethod
    async def update_quest(db: AsyncSession, quest_id: uuid.UUID, data) -> Quest:
        quest = (await db.execute(
            select(Quest).where(Quest.id == quest_id, Quest.deleted_at.is_(None))
        )).scalar_one_or_none()
        if not quest:
            raise ValueError("Quest not found")
        for k, v in data.model_dump(exclude_none=True).items():
            setattr(quest, k, v)
        await db.flush()
        await db.refresh(quest)
        return quest

    @staticmethod
    async def delete_quest(db: AsyncSession, quest_id: uuid.UUID):
        """Soft delete: set deleted_at and deactivate."""
        quest = (await db.execute(
            select(Quest).where(Quest.id == quest_id, Quest.deleted_at.is_(None))
        )).scalar_one_or_none()
        if not quest:
            raise ValueError("Quest not found")
        quest.deleted_at = datetime.now(timezone.utc)
        quest.is_active = False
        await db.flush()

    # ── Partners ─────────────────────────────────────────────────────────────
    # Campaign CRUD moved to app/services/campaign_service.py — see
    # docs/ARCHITECTURE.md for the campaign-service boundary.
    @staticmethod
    async def list_partners(db: AsyncSession):
        return list((await db.execute(select(Partner).order_by(Partner.name))).scalars().all())

    @staticmethod
    async def create_partner(db: AsyncSession, data) -> Partner:
        partner = Partner(**data.model_dump())
        db.add(partner)
        await db.flush()
        await db.refresh(partner)
        return partner

    # ── NFT grant ────────────────────────────────────────────────────────────
    @staticmethod
    async def grant_nft(db: AsyncSession, data) -> NFTHolding:
        u = (await db.execute(select(User).where(User.id == data.user_id))).scalar_one_or_none()
        if not u:
            raise ValueError("User not found")
        nft = NFTHolding(
            user_id=data.user_id, name=data.name, tier=data.tier,
            daily_pp_rate=data.daily_pp_rate, contract_address="admin-grant",
            token_id=uuid.uuid4().hex[:10], last_verified_at=datetime.now(timezone.utc),
        )
        db.add(nft)
        await db.flush()
        await db.refresh(nft)
        return nft

    # ── Completions review ───────────────────────────────────────────────────
    @staticmethod
    async def list_completions(
        db: AsyncSession, status: Optional[str], page: int = 1, page_size: int = 20,
    ) -> tuple[list, int]:
        """List quest completions with user/quest names, paginated."""
        base = []
        if status:
            base.append(QuestCompletion.status == status)

        count_q = select(func.count()).select_from(QuestCompletion)
        for w in base:
            count_q = count_q.where(w)
        total = int((await db.execute(count_q)).scalar() or 0)

        q = (
            select(
                QuestCompletion,
                User.name.label("user_name"),
                User.email.label("user_email"),
                Quest.title.label("quest_title"),
            )
            .join(User, User.id == QuestCompletion.user_id)
            .join(Quest, Quest.id == QuestCompletion.quest_id)
            .order_by(desc(QuestCompletion.created_at))
        )
        for w in base:
            q = q.where(w)
        offset = (page - 1) * page_size
        q = q.offset(offset).limit(page_size)
        rows = (await db.execute(q)).all()

        results = []
        for comp, user_name, user_email, quest_title in rows:
            results.append({
                "id": comp.id,
                "user_id": comp.user_id,
                "quest_id": comp.quest_id,
                "user_name": user_name,
                "user_email": user_email,
                "quest_title": quest_title,
                "status": comp.status,
                "pp_awarded": float(comp.pp_awarded),
                "proof": comp.proof,
                "reviewed_by_id": comp.reviewed_by_id,
                "reviewed_at": comp.reviewed_at,
                "review_reason": comp.review_reason,
                "created_at": comp.created_at,
            })
        return results, total

    @staticmethod
    async def review_completion(
        db: AsyncSession,
        completion_id: uuid.UUID,
        approve: bool,
        admin_user_id: uuid.UUID,
        reason: str | None = None,
    ) -> QuestCompletion:
        comp = (await db.execute(
            select(QuestCompletion).where(QuestCompletion.id == completion_id).with_for_update()
        )).scalar_one_or_none()
        if not comp:
            raise ValueError("Completion not found")
        if comp.status != "pending":
            raise ValueError(f"This completion is already {comp.status}")
        if not approve and not reason:
            raise ValueError("A rejection reason is required")
        was_pending = comp.status == "pending"
        comp.status = "approved" if approve else "rejected"
        comp.reviewed_by_id = admin_user_id
        comp.reviewed_at = datetime.utcnow()
        comp.review_reason = reason
        # Award PP only on transition pending -> approved, using QUEST_REWARD type
        if approve and was_pending and comp.pp_awarded and float(comp.pp_awarded) > 0:
            await PointsService.create_transaction(
                db, comp.user_id, float(comp.pp_awarded),
                TransactionType.QUEST_REWARD, "Quest completion approved",
            )
        await db.flush()
        await db.refresh(comp)
        return comp

    # ── Clear site data ───────────────────────────────────────────────────────
    @staticmethod
    async def clear_site_data(db: AsyncSession, options: dict) -> dict:
        """Clear selected data categories. Returns counts of deleted rows.

        Wrapped in a savepoint so that if any single delete fails (e.g. a
        foreign-key constraint), every preceding delete in this call is rolled
        back and no partial data loss occurs.
        """
        cleared = {}
        async with db.begin_nested():  # SAVEPOINT — auto-rollback on exception
            if options.get("points_transactions"):
                n = (await db.execute(delete(PointsTransaction))).rowcount
                cleared["points_transactions"] = n
                # Also clear ledger entries
                n2 = (await db.execute(delete(PPLedgerEntry))).rowcount
                cleared["pp_ledger_entries"] = n2

            if options.get("quest_completions"):
                n = (await db.execute(delete(QuestCompletion))).rowcount
                cleared["quest_completions"] = n

            if options.get("submissions"):
                n1 = (await db.execute(delete(SubmissionFile))).rowcount
                n2 = (await db.execute(delete(TaskSubmission))).rowcount
                cleared["submission_files"] = n1
                cleared["submissions"] = n2

            if options.get("campaign_data"):
                n1 = (await db.execute(delete(CampaignTaskCompletion))).rowcount
                n2 = (await db.execute(delete(CampaignTask))).rowcount
                n3 = (await db.execute(delete(CampaignParticipation))).rowcount
                n4 = (await db.execute(delete(CampaignRanking))).rowcount
                cleared["campaign_task_completions"] = n1
                cleared["campaign_tasks"] = n2
                cleared["campaign_participations"] = n3
                cleared["campaign_rankings"] = n4

            if options.get("leaderboard_cache"):
                n = (await db.execute(delete(LeaderboardCache))).rowcount
                cleared["leaderboard_cache"] = n

            if options.get("announcements"):
                n = (await db.execute(delete(Announcement))).rowcount
                cleared["announcements"] = n

            if options.get("schedules"):
                n = (await db.execute(delete(Schedule))).rowcount
                cleared["schedules"] = n

            if options.get("nft_holdings"):
                n = (await db.execute(delete(NFTHolding))).rowcount
                cleared["nft_holdings"] = n

            if options.get("p2p_orders"):
                n = (await db.execute(delete(P2POrder))).rowcount
                cleared["p2p_orders"] = n

            if options.get("stakes"):
                n = (await db.execute(delete(Stake))).rowcount
                cleared["stakes"] = n

            if options.get("redemptions"):
                n = (await db.execute(delete(Redemption))).rowcount
                cleared["redemptions"] = n

            if options.get("audit_logs"):
                n = (await db.execute(delete(AuditLog))).rowcount
                cleared["audit_logs"] = n

            if options.get("idempotency_keys"):
                n = (await db.execute(delete(IdempotencyKey))).rowcount
                cleared["idempotency_keys"] = n

            if options.get("deadline_penalties"):
                n = (await db.execute(delete(DeadlinePenaltyApplied))).rowcount
                cleared["deadline_penalties"] = n

            if options.get("reset_user_points"):
                # Count affected users first, then reset all gamification fields to zero
                user_count = int((await db.execute(select(func.count()).select_from(User))).scalar() or 0)
                await db.execute(
                    update(User).values(
                        points=0.0,
                        available_points=0.0,
                        locked_points=0.0,
                        escrow_points=0.0,
                        xp=0.0,
                        level=1,
                        current_streak=0,
                    )
                )
                cleared["users_reset"] = user_count

        await db.flush()
        return cleared
