"""Meta-Jungle ecosystem service layer (Chapters 5–13)."""
import uuid
import secrets
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    User, PointsTransaction, PPLedgerEntry, TransactionType,
    Quest, QuestCompletion, NFTHolding, P2POrder, Stake,
    Partner, Course, CourseCompletion, Redemption,
)
from app.services.points_service import PointsService


# ── PP economy constants (Chapter 5.1) ──────────────────────────────────────
DAILY_CAP_NO_NFT = 500
DAILY_CAP_ONE_NFT = 750
DAILY_CAP_THREE_NFT = 1200
DAILY_CAP_HARD = 2000

# Role thresholds (Chapter 6.2): (role, activity, reputation, influence, nfts, multiplier)
ROLE_THRESHOLDS = [
    ("Alpha OG", 950, 900, 700, 3, 2.0),
    ("OG Panda", 800, 700, 400, 1, 1.5),
    ("Whitelist", 600, 500, 200, 0, 1.2),
    ("Hunter", 400, 300, 100, 0, 1.0),
    ("Tracker", 200, 100, 0, 0, 1.0),
    ("Explorer", 0, 0, 0, 0, 1.0),
]

# Staking tiers (lock_days -> multiplier)
STAKE_TIERS = {30: 1.2, 90: 1.5, 180: 2.0}

# Marketplace catalog (Chapter 12) — mirrors apps/web/src/lib/marketplace.ts
MARKET_CATALOG = [
    {"id": "air-100", "category": "airtime", "name": "Airtime ₦100", "pp": 200, "fiat": "≈ ₦100", "provider": "Africa's Talking", "regions": ["NG", "GH", "KE", "ZA"], "input": "phone"},
    {"id": "air-500", "category": "airtime", "name": "Airtime ₦500", "pp": 950, "fiat": "≈ ₦500", "provider": "Reloadly", "regions": ["NG", "GH", "KE", "ZA"], "input": "phone"},
    {"id": "air-1000", "category": "airtime", "name": "Airtime ₦1,000", "pp": 1850, "fiat": "≈ ₦1,000", "provider": "Reloadly", "regions": ["NG", "GH", "KE", "ZA"], "input": "phone"},
    {"id": "data-1", "category": "data", "name": "Data Bundle 1GB", "pp": 500, "fiat": "≈ ₦350", "provider": "Reloadly", "regions": ["NG", "GH", "ZA", "ID", "PH"], "input": "phone"},
    {"id": "data-3", "category": "data", "name": "Data Bundle 3GB", "pp": 1300, "fiat": "≈ ₦900", "provider": "Reloadly", "regions": ["NG", "GH", "ZA", "ID", "PH"], "input": "phone"},
    {"id": "data-10", "category": "data", "name": "Data Bundle 10GB", "pp": 3800, "fiat": "≈ ₦3,000", "provider": "Reloadly", "regions": ["NG", "GH", "ZA", "ID", "PH"], "input": "phone"},
    {"id": "elec-token", "category": "electricity", "name": "Electricity token ₦1,000", "pp": 1000, "fiat": "≈ ₦1,000", "provider": "Reloadly Utilities", "regions": ["NG", "GH", "KE"], "input": "meter"},
    {"id": "elec-5k", "category": "electricity", "name": "Electricity token ₦5,000", "pp": 4900, "fiat": "≈ ₦5,000", "provider": "Reloadly Utilities", "regions": ["NG", "GH", "KE"], "input": "meter"},
    {"id": "wifi", "category": "cable", "name": "WiFi voucher", "pp": 300, "fiat": "≈ $3", "provider": "Partner API", "regions": ["SG", "AE", "GB"], "input": "none"},
    {"id": "dstv", "category": "cable", "name": "Cable TV — Compact", "pp": 2400, "fiat": "≈ ₦1,900", "provider": "Reloadly", "regions": ["NG", "GH", "KE", "ZA"], "input": "smartcard"},
    {"id": "gc-amazon-10", "category": "giftcards", "name": "Amazon Gift Card $10", "pp": 1100, "fiat": "$10", "provider": "Reloadly GiftCards", "regions": ["US", "GB", "DE", "FR"], "input": "email"},
    {"id": "gc-amazon-25", "category": "giftcards", "name": "Amazon Gift Card $25", "pp": 2700, "fiat": "$25", "provider": "Reloadly GiftCards", "regions": ["US", "GB", "DE", "FR"], "input": "email"},
    {"id": "gc-jumia", "category": "giftcards", "name": "Jumia voucher", "pp": 500, "fiat": "≈ ₦5,000", "provider": "Jumia API", "regions": ["NG", "GH", "KE"], "input": "email"},
    {"id": "gc-shopee", "category": "giftcards", "name": "Shopee credits", "pp": 500, "fiat": "≈ $5", "provider": "Shopee API", "regions": ["PH", "ID", "SG", "TH"], "input": "email"},
    {"id": "gc-google", "category": "giftcards", "name": "Google Play $10", "pp": 1150, "fiat": "$10", "provider": "Reloadly GiftCards", "regions": ["US", "GB", "NG", "PH"], "input": "email"},
    {"id": "gc-steam", "category": "giftcards", "name": "Steam Wallet $20", "pp": 2200, "fiat": "$20", "provider": "Reloadly GiftCards", "regions": ["US", "GB", "DE", "TH"], "input": "email"},
]
_CATALOG_BY_ID = {p["id"]: p for p in MARKET_CATALOG}


def _clamp(v: float, lo: int = 0, hi: int = 1000) -> int:
    return int(max(lo, min(hi, v)))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MetaJungleService:
    """Business logic for the Meta-Jungle ecosystem."""

    # ── Reputation (Chapter 6) ──────────────────────────────────────────────
    @staticmethod
    async def _nft_count(db: AsyncSession, user_id: uuid.UUID) -> int:
        r = await db.execute(select(func.count()).select_from(NFTHolding).where(NFTHolding.user_id == user_id))
        return int(r.scalar() or 0)

    @staticmethod
    async def compute_reputation(db: AsyncSession, user: User) -> dict:
        """Derive the three reputation scores + role from platform activity."""
        now = _utcnow()
        since = now - timedelta(days=30)

        nft_count = await MetaJungleService._nft_count(db, user.id)

        quests_30d = int((await db.execute(
            select(func.count()).select_from(QuestCompletion).where(
                QuestCompletion.user_id == user.id,
                QuestCompletion.created_at >= since,
                QuestCompletion.status == "approved",
            )
        )).scalar() or 0)

        referrals = int((await db.execute(
            select(func.count()).select_from(User).where(User.referred_by_id == user.id)
        )).scalar() or 0)

        penalties = int((await db.execute(
            select(func.count()).select_from(PointsTransaction).where(
                PointsTransaction.user_id == user.id,
                PointsTransaction.transaction_type.in_([
                    TransactionType.DEADLINE_PENALTY, TransactionType.ADMIN_PENALTY,
                ]),
            )
        )).scalar() or 0)

        created = user.created_at
        if created and created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age_days = (now - created).days if created else 0

        activity = _clamp(
            (user.current_streak or 0) * 25
            + quests_30d * 20
            + (user.level or 1) * 30
            + float(user.points or 0) / 50
        )
        reputation = _clamp(
            age_days * 3
            + (200 if user.email_verified else 0)
            + nft_count * 150
            + 100
            - penalties * 25
        )
        influence = _clamp(referrals * 120 + quests_30d * 5 + nft_count * 40)

        role, multiplier, nxt = MetaJungleService._role_for(activity, reputation, influence, nft_count)
        return {
            "user_id": user.id,
            "activity_score": activity,
            "reputation_score": reputation,
            "influence_score": influence,
            "role": role,
            "earn_multiplier": multiplier,
            "next_role": nxt,
        }

    @staticmethod
    def _role_for(activity: int, reputation: int, influence: int, nfts: int):
        achieved_idx = len(ROLE_THRESHOLDS) - 1
        for i, (role, a, r, inf, n, mult) in enumerate(ROLE_THRESHOLDS):
            if activity >= a and reputation >= r and influence >= inf and nfts >= n:
                achieved_idx = i
                break
        role, _, _, _, _, mult = ROLE_THRESHOLDS[achieved_idx]
        nxt = ROLE_THRESHOLDS[achieved_idx - 1][0] if achieved_idx > 0 else None
        return role, mult, nxt

    # ── Daily earn cap (Chapter 5.1) ────────────────────────────────────────
    @staticmethod
    async def _earned_today(db: AsyncSession, user_id: uuid.UUID) -> float:
        start = _utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        r = await db.execute(
            select(func.coalesce(func.sum(PointsTransaction.amount), 0)).where(
                PointsTransaction.user_id == user_id,
                PointsTransaction.amount > 0,
                PointsTransaction.created_at >= start,
            )
        )
        return float(r.scalar() or 0)

    @staticmethod
    async def _daily_cap(db: AsyncSession, user_id: uuid.UUID) -> int:
        nfts = await MetaJungleService._nft_count(db, user_id)
        if nfts >= 3:
            return DAILY_CAP_THREE_NFT
        if nfts >= 1:
            return DAILY_CAP_ONE_NFT
        return DAILY_CAP_NO_NFT

    @staticmethod
    def validate_screenshot_proof(proof: Optional[dict]) -> None:
        """Validate optional screenshot evidence without trusting the browser.

        A screenshot task may be submitted with a link, an inline image, both,
        or no attachment. Inline images are deliberately bounded so proof JSON
        cannot become an unbounded database payload.
        """
        if not proof:
            return

        screenshot_url = proof.get("screenshot_url")
        if screenshot_url is not None:
            if not isinstance(screenshot_url, str) or not re.match(
                r"^https?://[^\s]+$", screenshot_url
            ):
                raise ValueError("Screenshot link must be a valid http(s) URL")

        proof_url = proof.get("proof_url")
        if proof_url is not None and (
            not isinstance(proof_url, str) or not re.match(r"^https?://[^\s]+$", proof_url)
        ):
            raise ValueError("Completion link must be a valid http(s) URL")

        screenshot_image = proof.get("screenshot_image")
        if screenshot_image is not None:
            if not isinstance(screenshot_image, str) or not re.match(
                r"^data:image/(?:png|jpeg|gif|webp);base64,[A-Za-z0-9+/=]+$",
                screenshot_image,
            ):
                raise ValueError("Screenshot image must be a valid PNG, JPG, GIF, or WebP")
            if len(screenshot_image) > 7_000_000:
                raise ValueError("Screenshot image must be 5 MB or smaller")

    # ── Quests (Chapter 5.2) ────────────────────────────────────────────────
    @staticmethod
    async def list_quests(db: AsyncSession, page: int = 1, page_size: int = 20) -> tuple[list[Quest], int]:
        """List active, non-deleted, non-expired quests with pagination."""
        now = _utcnow()
        base = (
            Quest.is_active.is_(True),
            Quest.deleted_at.is_(None),
            (Quest.starts_at.is_(None)) | (Quest.starts_at <= now),
            (Quest.ends_at.is_(None)) | (Quest.ends_at > now),
        )
        count_q = select(func.count()).select_from(Quest).where(*base)
        total = int((await db.execute(count_q)).scalar() or 0)

        offset = (page - 1) * page_size
        q = (
            select(Quest)
            .where(*base)
            .order_by(Quest.pp_reward.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows = list((await db.execute(q)).scalars().all())
        return rows, total

    @staticmethod
    async def _role_index(role_name: str) -> int:
        """Return the index of a role in ROLE_THRESHOLDS (0 = highest)."""
        for i, (r, *_rest) in enumerate(ROLE_THRESHOLDS):
            if r == role_name:
                return i
        # Default to lowest role if unknown
        return len(ROLE_THRESHOLDS) - 1

    @staticmethod
    async def complete_quest(
        db: AsyncSession, user: User, quest_id: uuid.UUID, proof: Optional[dict],
    ) -> QuestCompletion:
        # Serialize attempts per user so daily limits cannot be bypassed by
        # concurrent submissions.
        user = (await db.execute(
            select(User).where(User.id == user.id).with_for_update()
        )).scalar_one()
        quest = (await db.execute(select(Quest).where(Quest.id == quest_id))).scalar_one_or_none()
        if not quest or not quest.is_active:
            raise ValueError("Quest not found or inactive")

        # Check quest not soft-deleted
        if quest.deleted_at is not None:
            raise ValueError("Quest not found or inactive")

        # Check quest not expired
        now = _utcnow()
        if quest.ends_at is not None:
            ends = quest.ends_at
            if ends.tzinfo is None:
                ends = ends.replace(tzinfo=timezone.utc)
            if ends <= now:
                raise ValueError("This quest has expired")

        # Check quest has started
        if quest.starts_at is not None:
            starts = quest.starts_at
            if starts.tzinfo is None:
                starts = starts.replace(tzinfo=timezone.utc)
            if starts > now:
                raise ValueError("This quest has not started yet")

        # Enforce min_role
        rep = await MetaJungleService.compute_reputation(db, user)
        user_role_idx = await MetaJungleService._role_index(rep["role"])
        quest_role_idx = await MetaJungleService._role_index(quest.min_role)
        # Lower index = higher role (0 = Alpha OG)
        if user_role_idx > quest_role_idx:
            raise ValueError(
                f"Your reputation role ({rep['role']}) does not meet the minimum "
                f"requirement ({quest.min_role}) for this quest"
            )

        # Membership-tier global daily quest limit
        from app.services.premium_service import PremiumService
        can_quest, quest_limit_reason = await PremiumService.can_join_quest(db, user.id)
        if not can_quest:
            raise ValueError(quest_limit_reason)

        # Per-quest daily limit (rejected completions don't count — user can retry)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        done_today = int((await db.execute(
            select(func.count()).select_from(QuestCompletion).where(
                QuestCompletion.user_id == user.id,
                QuestCompletion.quest_id == quest_id,
                QuestCompletion.created_at >= start,
                QuestCompletion.status != "rejected",
            )
        )).scalar() or 0)
        if done_today >= quest.daily_limit:
            raise ValueError("Daily limit reached for this quest")

        # Validate steps if quest has them
        if quest.steps and len(quest.steps) > 0:
            if not proof or "steps_completed" not in proof:
                raise ValueError(
                    "This quest requires step-by-step completion. "
                    "Please provide 'steps_completed' in your proof."
                )
            steps_completed = proof.get("steps_completed")
            if (
                not isinstance(steps_completed, list)
                or len(steps_completed) != len(quest.steps)
                or not all(isinstance(step, bool) and step for step in steps_completed)
            ):
                raise ValueError(
                    f"'steps_completed' must contain {len(quest.steps)} completed boolean steps"
                )

        # Validate proof based on verification_type.
        #
        # The client is never trusted to assert that an action happened.
        # oauth/webhook quests used to auto-approve on a browser-supplied
        # {"verified": true}, which let anyone mint PP by posting that flag.
        # Server-side provider verification does not exist yet, so those
        # types are review-gated like the rest until it does.
        vtype = quest.verification_type

        proof = proof or {}
        proof_url = proof.get("proof_url") or proof.get("screenshot_url")
        if proof_url is not None and (
            not isinstance(proof_url, str) or not re.match(r"^https?://[^\s]+$", proof_url)
        ):
            raise ValueError("Completion link must be a valid http(s) URL")
        if quest.link_required and not proof_url:
            raise ValueError("This quest requires a link showing the completed action")
        if quest.screenshot_required:
            screenshot = proof.get("screenshot_image")
            if not isinstance(screenshot, str) or not screenshot.startswith("data:image/"):
                raise ValueError("This quest requires an uploaded screenshot")
        if proof.get("screenshot_image") or proof.get("screenshot_url") or proof.get("proof_url"):
            MetaJungleService.validate_screenshot_proof(proof)

        if vtype == "on_chain":
            # Require tx_hash in proof
            tx_hash = proof.get("tx_hash")
            if not isinstance(tx_hash, str) or not re.match(r"^0x[a-fA-F0-9]{64}$", tx_hash):
                raise ValueError(
                    "On-chain quests require a valid 0x transaction hash"
                )
        elif vtype == "screenshot":
            if not (proof.get("screenshot_image") or proof.get("screenshot_url") or proof.get("proof_url")):
                raise ValueError("Screenshot quests require a screenshot or completion link")
            MetaJungleService.validate_screenshot_proof(proof)

        # Daily earn cap with role multiplier
        award = int(round(quest.pp_reward * rep["earn_multiplier"]))
        earned = await MetaJungleService._earned_today(db, user.id)
        cap = await MetaJungleService._daily_cap(db, user.id)
        remaining = min(cap, DAILY_CAP_HARD) - earned
        if remaining <= 0:
            raise ValueError("Daily earn cap reached")
        award = int(min(award, remaining))
        if award <= 0:
            raise ValueError("No reward remains within the daily earn cap")

        # No verification type self-approves. PP is awarded by
        # AdminService.review_completion on the pending -> approved
        # transition, so a completion never pays out from client input.
        status = "pending"

        completion = QuestCompletion(
            user_id=user.id,
            quest_id=quest_id,
            status=status,
            pp_awarded=award,
            proof=proof or {},
        )
        db.add(completion)
        await db.flush()

        await db.refresh(completion)
        return completion

    @staticmethod
    async def get_user_completions_today(db: AsyncSession, user_id: uuid.UUID) -> dict[str, str]:
        """Return the latest status for each quest attempted by the user today."""
        now = _utcnow()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        rows = (await db.execute(
            select(QuestCompletion.quest_id, QuestCompletion.status).where(
                QuestCompletion.user_id == user_id,
                QuestCompletion.created_at >= start,
                QuestCompletion.status.in_(["approved", "pending", "rejected"]),
            )
        )).all()
        return {str(qid): status for qid, status in rows}

    # ── NFT Vault ───────────────────────────────────────────────────────────
    @staticmethod
    async def list_nfts(db: AsyncSession, user_id: uuid.UUID) -> tuple[list[NFTHolding], int]:
        r = await db.execute(select(NFTHolding).where(NFTHolding.user_id == user_id))
        nfts = list(r.scalars().all())
        return nfts, sum(n.daily_pp_rate for n in nfts)

    # ── P2P ─────────────────────────────────────────────────────────────────
    @staticmethod
    async def list_orders(db: AsyncSession, side: Optional[str] = None) -> list[P2POrder]:
        q = select(P2POrder).where(P2POrder.status == "open")
        if side in ("buy", "sell"):
            q = q.where(P2POrder.side == side)
        q = q.order_by(P2POrder.created_at.desc())
        return list((await db.execute(q)).scalars().all())

    @staticmethod
    async def create_order(db: AsyncSession, user: User, data) -> P2POrder:
        raise ValueError("P2P escrow trading is not enabled yet")

    # ── Staking (Chapter 7) ─────────────────────────────────────────────────
    @staticmethod
    async def list_stakes(db: AsyncSession, user_id: uuid.UUID) -> tuple[list[Stake], int, float]:
        r = await db.execute(select(Stake).where(Stake.user_id == user_id, Stake.status == "active"))
        stakes = list(r.scalars().all())
        return stakes, sum(s.pp_amount for s in stakes), float(sum(s.accrued for s in stakes))

    @staticmethod
    async def create_stake(db: AsyncSession, user: User, pp_amount: int, lock_days: int) -> Stake:
        if lock_days not in STAKE_TIERS:
            raise ValueError("Lock duration must be 30, 90 or 180 days")
        if float(user.available_points if user.available_points is not None else user.points or 0) < pp_amount:
            raise ValueError("Insufficient PP to stake")
        await PointsService.create_transaction(
            db=db, user_id=user.id, amount=-float(pp_amount),
            transaction_type=TransactionType.ADMIN_PENALTY,
            reason=f"Stake locked ({lock_days}d)",
        )
        user.locked_points = (user.locked_points or 0) + pp_amount
        db.add(PPLedgerEntry(
            user_id=user.id,
            amount=pp_amount,
            bucket="locked",
            transaction_type="STAKE_LOCK",
            source_type="stake",
            entry_metadata={"lock_days": lock_days},
        ))
        stake = Stake(
            user_id=user.id, asset=f"{pp_amount} PP", pp_amount=pp_amount,
            multiplier=STAKE_TIERS[lock_days], lock_days=lock_days, status="active",
        )
        db.add(stake)
        await db.flush()
        await db.refresh(stake)
        return stake

    @staticmethod
    async def claim_stake(db: AsyncSession, user: User, stake_id: uuid.UUID) -> Stake:
        stake = (await db.execute(
            select(Stake).where(Stake.id == stake_id, Stake.user_id == user.id)
        )).scalar_one_or_none()
        if not stake or stake.status != "active":
            raise ValueError("Stake not found")
        now = _utcnow()
        started = stake.started_at.replace(tzinfo=timezone.utc) if stake.started_at.tzinfo is None else stake.started_at
        maturity = started + timedelta(days=stake.lock_days)
        if now < maturity:
            raise ValueError("Stake has not reached maturity")

        reward = float(stake.pp_amount) * (float(stake.multiplier) - 1.0)
        total = float(stake.pp_amount) + reward
        await PointsService.create_transaction(
            db=db, user_id=user.id, amount=total,
            transaction_type=TransactionType.ADMIN_BONUS,
            reason="Stake principal and reward released",
        )
        user.locked_points = max(0, float(user.locked_points or 0) - stake.pp_amount)
        db.add(PPLedgerEntry(
            user_id=user.id,
            amount=-stake.pp_amount,
            bucket="locked",
            transaction_type="STAKE_UNLOCK",
            source_type="stake",
            source_id=str(stake.id),
        ))
        db.add(PPLedgerEntry(
            user_id=user.id,
            amount=reward,
            bucket="available",
            transaction_type="STAKE_REWARD",
            source_type="stake",
            source_id=str(stake.id),
        ))
        stake.accrued = 0
        stake.status = "completed"
        stake.unlocked_at = now
        await db.flush()
        await db.refresh(stake)
        return stake

    @staticmethod
    async def unstake(db: AsyncSession, user: User, stake_id: uuid.UUID) -> Stake:
        """Return principal early without rewards, preserving the lock invariant."""
        stake = (await db.execute(
            select(Stake).where(Stake.id == stake_id, Stake.user_id == user.id).with_for_update()
        )).scalar_one_or_none()
        if not stake or stake.status != "active":
            raise ValueError("Stake not found")
        await PointsService.create_transaction(
            db=db, user_id=user.id, amount=float(stake.pp_amount),
            transaction_type=TransactionType.ADMIN_BONUS,
            reason="Stake principal returned after early exit",
        )
        user.locked_points = max(0, float(user.locked_points or 0) - stake.pp_amount)
        db.add(PPLedgerEntry(
            user_id=user.id,
            amount=-stake.pp_amount,
            bucket="locked",
            transaction_type="STAKE_UNLOCK",
            source_type="stake",
            source_id=str(stake.id),
            entry_metadata={"early_exit": True},
        ))
        stake.status = "cancelled"
        stake.unlocked_at = _utcnow()
        await db.flush()
        await db.refresh(stake)
        return stake

    # ── Campaigns ───────────────────────────────────────────────────────────
    # Moved to app/services/campaign_service.py — see docs/ARCHITECTURE.md for
    # the campaign-service boundary.

    # ── Learn (Chapter 13) ──────────────────────────────────────────────────
    @staticmethod
    async def list_courses(db: AsyncSession) -> list[Course]:
        r = await db.execute(select(Course).where(Course.is_active.is_(True)).order_by(Course.created_at))
        return list(r.scalars().all())

    @staticmethod
    async def submit_quiz(db: AsyncSession, user: User, course_id: uuid.UUID, answers: list[int]) -> dict:
        course = (await db.execute(select(Course).where(Course.id == course_id))).scalar_one_or_none()
        if not course or not course.quiz:
            raise ValueError("Course or quiz not found")
        questions = course.quiz.get("questions", [])
        if not questions:
            raise ValueError("Quiz has no questions")
        correct = sum(
            1 for i, q in enumerate(questions)
            if i < len(answers) and answers[i] == q.get("answer")
        )
        score = int(round(correct / len(questions) * 100))
        passed = score >= 80

        already = (await db.execute(
            select(CourseCompletion).where(
                CourseCompletion.user_id == user.id,
                CourseCompletion.course_id == course_id,
                CourseCompletion.passed.is_(True),
            )
        )).scalar_one_or_none()

        awarded = 0.0
        if passed and not already:
            awarded = float(course.pp_reward)
            await PointsService.create_transaction(
                db=db, user_id=user.id, amount=awarded,
                transaction_type=TransactionType.ADMIN_BONUS,
                reason=f"Course completed: {course.title}",
            )
        db.add(CourseCompletion(
            user_id=user.id, course_id=course_id, passed=passed, pp_awarded=awarded,
        ))
        await db.flush()
        return {"passed": passed, "score": score, "pp_awarded": awarded}

    # ── Marketplace (Chapter 12) ────────────────────────────────────────────
    @staticmethod
    async def redeem(db: AsyncSession, user: User, product_id: str, destination: Optional[str]) -> Redemption:
        raise ValueError("Marketplace fulfilment is not available yet")
