/**
 * @meta-jungle/types — shared domain model.
 * Master Prompt v3.0: Chapter 5 (PP economy), Chapter 6 (reputation),
 * Chapter 9 (database schema).
 */

// ── Identity & geography ───────────────────────────────────────────────────
export type Region = 'africa' | 'asia' | 'europe' | 'other';

// ── Reputation system (Chapter 6) ──────────────────────────────────────────
/** Roles unlocked by the three-score thresholds (Chapter 6.2). */
export type Role =
  | 'Explorer'
  | 'Tracker'
  | 'Hunter'
  | 'Whitelist'
  | 'OG Panda'
  | 'Alpha OG';

/** Three independent 0–1000 scores (Chapter 6.1). */
export interface ReputationScores {
  /** Platform engagement intensity (outer ring, sky). */
  activityScore: number;
  /** Trustworthiness & community value (middle ring, cobalt). */
  reputationScore: number;
  /** Ecosystem growth contribution (inner ring, bamboo gold). */
  influenceScore: number;
  role: Role;
  updatedAt: string;
}

/** Role threshold table from Chapter 6.2. */
export interface RoleThreshold {
  role: Role;
  minActivity: number;
  minReputation: number;
  minInfluence: number;
  minNFTs: number;
  /** Daily earn multiplier unlocked at this role. */
  earnMultiplier: number;
}

export const ROLE_THRESHOLDS: RoleThreshold[] = [
  { role: 'Explorer', minActivity: 0, minReputation: 0, minInfluence: 0, minNFTs: 0, earnMultiplier: 1 },
  { role: 'Tracker', minActivity: 200, minReputation: 100, minInfluence: 0, minNFTs: 0, earnMultiplier: 1 },
  { role: 'Hunter', minActivity: 400, minReputation: 300, minInfluence: 100, minNFTs: 0, earnMultiplier: 1 },
  { role: 'Whitelist', minActivity: 600, minReputation: 500, minInfluence: 200, minNFTs: 0, earnMultiplier: 1.2 },
  { role: 'OG Panda', minActivity: 800, minReputation: 700, minInfluence: 400, minNFTs: 1, earnMultiplier: 1.5 },
  { role: 'Alpha OG', minActivity: 950, minReputation: 900, minInfluence: 700, minNFTs: 3, earnMultiplier: 2 },
];

// ── User (Chapter 9: users) ────────────────────────────────────────────────
export interface User {
  id: string;
  walletAddress?: string;
  username: string;
  email?: string | null;
  region: Region;
  createdAt: string;
  lastActive: string;
  isKycLite: boolean;
  isBanned: boolean;
  referrerId?: string | null;
}

// ── Panda Points economy (Chapter 5) ───────────────────────────────────────
/** 1,000 PP = $10 USD (Chapter 5.1). */
export const PP_PER_USD = 100;

export const DAILY_EARN_CAP = {
  noNft: 500,
  oneNft: 750,
  threePlusNft: 1200,
  hardCap: 2000,
} as const;

export type PPActionType =
  | 'daily_login'
  | 'streak_bonus'
  | 'follow_twitter'
  | 'retweet'
  | 'quiz'
  | 'watch_video'
  | 'referral'
  | 'nft_hold'
  | 'partner_task'
  | 'community_content'
  | 'bug_report'
  | 'spend'
  | 'p2p_lock'
  | 'p2p_release';

/** A single PP ledger entry (Chapter 9: pp_ledger). Positive = earn, negative = spend. */
export interface PPLedgerEntry {
  id: string;
  userId: string;
  amount: number;
  actionType: PPActionType;
  referenceId?: string;
  onChainTx?: string | null;
  createdAt: string;
  note?: string;
}

// ── NFTs (Chapter 9: nft_holdings) ─────────────────────────────────────────
export type NFTTier = 'common' | 'rare' | 'epic' | 'legendary';

export interface NFTHolding {
  id: string;
  userId: string;
  contractAddress: string;
  tokenId: string;
  tier: NFTTier;
  dailyPpRate: number;
  lastVerifiedAt: string;
  isStaked: boolean;
}

// ── Quests (Chapter 9: quests / quest_completions) ─────────────────────────
export type QuestCategory =
  | 'social'
  | 'partner'
  | 'nft'
  | 'learning'
  | 'referral'
  | 'daily';

export type VerificationType = 'oauth' | 'screenshot' | 'on_chain' | 'webhook' | 'manual';

export interface Quest {
  id: string;
  title: string;
  description: string;
  ppReward: number;
  steps: { label: string; verification: VerificationType }[];
  verificationType: VerificationType;
  category: QuestCategory;
  startAt: string;
  endAt?: string;
  isActive: boolean;
  minRole: Role;
  partnerId?: string | null;
}

export type CompletionStatus = 'pending' | 'approved' | 'rejected';

export interface QuestCompletion {
  id: string;
  userId: string;
  questId: string;
  completedAt: string;
  proof: Record<string, unknown>;
  ppAwarded: number;
  status: CompletionStatus;
}

// ── P2P (Chapter 9: p2p_orders) ────────────────────────────────────────────
export type P2POrderStatus = 'open' | 'locked' | 'completed' | 'cancelled' | 'disputed';

export interface P2POrder {
  id: string;
  sellerId: string;
  buyerId?: string | null;
  ppAmount: number;
  askingPrice: number;
  currency: string;
  paymentMethod: string;
  status: P2POrderStatus;
  escrowTx?: string;
  createdAt: string;
  completedAt?: string | null;
}

// ── Partners & campaigns (Chapter 9 / 11) ──────────────────────────────────
export type PartnerTier = 'bronze' | 'silver' | 'gold' | 'platinum';

export interface Partner {
  id: string;
  name: string;
  logoUrl: string;
  tier: PartnerTier;
  monthlySpend: number;
  createdAt: string;
  contactEmail: string;
  isVerified: boolean;
}

export interface Campaign {
  id: string;
  partnerId: string;
  title: string;
  ppBudget: number;
  ppPerTask: number;
  startAt: string;
  endAt: string;
  targetRegions: Region[];
  targetRoles: Role[];
  status: 'draft' | 'active' | 'paused' | 'ended';
  totalParticipants: number;
  createdAt: string;
}
