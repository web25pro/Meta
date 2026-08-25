"""Wallet connection and LPanda NFT verification service.

Queries the LPanda ERC-721 contract via JSON-RPC (Alchemy / Infura) to count
NFTs held by a wallet address, then maps the count to a membership tier.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.core.tier_config import get_tier_for_nft_count, get_tier_config, get_next_tier
from app.models.user import User
from app.models.metajungle import NFTHolding

logger = get_logger(__name__)

# Minimal ERC-721 ABI fragment for ``balanceOf(address)``.
# Encoded call: keccak256("balanceOf(address)")[:4] = 0x70a08231
_BALANCE_OF_SELECTOR = "0x70a08231"


class WalletService:
    """Wallet connection and NFT balance verification."""

    # ── NFT balance query ────────────────────────────────────────────────────

    @staticmethod
    async def query_nft_balance(wallet_address: str) -> int:
        """Query the LPanda NFT contract for the number of tokens held by *wallet_address*.

        Uses ``balanceOf(address)`` via the configured JSON-RPC endpoint.
        Returns 0 if the RPC call fails or the contract is not configured.
        """
        contract = settings.LPANDA_NFT_CONTRACT
        rpc_url = settings.ETH_RPC_URL

        if not contract or not rpc_url:
            logger.warning("NFT verification skipped — LPANDA_NFT_CONTRACT or ETH_RPC_URL not configured")
            return 0

        # Pad address to 32 bytes (remove 0x prefix, left-pad with zeros)
        addr = wallet_address.lower().replace("0x", "").zfill(64)
        data = f"{_BALANCE_OF_SELECTOR}{addr}"

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_call",
            "params": [{"to": contract, "data": data}, "latest"],
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(rpc_url, json=payload)
                resp.raise_for_status()
                result = resp.json()

            if "error" in result:
                logger.error("RPC error querying NFT balance", extra={"error": result["error"]})
                return 0

            hex_value = result.get("result", "0x0")
            return int(hex_value, 16)

        except Exception:
            logger.exception("Failed to query NFT balance via RPC")
            return 0

    # ── Wallet connection + tier assignment ──────────────────────────────────

    @staticmethod
    async def verify_and_update_tier(
        db: AsyncSession,
        user_id: uuid.UUID,
        wallet_address: str,
    ) -> dict:
        """Connect a wallet, query NFT balance, and update the user's membership tier.

        Returns a dict with ``tier``, ``nft_count``, ``benefits``, and
        ``next_tier`` information.
        """
        # Normalise address
        wallet_address = wallet_address.strip().lower()
        if not wallet_address.startswith("0x") or len(wallet_address) != 42:
            raise ValueError("Invalid EVM wallet address")

        # Load user
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        # Query on-chain NFT balance
        nft_count = await WalletService.query_nft_balance(wallet_address)

        # Determine tier
        tier_key = get_tier_for_nft_count(nft_count)
        tier_cfg = get_tier_config(tier_key)
        now = datetime.now(timezone.utc)

        # Update user record
        user.wallet_address = wallet_address
        user.wallet_verified_at = now
        user.membership_tier = tier_key
        user.tier_updated_at = now
        await db.flush()
        await db.refresh(user)

        # Build response
        next_tier = get_next_tier(tier_key)
        next_info = None
        if next_tier:
            next_name, next_nfts = next_tier
            next_info = {
                "name": next_name,
                "nfts_required": next_nfts,
                "nfts_needed": max(0, next_nfts - nft_count),
            }

        return {
            "tier": tier_key,
            "tier_name": tier_cfg["name"],
            "nft_count": nft_count,
            "wallet_address": wallet_address,
            "benefits": {
                "daily_quest_limit": tier_cfg["daily_quest_limit"],
                "monthly_campaign_limit": tier_cfg["monthly_campaign_limit"],
                "can_create_campaign": tier_cfg["can_create_campaign"],
                "campaign_feature_level": tier_cfg["campaign_feature_level"],
                "can_use_media": tier_cfg["can_use_media"],
                "can_create_video_contest": tier_cfg["can_create_video_contest"],
                "can_create_bounty": tier_cfg["can_create_bounty"],
            },
            "next_tier": next_info,
        }

    # ── Periodic revalidation ────────────────────────────────────────────────

    @staticmethod
    async def revalidate_tier(db: AsyncSession, user_id: uuid.UUID) -> dict:
        """Re-check the user's NFT balance and update tier if it has changed.

        Returns the same shape as ``verify_and_update_tier``.
        """
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")
        if not user.wallet_address:
            raise ValueError("No wallet connected")

        nft_count = await WalletService.query_nft_balance(user.wallet_address)
        tier_key = get_tier_for_nft_count(nft_count)
        tier_cfg = get_tier_config(tier_key)
        now = datetime.now(timezone.utc)

        tier_changed = tier_key != user.membership_tier
        user.membership_tier = tier_key
        user.tier_updated_at = now
        user.wallet_verified_at = now
        await db.flush()
        await db.refresh(user)

        next_tier = get_next_tier(tier_key)
        next_info = None
        if next_tier:
            next_name, next_nfts = next_tier
            next_info = {
                "name": next_name,
                "nfts_required": next_nfts,
                "nfts_needed": max(0, next_nfts - nft_count),
            }

        return {
            "tier": tier_key,
            "tier_name": tier_cfg["name"],
            "nft_count": nft_count,
            "wallet_address": user.wallet_address,
            "tier_changed": tier_changed,
            "benefits": {
                "daily_quest_limit": tier_cfg["daily_quest_limit"],
                "monthly_campaign_limit": tier_cfg["monthly_campaign_limit"],
                "can_create_campaign": tier_cfg["can_create_campaign"],
                "campaign_feature_level": tier_cfg["campaign_feature_level"],
                "can_use_media": tier_cfg["can_use_media"],
                "can_create_video_contest": tier_cfg["can_create_video_contest"],
                "can_create_bounty": tier_cfg["can_create_bounty"],
            },
            "next_tier": next_info,
        }
