/**
 * LPanda Premium membership API client.
 * Handles wallet connection, NFT verification, tier status, and tier config.
 */
import apiClient from '@/lib/api';

// ── Types ────────────────────────────────────────────────────────────────────

export interface TierBenefits {
  daily_quest_limit: number | null;
  monthly_campaign_limit: number | null;
  can_create_campaign: boolean;
  campaign_feature_level: string;
  can_use_media: boolean;
  can_create_video_contest: boolean;
  can_create_bounty: boolean;
}

export interface NextTierInfo {
  name: string;
  nfts_required: number;
  nfts_needed: number;
}

export interface WalletConnectResponse {
  tier: string;
  tier_name: string;
  nft_count: number;
  wallet_address: string;
  benefits: TierBenefits;
  next_tier: NextTierInfo | null;
}

export interface QuestUsage {
  used: number;
  limit: number | null;
  unlimited: boolean;
}

export interface CampaignUsage {
  used: number;
  limit: number | null;
  unlimited: boolean;
}

export interface MembershipStatus {
  tier: string;
  tier_name: string;
  nft_count: number;
  wallet_address: string | null;
  wallet_verified_at: string | null;
  tier_updated_at: string | null;
  usage: {
    quests_today: QuestUsage;
    campaigns_this_month: CampaignUsage;
  };
  permissions: TierBenefits;
  next_tier: NextTierInfo | null;
  available_points: number;
  locked_points: number;
  escrow_points: number;
}

export interface TierInfo {
  key: string;
  name: string;
  nft_required: number;
  daily_quest_limit: number | null;
  monthly_campaign_limit: number | null;
  can_create_campaign: boolean;
  campaign_feature_level: string;
  can_use_media: boolean;
  can_create_video_contest: boolean;
  can_create_bounty: boolean;
  description: string;
}

// ── API calls ────────────────────────────────────────────────────────────────

export const premiumAPI = {
  /** Connect wallet and verify NFT ownership */
  connectWallet: async (walletAddress: string): Promise<WalletConnectResponse> => {
    const { data } = await apiClient.post('/premium/connect-wallet', {
      wallet_address: walletAddress,
    });
    return data;
  },

  /** Re-check NFT balance and update tier */
  revalidate: async (): Promise<WalletConnectResponse> => {
    const { data } = await apiClient.post('/premium/revalidate');
    return data;
  },

  /** Get current membership status */
  getStatus: async (): Promise<MembershipStatus> => {
    const { data } = await apiClient.get('/premium/status');
    return data;
  },

  /** Get all tier configurations */
  getTiers: async (): Promise<TierInfo[]> => {
    const { data } = await apiClient.get('/premium/tiers');
    return data.tiers;
  },
};
