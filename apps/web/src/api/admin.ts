/** Admin panel API client (Overall_Admin only). */
import apiClient from '@/lib/api';

export interface AdminOverview {
  total_users: number;
  banned_users: number;
  pp_issued: number;
  pp_spent: number;
  redemptions: number;
  active_campaigns: number;
  quests: number;
  quest_completions: number;
  nfts_held: number;
}

export interface AdminUser {
  id: string;
  name: string;
  username?: string | null;
  email: string;
  role: string;
  user_type: string;
  points: number;
  is_banned: boolean;
  is_active: boolean;
  email_verified: boolean;
  created_at: string;
}

export interface AdminQuest {
  id: string;
  title: string;
  description: string;
  pp_reward: number;
  category: string;
  verification_type: string;
  min_role: string;
  daily_limit: number;
  is_active: boolean;
  starts_at?: string | null;
  ends_at?: string | null;
}

export interface AdminCampaign {
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
}

export interface AdminPartner {
  id: string;
  name: string;
  tier: string;
  is_verified: boolean;
}

export const adminAPI = {
  overview: async (): Promise<AdminOverview> => (await apiClient.get('/admin/overview')).data,

  listUsers: async (page = 1, q = ''): Promise<{ users: AdminUser[]; total: number }> =>
    (await apiClient.get('/admin/users', { params: { page, ...(q ? { q } : {}) } })).data,
  updateUser: async (id: string, body: { role?: string; is_active?: boolean }) =>
    (await apiClient.patch(`/admin/users/${id}`, body)).data,
  adjustPoints: async (id: string, amount: number, reason: string) =>
    (await apiClient.post(`/admin/users/${id}/points`, { amount, reason })).data,

  listQuests: async (): Promise<AdminQuest[]> => (await apiClient.get('/admin/quests')).data,
  createQuest: async (body: Partial<AdminQuest>) => (await apiClient.post('/admin/quests', body)).data,
  updateQuest: async (id: string, body: Partial<AdminQuest>) =>
    (await apiClient.patch(`/admin/quests/${id}`, body)).data,
  deleteQuest: async (id: string) => (await apiClient.delete(`/admin/quests/${id}`)).data,

  listPartners: async (): Promise<AdminPartner[]> => (await apiClient.get('/admin/partners')).data,
  createPartner: async (body: { name: string; tier?: string }) =>
    (await apiClient.post('/admin/partners', body)).data,

  listCampaigns: async (): Promise<AdminCampaign[]> => (await apiClient.get('/admin/campaigns')).data,
  createCampaign: async (body: {
    partner_id: string;
    title: string;
    blurb?: string;
    pp_budget: number;
    pp_per_task: number;
    featured?: boolean;
    days?: number;
  }) => (await apiClient.post('/admin/campaigns', body)).data,
  setCampaignStatus: async (id: string, status: string) =>
    (await apiClient.patch(`/admin/campaigns/${id}`, { status })).data,

  grantNFT: async (body: { user_id: string; name?: string; tier?: string; daily_pp_rate?: number }) =>
    (await apiClient.post('/admin/nft/grant', body)).data,

  listCompletions: async (status = 'pending', page = 1) =>
    (await apiClient.get('/admin/quest-completions', { params: { status, page, page_size: 20 } })).data,
  reviewCompletion: async (id: string, approve: boolean) =>
    (await apiClient.post(`/admin/quest-completions/${id}/review`, null, { params: { approve } })).data,
};
