"""Campaign domain service — partner campaigns, targeting and billing.

Self-contained on purpose: this module owns every campaign read and write so the
Chapter-8 ``campaign-service`` extraction (see ``docs/ARCHITECTURE.md``) is a
directory move rather than a rewrite. It depends on the shared PP economy only
through ``MetaJungleService`` (reputation, daily cap) and ``PointsService`` (the
ledger) — the two seams that would become RPC calls after a split.

Budget accounting is reserve → claim → settle:

* auto-verified completions credit the ledger and add to ``pp_claimed``
* review-gated completions add to ``pp_reserved``; admin approval moves the PP
  to ``pp_claimed``, rejection releases it

A campaign therefore never commits more than ``pp_budget`` in total.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    User, TransactionType,
    Partner, Campaign, CampaignParticipation, CampaignTask, CampaignTaskCompletion,
    CAMPAIGN_STATUSES,
)
from app.services.points_service import PointsService
from app.services.metajungle_service import MetaJungleService, DAILY_CAP_HARD

#: Verification types that need no human review, matching quest semantics.
AUTO_APPROVE_TYPES = {"oauth", "webhook"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    """Treat naive DB timestamps as UTC, as ``complete_quest`` does."""
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class CampaignService:
    """Business logic for partner campaigns."""

    # ── Lifecycle ───────────────────────────────────────────────────────────
    @staticmethod
    def _assert_live(campaign: Campaign) -> None:
        """Raise unless the campaign is active and inside its date window."""
        if campaign.status != "active":
            raise ValueError(f"This campaign is {campaign.status}, not active")

        now = _utcnow()
        starts_at = _aware(campaign.starts_at)
        ends_at = _aware(campaign.ends_at)
        if starts_at is not None and starts_at > now:
            raise ValueError("This campaign has not started yet")
        if ends_at is not None and ends_at <= now:
            raise ValueError("This campaign has ended")

    # ── Targeting ───────────────────────────────────────────────────────────
    @staticmethod
    async def check_eligibility(db: AsyncSession, user: User, campaign: Campaign) -> dict:
        """Evaluate targeting for one user/campaign pair.

        Returns ``{"eligible", "reason", "role", "earn_multiplier"}``. An empty
        ``target_regions``/``target_roles`` means no restriction on that axis; a
        populated ``target_regions`` excludes users with no region set, so
        partner budget is never spent on an unverifiable audience.
        """
        rep = await MetaJungleService.compute_reputation(db, user)
        role = rep["role"]

        def result(reason: Optional[str]) -> dict:
            return {
                "eligible": reason is None,
                "reason": reason,
                "role": role,
                "earn_multiplier": rep["earn_multiplier"],
            }

        regions = campaign.target_regions or []
        if regions:
            if not user.region:
                return result(
                    "This campaign is region-targeted and your account has no region set"
                )
            if user.region.upper() not in {r.upper() for r in regions}:
                return result(f"This campaign is not available in your region ({user.region})")

        roles = campaign.target_roles or []
        if roles and role not in roles:
            return result(f"This campaign targets {', '.join(roles)} — your role is {role}")

        # min_role uses the same index comparison as quests: lower index = higher role.
        user_idx = await MetaJungleService._role_index(role)
        min_idx = await MetaJungleService._role_index(campaign.min_role)
        if user_idx > min_idx:
            return result(f"Requires at least {campaign.min_role} — your role is {role}")

        return result(None)

    # ── Reads ───────────────────────────────────────────────────────────────
    @staticmethod
    async def list_campaigns(db: AsyncSession, user: Optional[User] = None) -> list[Campaign]:
        """Active campaigns inside their date window, newest/featured first."""
        now = _utcnow()
        rows = (await db.execute(
            select(Campaign, Partner.name)
            .join(Partner, Partner.id == Campaign.partner_id)
            .where(
                Campaign.status == "active",
                Campaign.deleted_at.is_(None),
                (Campaign.starts_at.is_(None)) | (Campaign.starts_at <= now),
                (Campaign.ends_at.is_(None)) | (Campaign.ends_at > now),
            )
            .order_by(Campaign.featured.desc(), Campaign.created_at.desc())
        )).all()

        joined: set[uuid.UUID] = set()
        if user is not None and rows:
            joined = {
                cid for (cid,) in (await db.execute(
                    select(CampaignParticipation.campaign_id).where(
                        CampaignParticipation.user_id == user.id,
                        CampaignParticipation.campaign_id.in_([c.id for c, _ in rows]),
                    )
                )).all()
            }

        campaigns = []
        for campaign, brand in rows:
            # Transient attrs consumed by CampaignResponse.
            campaign.brand = brand
            campaign.joined = campaign.id in joined
            campaign.pp_available = max(
                0, campaign.pp_budget - campaign.pp_claimed - campaign.pp_reserved
            )
            campaigns.append(campaign)
        return campaigns

    @staticmethod
    async def get_campaign(
        db: AsyncSession, campaign_id: uuid.UUID, include_deleted: bool = False
    ) -> Campaign:
        campaign = (await db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )).scalar_one_or_none()
        if not campaign:
            raise ValueError("Campaign not found")
        if campaign.deleted_at is not None and not include_deleted:
            raise ValueError("Campaign not found")
        return campaign

    @staticmethod
    async def list_tasks(
        db: AsyncSession, campaign_id: uuid.UUID, user: Optional[User] = None
    ) -> list[CampaignTask]:
        """Tasks for a campaign, annotated with the caller's progress today.

        Admin callers pass no ``user`` and get every task, active or not.
        """
        await CampaignService.get_campaign(db, campaign_id)
        query = select(CampaignTask).where(CampaignTask.campaign_id == campaign_id)
        if user is not None:
            query = query.where(CampaignTask.is_active.is_(True))
        tasks = list((await db.execute(
            query.order_by(CampaignTask.order_index, CampaignTask.created_at)
        )).scalars().all())
        if not tasks or user is None:
            for task in tasks:
                task.completed_today = 0
                task.can_complete = False
            return tasks

        start = _utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        counts = dict((tid, n) for tid, n in (await db.execute(
            select(CampaignTaskCompletion.task_id, func.count())
            .where(
                CampaignTaskCompletion.user_id == user.id,
                CampaignTaskCompletion.campaign_id == campaign_id,
                CampaignTaskCompletion.created_at >= start,
                CampaignTaskCompletion.status != "rejected",
            )
            .group_by(CampaignTaskCompletion.task_id)
        )).all())

        for task in tasks:
            task.completed_today = int(counts.get(task.id, 0))
            task.can_complete = task.completed_today < task.daily_limit
        return tasks

    # ── Join ────────────────────────────────────────────────────────────────
    @staticmethod
    async def join_campaign(
        db: AsyncSession, user: User, campaign_id: uuid.UUID
    ) -> CampaignParticipation:
        campaign = await CampaignService.get_campaign(db, campaign_id)
        CampaignService._assert_live(campaign)

        eligibility = await CampaignService.check_eligibility(db, user, campaign)
        if not eligibility["eligible"]:
            raise ValueError(eligibility["reason"])

        existing = (await db.execute(
            select(CampaignParticipation).where(
                CampaignParticipation.campaign_id == campaign_id,
                CampaignParticipation.user_id == user.id,
            )
        )).scalar_one_or_none()
        if existing:
            raise ValueError("Already joined this campaign")

        if campaign.max_participants is not None and campaign.total_participants >= campaign.max_participants:
            raise ValueError("This campaign is full")

        part = CampaignParticipation(campaign_id=campaign_id, user_id=user.id)
        db.add(part)
        campaign.total_participants += 1
        await db.flush()
        await db.refresh(part)
        return part

    # ── Earn loop ───────────────────────────────────────────────────────────
    @staticmethod
    def _validate_proof(task: CampaignTask, proof: Optional[dict]) -> None:
        """Same proof rules as ``MetaJungleService.complete_quest``."""
        vtype = task.verification_type
        if vtype in AUTO_APPROVE_TYPES:
            if not proof or proof.get("verified") is not True:
                raise ValueError(f'This {vtype} task requires proof with {{"verified": true}}')
        elif vtype == "on_chain":
            if not proof or not proof.get("tx_hash"):
                raise ValueError("On-chain tasks require a 'tx_hash' in your proof")
        elif vtype == "screenshot":
            if not proof or not proof.get("screenshot_url"):
                raise ValueError("Screenshot tasks require a 'screenshot_url' in your proof")

    @staticmethod
    async def complete_task(
        db: AsyncSession,
        user: User,
        campaign_id: uuid.UUID,
        task_id: uuid.UUID,
        proof: Optional[dict],
    ) -> CampaignTaskCompletion:
        """Complete a campaign task, awarding or reserving PP.

        Enforces, in order: campaign lifecycle, targeting, participation, the
        per-task daily limit, proof validity, the campaign budget, and finally
        the platform daily earn cap with the caller's role multiplier.
        """
        campaign = await CampaignService.get_campaign(db, campaign_id)
        CampaignService._assert_live(campaign)

        task = (await db.execute(
            select(CampaignTask).where(
                CampaignTask.id == task_id,
                CampaignTask.campaign_id == campaign_id,
            )
        )).scalar_one_or_none()
        if not task or not task.is_active:
            raise ValueError("Campaign task not found or inactive")

        eligibility = await CampaignService.check_eligibility(db, user, campaign)
        if not eligibility["eligible"]:
            raise ValueError(eligibility["reason"])

        joined = (await db.execute(
            select(CampaignParticipation.id).where(
                CampaignParticipation.campaign_id == campaign_id,
                CampaignParticipation.user_id == user.id,
            )
        )).scalar_one_or_none()
        if not joined:
            raise ValueError("Join this campaign before completing its tasks")

        # Per-task daily limit. Rejected attempts don't count, so a user can retry.
        start = _utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        done_today = int((await db.execute(
            select(func.count()).select_from(CampaignTaskCompletion).where(
                CampaignTaskCompletion.user_id == user.id,
                CampaignTaskCompletion.task_id == task_id,
                CampaignTaskCompletion.created_at >= start,
                CampaignTaskCompletion.status != "rejected",
            )
        )).scalar() or 0)
        if done_today >= task.daily_limit:
            raise ValueError("Daily limit reached for this task")

        CampaignService._validate_proof(task, proof)

        # Role multiplier, then the campaign budget, then the platform cap.
        base = task.pp_reward or campaign.pp_per_task
        award = int(round(base * eligibility["earn_multiplier"]))

        budget_left = campaign.pp_budget - campaign.pp_claimed - campaign.pp_reserved
        if budget_left <= 0:
            raise ValueError("This campaign's PP budget is exhausted")
        award = min(award, budget_left)

        earned = await MetaJungleService._earned_today(db, user.id)
        cap = await MetaJungleService._daily_cap(db, user.id)
        remaining = min(cap, DAILY_CAP_HARD) - earned
        if remaining <= 0:
            raise ValueError("Daily earn cap reached")
        award = int(min(award, remaining))

        auto = task.verification_type in AUTO_APPROVE_TYPES
        completion = CampaignTaskCompletion(
            campaign_id=campaign_id,
            task_id=task_id,
            user_id=user.id,
            status="approved" if auto else "pending",
            pp_awarded=award,
            proof=proof or {},
        )
        db.add(completion)
        await db.flush()

        if auto:
            if award > 0:
                await PointsService.create_transaction(
                    db=db, user_id=user.id, amount=float(award),
                    transaction_type=TransactionType.CAMPAIGN_REWARD,
                    reason=f"Campaign reward: {campaign.title} — {task.title}",
                )
            campaign.pp_claimed += award
        else:
            # Escrow against the budget until an admin settles it.
            campaign.pp_reserved += award

        await db.flush()
        await db.refresh(completion)
        return completion

    # ── Review (settles reserved budget) ────────────────────────────────────
    @staticmethod
    async def review_completion(
        db: AsyncSession,
        admin: User,
        completion_id: uuid.UUID,
        approve: bool,
    ) -> CampaignTaskCompletion:
        """Approve or reject a pending completion, settling its reserved PP."""
        completion = (await db.execute(
            select(CampaignTaskCompletion).where(CampaignTaskCompletion.id == completion_id)
        )).scalar_one_or_none()
        if not completion:
            raise ValueError("Completion not found")
        if completion.status != "pending":
            raise ValueError(f"This completion is already {completion.status}")

        campaign = await CampaignService.get_campaign(db, completion.campaign_id)
        award = int(completion.pp_awarded or 0)

        # Release the reservation either way.
        campaign.pp_reserved = max(0, campaign.pp_reserved - award)

        if approve:
            if award > 0:
                await PointsService.create_transaction(
                    db=db, user_id=completion.user_id, amount=float(award),
                    transaction_type=TransactionType.CAMPAIGN_REWARD,
                    reason=f"Campaign reward: {campaign.title}",
                )
            campaign.pp_claimed += award
            completion.status = "approved"
        else:
            completion.status = "rejected"
            completion.pp_awarded = 0

        completion.reviewed_by_id = admin.id
        completion.reviewed_at = _utcnow()
        await db.flush()
        await db.refresh(completion)
        return completion

    # ── Admin CRUD ──────────────────────────────────────────────────────────
    @staticmethod
    def _slugify(title: str, campaign_id: uuid.UUID) -> str:
        base = "".join(ch if ch.isalnum() else "-" for ch in title.lower())
        base = "-".join(part for part in base.split("-") if part)
        return f"{base}-{campaign_id.hex[:8]}"[:64]

    @staticmethod
    async def admin_list_campaigns(db: AsyncSession) -> list[Campaign]:
        """Every campaign regardless of status, newest first. Excludes deleted."""
        rows = (await db.execute(
            select(Campaign, Partner.name)
            .join(Partner, Partner.id == Campaign.partner_id)
            .where(Campaign.deleted_at.is_(None))
            .order_by(Campaign.created_at.desc())
        )).all()
        out = []
        for campaign, brand in rows:
            campaign.brand = brand
            campaign.pp_available = max(
                0, campaign.pp_budget - campaign.pp_claimed - campaign.pp_reserved
            )
            out.append(campaign)
        return out

    @staticmethod
    async def create_campaign(db: AsyncSession, data) -> Campaign:
        partner = (await db.execute(
            select(Partner).where(Partner.id == data.partner_id)
        )).scalar_one_or_none()
        if not partner:
            raise ValueError("Partner not found")

        now = _utcnow()
        campaign_id = uuid.uuid4()
        campaign = Campaign(
            id=campaign_id,
            partner_id=data.partner_id,
            slug=CampaignService._slugify(data.title, campaign_id),
            title=data.title,
            blurb=data.blurb,
            pp_budget=data.pp_budget,
            pp_per_task=data.pp_per_task,
            featured=data.featured,
            status=getattr(data, "status", None) or "draft",
            target_regions=getattr(data, "target_regions", None) or [],
            target_roles=getattr(data, "target_roles", None) or [],
            min_role=getattr(data, "min_role", None) or "Explorer",
            max_participants=getattr(data, "max_participants", None),
            starts_at=now,
            ends_at=now + timedelta(days=data.days),
        )
        db.add(campaign)
        await db.flush()
        await db.refresh(campaign)
        campaign.brand = partner.name
        return campaign

    @staticmethod
    async def set_campaign_status(db: AsyncSession, campaign_id: uuid.UUID, status: str) -> Campaign:
        if status not in CAMPAIGN_STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(CAMPAIGN_STATUSES)}")
        campaign = await CampaignService.get_campaign(db, campaign_id)
        campaign.status = status
        await db.flush()
        await db.refresh(campaign)
        return campaign

    @staticmethod
    async def create_task(db: AsyncSession, campaign_id: uuid.UUID, data) -> CampaignTask:
        await CampaignService.get_campaign(db, campaign_id)
        task = CampaignTask(
            campaign_id=campaign_id,
            title=data.title,
            description=data.description,
            pp_reward=data.pp_reward,
            verification_type=data.verification_type,
            daily_limit=data.daily_limit,
            action_url=data.action_url,
            order_index=data.order_index,
        )
        db.add(task)
        await db.flush()
        await db.refresh(task)
        return task

    @staticmethod
    async def set_task_active(
        db: AsyncSession, campaign_id: uuid.UUID, task_id: uuid.UUID, is_active: bool
    ) -> CampaignTask:
        task = (await db.execute(
            select(CampaignTask).where(
                CampaignTask.id == task_id,
                CampaignTask.campaign_id == campaign_id,
            )
        )).scalar_one_or_none()
        if not task:
            raise ValueError("Campaign task not found")
        task.is_active = is_active
        await db.flush()
        await db.refresh(task)
        return task

    @staticmethod
    async def delete_campaign(db: AsyncSession, admin: User, campaign_id: uuid.UUID) -> dict:
        """Soft delete a campaign, releasing any budget it still holds.

        Soft rather than hard because approved completions have already credited
        PP through the immutable ledger; cascading them away would orphan the
        audit trail. Any still-pending completions are rejected first so their
        reserved PP is released and they leave the review queue — otherwise they
        would sit there forever against a campaign nobody can see.
        """
        campaign = await CampaignService.get_campaign(db, campaign_id)

        pending = list((await db.execute(
            select(CampaignTaskCompletion).where(
                CampaignTaskCompletion.campaign_id == campaign_id,
                CampaignTaskCompletion.status == "pending",
            )
        )).scalars().all())

        now = _utcnow()
        for completion in pending:
            completion.status = "rejected"
            completion.pp_awarded = 0
            completion.reviewed_by_id = admin.id
            completion.reviewed_at = now

        campaign.pp_reserved = 0
        campaign.status = "ended"
        campaign.deleted_at = now
        await db.flush()
        return {"rejected_pending": len(pending)}

    @staticmethod
    async def list_pending_completions(db: AsyncSession) -> list[CampaignTaskCompletion]:
        """Pending completions across all campaigns, oldest first, for admin review."""
        rows = (await db.execute(
            select(CampaignTaskCompletion, Campaign.title, CampaignTask.title, User.username)
            .join(Campaign, Campaign.id == CampaignTaskCompletion.campaign_id)
            .join(CampaignTask, CampaignTask.id == CampaignTaskCompletion.task_id)
            .join(User, User.id == CampaignTaskCompletion.user_id)
            .where(
                CampaignTaskCompletion.status == "pending",
                Campaign.deleted_at.is_(None),
            )
            .order_by(CampaignTaskCompletion.created_at)
        )).all()
        out = []
        for completion, campaign_title, task_title, username in rows:
            completion.campaign_title = campaign_title
            completion.task_title = task_title
            completion.username = username
            out.append(completion)
        return out
