"""Meta-Jungle ecosystem service layer (Chapters 5–13)."""
import uuid
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    User, PointsTransaction, TransactionType,
    Quest, QuestCompletion, NFTHolding, P2POrder, Stake,
    Partner, Campaign, CampaignParticipation, Course, CourseCompletion, Redemption,
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

    # ── Quests (Chapter 5.2) ────────────────────────────────────────────────
    @staticmethod
    async def list_quests(db: AsyncSession, page: int = 1, page_size: int = 20) -> tuple[list[Quest], int]:
        """List active, non-deleted, non-expired quests with pagination."""
        now = _utcnow()
        base = (
            Quest.is_active.is_(True),
            Quest.deleted_at.is_(None),
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

        # Per-quest daily limit
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        done_today = int((await db.execute(
            select(func.count()).select_from(QuestCompletion).where(
                QuestCompletion.user_id == user.id,
                QuestCompletion.quest_id == quest_id,
                QuestCompletion.created_at >= start,
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
            if not isinstance(steps_completed, list) or len(steps_completed) != len(quest.steps):
                raise ValueError(
                    f"'steps_completed' must be a list of {len(quest.steps)} boolean values"
                )

        # Validate proof based on verification_type
        vtype = quest.verification_type
        auto_approve_types = {"oauth", "webhook"}

        if vtype in auto_approve_types:
            # Require proof with verified flag
            if not proof or proof.get("verified") is not True:
                raise ValueError(
                    f"This {vtype} quest requires proof with {{\"verified\": true}}"
                )
        elif vtype == "on_chain":
            # Require tx_hash in proof
            if not proof or not proof.get("tx_hash"):
                raise ValueError(
                    "On-chain quests require a 'tx_hash' in your proof"
                )

        # Daily earn cap with role multiplier
        award = int(round(quest.pp_reward * rep["earn_multiplier"]))
        earned = await MetaJungleService._earned_today(db, user.id)
        cap = await MetaJungleService._daily_cap(db, user.id)
        remaining = min(cap, DAILY_CAP_HARD) - earned
        if remaining <= 0:
            raise ValueError("Daily earn cap reached")
        award = int(min(award, remaining))

        # Determine completion status based on verification type
        if vtype in auto_approve_types:
            status = "approved"
        else:
            # manual, screenshot, on_chain → pending admin review
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

        # Award PP immediately only for auto-approve types
        if status == "approved" and award > 0:
            await PointsService.create_transaction(
                db=db, user_id=user.id, amount=float(award),
                transaction_type=TransactionType.QUEST_REWARD,
                reason=f"Quest reward: {quest.title}",
            )

        await db.refresh(completion)
        return completion

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
        # Sellers must escrow PP up front + a 50 PP listing fee (Chapter 5.4).
        if data.side == "sell":
            required = data.pp_amount + 50
            if float(user.points or 0) < required:
                raise ValueError("Insufficient PP to escrow this sell order (incl. 50 PP listing fee)")
            await PointsService.create_transaction(
                db=db, user_id=user.id, amount=-50.0,
                transaction_type=TransactionType.ADMIN_PENALTY,
                reason="P2P listing fee",
            )
        order = P2POrder(
            seller_id=user.id if data.side == "sell" else None,
            buyer_id=user.id if data.side == "buy" else None,
            side=data.side, pp_amount=data.pp_amount, price=data.price,
            currency=data.currency, payment_method=data.payment_method, status="open",
        )
        db.add(order)
        await db.flush()
        await db.refresh(order)
        return order

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
        if float(user.points or 0) < pp_amount:
            raise ValueError("Insufficient PP to stake")
        await PointsService.create_transaction(
            db=db, user_id=user.id, amount=-float(pp_amount),
            transaction_type=TransactionType.ADMIN_PENALTY,
            reason=f"Stake locked ({lock_days}d)",
        )
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
        if stake.accrued and float(stake.accrued) > 0:
            await PointsService.create_transaction(
                db=db, user_id=user.id, amount=float(stake.accrued),
                transaction_type=TransactionType.ADMIN_BONUS,
                reason="Staking rewards claimed",
            )
            stake.accrued = 0
        await db.flush()
        await db.refresh(stake)
        return stake

    # ── Campaigns (Chapter 11) ──────────────────────────────────────────────
    @staticmethod
    async def list_campaigns(db: AsyncSession) -> list[Campaign]:
        rows = (await db.execute(
            select(Campaign, Partner.name)
            .join(Partner, Partner.id == Campaign.partner_id)
            .where(Campaign.status == "active")
            .order_by(Campaign.featured.desc(), Campaign.created_at.desc())
        )).all()
        campaigns = []
        for campaign, brand in rows:
            campaign.brand = brand  # transient attr for the response schema
            campaigns.append(campaign)
        return campaigns

    @staticmethod
    async def join_campaign(db: AsyncSession, user: User, campaign_id: uuid.UUID) -> CampaignParticipation:
        campaign = (await db.execute(select(Campaign).where(Campaign.id == campaign_id))).scalar_one_or_none()
        if not campaign or campaign.status != "active":
            raise ValueError("Campaign not found or inactive")
        existing = (await db.execute(
            select(CampaignParticipation).where(
                CampaignParticipation.campaign_id == campaign_id,
                CampaignParticipation.user_id == user.id,
            )
        )).scalar_one_or_none()
        if existing:
            raise ValueError("Already joined this campaign")
        part = CampaignParticipation(campaign_id=campaign_id, user_id=user.id)
        db.add(part)
        campaign.total_participants += 1
        await db.flush()
        await db.refresh(part)
        return part

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
        product = _CATALOG_BY_ID.get(product_id)
        if not product:
            raise ValueError("Unknown product")
        cost = product["pp"]
        if float(user.points or 0) < cost:
            raise ValueError("Insufficient Panda Points for this redemption")

        await PointsService.create_transaction(
            db=db, user_id=user.id, amount=-float(cost),
            transaction_type=TransactionType.ADMIN_PENALTY,
            reason=f"Redeemed {product['name']}",
        )
        code = "MJ-" + secrets.token_hex(3).upper() + "-" + secrets.token_hex(3).upper()
        redemption = Redemption(
            user_id=user.id, product_id=product_id, product_name=product["name"],
            category=product["category"], pp_cost=cost, destination=destination,
            voucher_code=code, status="completed",
        )
        db.add(redemption)
        await db.flush()
        await db.refresh(redemption)
        return redemption
