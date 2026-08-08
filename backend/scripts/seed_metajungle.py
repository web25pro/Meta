"""Seed the Meta-Jungle catalogs (quests, courses, partners, campaigns).

Idempotent: only inserts rows when a table is empty.

Usage:
    python -m scripts.seed_metajungle
"""
import asyncio
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func

from app.core.database import AsyncSessionLocal
from app.models import Quest, Course, Partner, Campaign, CampaignTask


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
                Campaign(partner_id=partners[0].id, slug="provide-liquidity-earn",
                         title="Provide liquidity & earn",
                         blurb="Add liquidity to the LPANDA/USDC pool and verify on-chain.",
                         pp_budget=500000, pp_per_task=500, status="active",
                         featured=True, starts_at=now, ends_at=now + timedelta(days=6)),
                Campaign(partner_id=partners[1].id, slug="shop-review-challenge",
                         title="Shop & review challenge",
                         blurb="Make a verified purchase and leave a review.",
                         pp_budget=120000, pp_per_task=200, status="active",
                         starts_at=now, ends_at=now + timedelta(days=12)),
                Campaign(partner_id=partners[2].id, slug="bridge-to-base-quest",
                         title="Bridge to Base quest",
                         blurb="Bridge any asset to Base and complete a swap.",
                         pp_budget=250000, pp_per_task=350, status="active",
                         starts_at=now, ends_at=now + timedelta(days=3)),
                Campaign(partner_id=partners[3].id, slug="learn-a-language-streak",
                         title="Learn a language streak",
                         blurb="Hit a 7-day streak in any course.",
                         pp_budget=80000, pp_per_task=150, status="active",
                         starts_at=now, ends_at=now + timedelta(days=20)),
            ]
            db.add_all(campaigns)
            await db.flush()

            # Real tasks, so joining a campaign leads somewhere. pp_claimed and
            # total_participants start at 0 and are driven by actual completions.
            tasks = [
                CampaignTask(campaign_id=campaigns[0].id, title="Add LPANDA/USDC liquidity",
                             description="Supply at least $50 of liquidity to the pool.",
                             pp_reward=500, verification_type="on_chain", order_index=0),
                CampaignTask(campaign_id=campaigns[0].id, title="Hold the position for 7 days",
                             description="Keep your liquidity in the pool for a full week.",
                             pp_reward=250, verification_type="on_chain", order_index=1),
                CampaignTask(campaign_id=campaigns[1].id, title="Make a verified purchase",
                             description="Buy anything from the partner store.",
                             pp_reward=200, verification_type="screenshot", order_index=0),
                CampaignTask(campaign_id=campaigns[1].id, title="Leave a product review",
                             description="Post an honest review of what you bought.",
                             pp_reward=100, verification_type="manual", order_index=1),
                CampaignTask(campaign_id=campaigns[2].id, title="Bridge an asset to Base",
                             description="Bridge any supported asset to the Base network.",
                             pp_reward=350, verification_type="on_chain", order_index=0),
                CampaignTask(campaign_id=campaigns[2].id, title="Complete a swap on Base",
                             description="Swap any pair on a supported Base DEX.",
                             pp_reward=150, verification_type="on_chain", order_index=1),
                CampaignTask(campaign_id=campaigns[3].id, title="Study for 7 days straight",
                             description="Keep a 7-day streak in any Learn-to-earn course.",
                             pp_reward=150, verification_type="webhook", daily_limit=1, order_index=0),
            ]
            db.add_all(tasks)
            print(f"seeded {len(partners)} partners, {len(campaigns)} campaigns, {len(tasks)} campaign tasks")

        await db.commit()
    print("Meta-Jungle seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
