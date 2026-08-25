"""Centralized LPanda membership tier configuration.

All tier-gated permissions and limits are defined here. Other services import
from this module instead of hard-coding tier logic throughout the application.

To add a new tier or adjust limits, edit ``MEMBERSHIP_TIERS`` and the helper
functions will pick up the changes automatically.
"""

from __future__ import annotations

from typing import Optional


# ── Tier definitions ─────────────────────────────────────────────────────────
# Keys are stored in the ``users.membership_tier`` column.  The tiers are
# ordered from lowest to highest; ``get_tier_for_nft_count`` walks the list
# in reverse to find the highest tier the user qualifies for.

MEMBERSHIP_TIERS: dict[str, dict] = {
    "standard": {
        "name": "Standard",
        "nft_required": 0,
        "daily_quest_limit": 3,          # None == unlimited
        "monthly_campaign_limit": 1,
        "can_create_campaign": False,
        "campaign_feature_level": "none",   # none | limited | full
        "can_use_media": False,
        "can_create_video_contest": False,
        "can_create_bounty": False,
        "description": "Free tier — basic access to quests and campaigns.",
    },
    "panda_plus": {
        "name": "Panda Plus",
        "nft_required": 1,
        "daily_quest_limit": 5,
        "monthly_campaign_limit": 3,
        "can_create_campaign": False,
        "campaign_feature_level": "none",
        "can_use_media": False,
        "can_create_video_contest": False,
        "can_create_bounty": False,
        "description": "Hold 1 LPanda NFT to unlock extended quest and campaign access.",
    },
    "panda_pro": {
        "name": "Panda Pro",
        "nft_required": 3,
        "daily_quest_limit": 15,
        "monthly_campaign_limit": 10,
        "can_create_campaign": True,
        "campaign_feature_level": "limited",
        "can_use_media": False,
        "can_create_video_contest": False,
        "can_create_bounty": False,
        "description": "Hold 3 LPanda NFTs to unlock campaign creation with limited features.",
    },
    "panda_elite": {
        "name": "Panda Elite",
        "nft_required": 5,
        "daily_quest_limit": None,       # unlimited
        "monthly_campaign_limit": None,   # unlimited
        "can_create_campaign": True,
        "campaign_feature_level": "full",
        "can_use_media": True,
        "can_create_video_contest": True,
        "can_create_bounty": True,
        "description": "Hold 5+ LPanda NFTs for unlimited access and full campaign creation.",
    },
}

# Ordered list of tier keys from lowest to highest.
TIER_ORDER: list[str] = ["standard", "panda_plus", "panda_pro", "panda_elite"]


# ── Helper functions ─────────────────────────────────────────────────────────

def get_tier_for_nft_count(count: int) -> str:
    """Return the highest tier key the user qualifies for given *count* NFTs."""
    result = "standard"
    for tier_key in TIER_ORDER:
        if count >= MEMBERSHIP_TIERS[tier_key]["nft_required"]:
            result = tier_key
    return result


def get_tier_config(tier: str) -> dict:
    """Return the full configuration dict for *tier*.

    Raises ``KeyError`` if the tier key is unknown.
    """
    return MEMBERSHIP_TIERS[tier]


def get_tier_permissions(tier: str) -> dict:
    """Return only the permission/limit flags for *tier* (excludes metadata)."""
    cfg = MEMBERSHIP_TIERS[tier]
    return {
        "daily_quest_limit": cfg["daily_quest_limit"],
        "monthly_campaign_limit": cfg["monthly_campaign_limit"],
        "can_create_campaign": cfg["can_create_campaign"],
        "campaign_feature_level": cfg["campaign_feature_level"],
        "can_use_media": cfg["can_use_media"],
        "can_create_video_contest": cfg["can_create_video_contest"],
        "can_create_bounty": cfg["can_create_bounty"],
    }


def get_next_tier(current_tier: str) -> Optional[tuple[str, int]]:
    """Return ``(next_tier_name, nfts_needed)`` or ``None`` if already max."""
    try:
        idx = TIER_ORDER.index(current_tier)
    except ValueError:
        return None
    if idx >= len(TIER_ORDER) - 1:
        return None
    next_key = TIER_ORDER[idx + 1]
    return MEMBERSHIP_TIERS[next_key]["name"], MEMBERSHIP_TIERS[next_key]["nft_required"]


def get_all_tiers() -> list[dict]:
    """Return a list of all tier configs in order (for the comparison UI)."""
    return [
        {"key": k, **MEMBERSHIP_TIERS[k]}
        for k in TIER_ORDER
    ]
