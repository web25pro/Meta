"""Seed the Meta-Jungle catalogs (quests, courses, partners, campaigns).

Idempotent: only inserts rows when a table is empty.

Usage:
    python -m scripts.seed_metajungle
"""
import asyncio
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func

from app.core.database import AsyncSessionLocal
from app.models import Quest, Course, Partner, Campaign


QUESTS = [
    {"title": "Daily check-in", "description": "Log in every day to grow your streak.", "pp_reward": 10, "category": "daily", "verification_type": "manual", "daily_limit": 1},
    {"title": "Follow @LPanda on X", "description": "Connect your X account and follow @LPanda.", "pp_reward": 50, "category": "social", "verification_type": "oauth", "daily_limit": 1},
    {"title": "Retweet the launch post", "description": "Share the pinned launch announcement.", "pp_reward": 30, "category": "social", "verification_type": "webhook", "daily_limit": 3},
    {"title": "Complete the Web3 basics quiz", "description": "Score 80%+ on the 10-question quiz.", "pp_reward": 200, "category": "learning", "verification_type": "manual", "daily_limit": 1},
    {"title": "Refer a friend", "description": "Invite a friend who completes 3 quests in 7 days.", "pp_reward": 300, "category": "referral", "verification_type": "manual", "daily_limit": 1},
    {"title": "Watch & verify video", "description": "Watch the featured explainer to the end.", "pp_reward": 40, "category": "social", "verification_type": "webhook", "daily_limit": 3},
]

COURSES = [
    {"title": "Web3 Foundations", "blurb": "Wallets, keys, and how blockchains work.", "level": "Beginner", "lessons": 6, "pp_reward": 200,
     "quiz": {"questions": [{"q": "What secures a wallet?", "options": ["A username", "A private key", "An email", "A phone"], "answer": 1}]}},
    {"title": "Understanding Base", "blurb": "Why L2s matter and how Base scales Ethereum.", "level": "Beginner", "lessons": 5, "pp_reward": 250,
     "quiz": {"questions": [{"q": "Base is a…", "options": ["Layer 1", "Layer 2 rollup", "Bank", "Stablecoin"], "answer": 1}]}},
    {"title": "DeFi Essentials", "blurb": "Liquidity, yield, and managing risk.", "level": "Intermediate", "lessons": 8, "pp_reward": 400,
     "quiz": {"questions": [{"q": "Providing liquidity risks…", "options": ["Nothing", "Impermanent loss", "Gas only", "Bans"], "answer": 1}]}},
    {"title": "NFT Utility & Reputation", "blurb": "How NFTs unlock real-world value.", "level": "Intermediate", "lessons": 4, "pp_reward": 300,
     "quiz": {"questions": [{"q": "A soul-bound NFT is…", "options": ["Tradable", "Non-transferable", "Free", "A coin"], "answer": 1}]}},
]

PARTNERS = [
    {"name": "Aerodrome", "tier": "platinum", "is_verified": True},
    {"name": "Jumia", "tier": "gold", "is_verified": True},
    {"name": "Base", "tier": "platinum", "is_verified": True},
    {"name": "Duolingo", "tier": "silver", "is_verified": True},
]


async def _empty(db, model) -> bool:
    return (await db.execute(select(func.count()).select_from(model))).scalar() == 0


async def seed() -> None:
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        if await _empty(db, Quest):
            db.add_all([Quest(**q, is_active=True, starts_at=now) for q in QUESTS])
            print(f"seeded {len(QUESTS)} quests")

        if await _empty(db, Course):
            db.add_all([Course(**c, is_active=True) for c in COURSES])
            print(f"seeded {len(COURSES)} courses")

        if await _empty(db, Partner):
            partners = [Partner(name=p["name"], tier=p["tier"], is_verified=p["is_verified"]) for p in PARTNERS]
            db.add_all(partners)
            await db.flush()
            campaigns = [
                Campaign(partner_id=partners[0].id, title="Provide liquidity & earn",
                         blurb="Add liquidity to the LPANDA/USDC pool and verify on-chain.",
                         pp_budget=500000, pp_per_task=500, pp_claimed=310000, status="active",
                         featured=True, total_participants=1240, ends_at=now + timedelta(days=6)),
                Campaign(partner_id=partners[1].id, title="Shop & review challenge",
                         blurb="Make a verified purchase and leave a review.",
                         pp_budget=120000, pp_per_task=200, pp_claimed=49000, status="active",
                         total_participants=880, ends_at=now + timedelta(days=12)),
                Campaign(partner_id=partners[2].id, title="Bridge to Base quest",
                         blurb="Bridge any asset to Base and complete a swap.",
                         pp_budget=250000, pp_per_task=350, pp_claimed=220000, status="active",
                         total_participants=2010, ends_at=now + timedelta(days=3)),
                Campaign(partner_id=partners[3].id, title="Learn a language streak",
                         blurb="Hit a 7-day streak in any course.",
                         pp_budget=80000, pp_per_task=150, pp_claimed=18400, status="active",
                         total_participants=540, ends_at=now + timedelta(days=20)),
            ]
            db.add_all(campaigns)
            print(f"seeded {len(partners)} partners and {len(campaigns)} campaigns")

        await db.commit()
    print("Meta-Jungle seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
