import apiClient from '@/lib/api';

export interface CommunityRegisterRequest {
  email: string;
  password: string;
  username: string;
  referral_code?: string;
}

export interface CommunityUserResponse {
  id: string;
  email: string;
  username: string;
  email_verified: boolean;
  referral_code: string;
  points: number;
  xp: number;
  level: number;
  current_streak: number;
  created_at: string;
}

export interface ReferralCodeResponse {
  referral_code: string;
  referral_link: string;
}

export interface ReferralStatsResponse {
  total_referrals: number;
  successful_referrals: number;
  referral_earnings: number;
}

export const communityAPI = {
  /**
   * Register a new community user
   */
  register: async (data: CommunityRegisterRequest): Promise<CommunityUserResponse> => {
    const response = await apiClient.post<CommunityUserResponse>('/community/register', data);
    return response.data;
  },

  /**
   * Login to community account
   */
  communityLogin: async (email: string, password: string): Promise<{ access_token: string; refresh_token: string; user: CommunityUserResponse }> => {
    const response = await apiClient.post('/community/login', { email, password });
    return response.data;
  },

  /**
   * Get referral code and link
   */
  getReferralCode: async (): Promise<ReferralCodeResponse> => {
    const response = await apiClient.get<ReferralCodeResponse>('/community/referral-code');
    return response.data;
  },

  getReferralStats: async (): Promise<ReferralStatsResponse> => {
    const response = await apiClient.get<ReferralStatsResponse>('/community/referral-stats');
    return response.data;
  },
};
