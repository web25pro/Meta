"""Admin panel service layer (Overall_Admin only)."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    User, UserRole, PointsTransaction, TransactionType,
    Quest, QuestCompletion, NFTHolding, Partner, Campaign, Redemption, Course,
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

    # ── Partners & campaigns ─────────────────────────────────────────────────
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

    @staticmethod
    async def list_campaigns(db: AsyncSession):
        rows = (await db.execute(
            select(Campaign, Partner.name).join(Partner, Partner.id == Campaign.partner_id).order_by(desc(Campaign.created_at))
        )).all()
        out = []
        for c, brand in rows:
            c.brand = brand
            out.append(c)
        return out

    @staticmethod
    async def create_campaign(db: AsyncSession, data) -> Campaign:
        partner = (await db.execute(select(Partner).where(Partner.id == data.partner_id))).scalar_one_or_none()
        if not partner:
            raise ValueError("Partner not found")
        now = datetime.now(timezone.utc)
        campaign = Campaign(
            partner_id=data.partner_id, title=data.title, blurb=data.blurb,
            pp_budget=data.pp_budget, pp_per_task=data.pp_per_task, featured=data.featured,
            status="active", starts_at=now, ends_at=now + timedelta(days=data.days),
        )
        db.add(campaign)
        await db.flush()
        await db.refresh(campaign)
        campaign.brand = partner.name
        return campaign

    @staticmethod
    async def set_campaign_status(db: AsyncSession, campaign_id: uuid.UUID, status: str) -> Campaign:
        campaign = (await db.execute(select(Campaign).where(Campaign.id == campaign_id))).scalar_one_or_none()
        if not campaign:
            raise ValueError("Campaign not found")
        campaign.status = status
        await db.flush()
        await db.refresh(campaign)
        return campaign

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
                "created_at": comp.created_at,
            })
        return results, total

    @staticmethod
    async def review_completion(db: AsyncSession, completion_id: uuid.UUID, approve: bool) -> QuestCompletion:
        comp = (await db.execute(select(QuestCompletion).where(QuestCompletion.id == completion_id))).scalar_one_or_none()
        if not comp:
            raise ValueError("Completion not found")
        was_pending = comp.status == "pending"
        comp.status = "approved" if approve else "rejected"
        # Award PP only on transition pending -> approved, using QUEST_REWARD type
        if approve and was_pending and comp.pp_awarded and float(comp.pp_awarded) > 0:
            await PointsService.create_transaction(
                db, comp.user_id, float(comp.pp_awarded),
                TransactionType.QUEST_REWARD, "Quest completion approved",
            )
        await db.flush()
        await db.refresh(comp)
        return comp
