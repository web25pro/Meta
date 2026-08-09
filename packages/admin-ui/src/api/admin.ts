/** Admin panel API client (Overall_Admin only). */
import apiClient from '@meta-jungle/api-client';

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
  action_url?: string | null;
  is_active: boolean;
  starts_at?: string | null;
  ends_at?: string | null;
}

export interface AdminCampaign {
  id: string;
  slug: string;
  brand?: string | null;
  title: string;
  blurb: string;
  pp_budget: number;
  pp_per_task: number;
  pp_claimed: number;
  pp_reserved: number;
  pp_available: number;
  status: 'draft' | 'active' | 'paused' | 'ended';
  featured: boolean;
  total_participants: number;
  max_participants?: number | null;
  target_regions: string[];
  target_roles: string[];
  min_role: string;
  starts_at?: string | null;
  ends_at?: string | null;
}

export interface AdminCampaignTask {
  id: string;
  campaign_id: string;
  title: string;
  description: string;
  pp_reward: number;
  verification_type: string;
  daily_limit: number;
  action_url?: string | null;
  order_index: number;
  is_active: boolean;
}

export interface AdminCampaignReviewItem {
  id: string;
  campaign_id: string;
  campaign_title: string;
  task_id: string;
  task_title: string;
  user_id: string;
  username: string;
  pp_awarded: number;
  proof?: Record<string, unknown> | null;
  created_at: string;
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
    status?: string;
    target_regions?: string[];
    target_roles?: string[];
    min_role?: string;
    max_participants?: number | null;
  }) => (await apiClient.post('/admin/campaigns', body)).data,
  setCampaignStatus: async (id: string, status: string) =>
    (await apiClient.patch(`/admin/campaigns/${id}`, { status })).data,
  deleteCampaign: async (id: string): Promise<{ rejected_pending: number }> =>
    (await apiClient.delete(`/admin/campaigns/${id}`)).data,

  listCampaignTasks: async (id: string): Promise<AdminCampaignTask[]> =>
    (await apiClient.get(`/admin/campaigns/${id}/tasks`)).data.tasks,
  createCampaignTask: async (
    id: string,
    body: {
      title: string;
      description?: string;
      pp_reward: number;
      verification_type?: string;
      daily_limit?: number;
      action_url?: string | null;
      order_index?: number;
    },
  ) => (await apiClient.post(`/admin/campaigns/${id}/tasks`, body)).data,
  setCampaignTaskActive: async (campaignId: string, taskId: string, is_active: boolean) =>
    (await apiClient.patch(`/admin/campaigns/${campaignId}/tasks/${taskId}/active`, { is_active }))
      .data,

  campaignReviewQueue: async (): Promise<AdminCampaignReviewItem[]> =>
    (await apiClient.get('/admin/campaigns/review-queue')).data.completions,
  reviewCampaignCompletion: async (completionId: string, approve: boolean, reason?: string) =>
    (await apiClient.post(`/admin/campaigns/review-queue/${completionId}`, { approve, reason })).data,

  grantNFT: async (body: { user_id: string; name?: string; tier?: string; daily_pp_rate?: number }) =>
    (await apiClient.post('/admin/nft/grant', body)).data,

  listCompletions: async (status = 'pending', page = 1) =>
    (await apiClient.get('/admin/quest-completions', { params: { status, page, page_size: 20 } })).data,
  reviewCompletion: async (id: string, approve: boolean, reason?: string) =>
    (await apiClient.post(`/admin/quest-completions/${id}/review`, null, { params: { approve, reason } })).data,
};
