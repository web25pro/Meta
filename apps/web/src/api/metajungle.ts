/**
 * Meta-Jungle ecosystem API client (reputation, quests, NFT, P2P, staking,
 * campaigns, learn, marketplace). Backed by the FastAPI endpoints documented
 * in backend/METAJUNGLE_API.md.
 */
import apiClient from '@/lib/api';

// ── Reputation ──────────────────────────────────────────────────────────────
export interface Reputation {
  user_id: string;
  activity_score: number;
  reputation_score: number;
  influence_score: number;
  role: string;
  earn_multiplier: number;
  next_role: string | null;
}

// ── Quests ──────────────────────────────────────────────────────────────────
export interface ApiQuest {
  id: string;
  title: string;
  description: string;
  pp_reward: number;
  category: string;
  verification_type: string;
  min_role: string;
  steps?: { label: string; verification: string }[] | null;
  daily_limit: number;
  is_active: boolean;
  starts_at?: string | null;
  ends_at?: string | null;
}

// ── NFT ─────────────────────────────────────────────────────────────────────
export interface ApiNFT {
  id: string;
  name: string;
  tier: 'common' | 'rare' | 'epic' | 'legendary';
  daily_pp_rate: number;
  contract_address: string;
  token_id: string;
  traits?: { label: string; value: string }[] | null;
  utilities?: string[] | null;
  is_staked: boolean;
}

// ── P2P ─────────────────────────────────────────────────────────────────────
export interface ApiP2POrder {
  id: string;
  side: 'buy' | 'sell';
  pp_amount: number;
  price: number;
  currency: string;
  payment_method: string;
  status: string;
  seller_id?: string | null;
  buyer_id?: string | null;
  created_at: string;
}

// ── Staking ─────────────────────────────────────────────────────────────────
export interface ApiStake {
  id: string;
  asset: string;
  pp_amount: number;
  multiplier: number;
  lock_days: number;
  accrued: number;
  status: string;
  started_at: string;
  unlocked_at?: string | null;
}

// ── Campaigns ───────────────────────────────────────────────────────────────
export interface ApiCampaign {
  id: string;
  brand?: string | null;
  title: string;
  blurb: string;
  pp_budget: number;
  pp_per_task: number;
  pp_claimed: number;
  status: string;
  featured: boolean;
  total_participants: number;
  ends_at?: string | null;
}

// ── Learn ───────────────────────────────────────────────────────────────────
export interface ApiCourse {
  id: string;
  title: string;
  blurb: string;
  level: 'Beginner' | 'Intermediate' | 'Advanced';
  lessons: number;
  pp_reward: number;
  quiz?: { q: string; options: string[] } | null;
}

// ── Marketplace ─────────────────────────────────────────────────────────────
export interface ApiProduct {
  id: string;
  category: string;
  name: string;
  pp: number;
  fiat: string;
  provider: string;
  regions: string[];
  input: string;
}

export interface ApiRedemption {
  id: string;
  product_id: string;
  product_name: string;
  category: string;
  pp_cost: number;
  destination?: string | null;
  voucher_code: string;
  status: string;
  created_at: string;
}

export const metajungleAPI = {
  getReputation: async (): Promise<Reputation> =>
    (await apiClient.get('/reputation/me')).data,

  listQuests: async (): Promise<ApiQuest[]> =>
    (await apiClient.get('/quests')).data.quests,
  completeQuest: async (id: string, proof?: Record<string, unknown>) =>
    (await apiClient.post(`/quests/${id}/complete`, { proof: proof ?? null })).data,

  listNFTs: async (): Promise<{ nfts: ApiNFT[]; total_daily_yield: number }> =>
    (await apiClient.get('/nft')).data,

  listOrders: async (side?: 'buy' | 'sell'): Promise<ApiP2POrder[]> =>
    (await apiClient.get('/p2p/orders', { params: side ? { side } : {} })).data.orders,
  createOrder: async (body: {
    side: 'buy' | 'sell';
    pp_amount: number;
    price: number;
    currency?: string;
    payment_method: string;
  }) => (await apiClient.post('/p2p/orders', body)).data,

  listStakes: async (): Promise<{ stakes: ApiStake[]; total_staked: number; total_accrued: number }> =>
    (await apiClient.get('/staking')).data,
  createStake: async (pp_amount: number, lock_days: number) =>
    (await apiClient.post('/staking', { pp_amount, lock_days })).data,
  claimStake: async (id: string) =>
    (await apiClient.post(`/staking/${id}/claim`)).data,

  listCampaigns: async (): Promise<ApiCampaign[]> =>
    (await apiClient.get('/campaigns')).data.campaigns,
  joinCampaign: async (id: string) =>
    (await apiClient.post(`/campaigns/${id}/join`)).data,

  listCourses: async (): Promise<ApiCourse[]> =>
    (await apiClient.get('/learn/courses')).data.courses,
  submitQuiz: async (id: string, answers: number[]): Promise<{ passed: boolean; score: number; pp_awarded: number }> =>
    (await apiClient.post(`/learn/courses/${id}/quiz`, { answers })).data,

  getCatalog: async (): Promise<ApiProduct[]> =>
    (await apiClient.get('/marketplace/catalog')).data.products,
  redeem: async (product_id: string, destination?: string): Promise<ApiRedemption> =>
    (await apiClient.post('/marketplace/redeem', { product_id, destination: destination ?? null })).data,
};
