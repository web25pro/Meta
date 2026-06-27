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

export interface EmailVerificationResponse {
  message: string;
  email_verified: boolean;
}

export interface PasswordResetResponse {
  message: string;
}

export interface PasswordResetConfirmRequest {
  token: string;
  new_password: string;
}

export interface ReferralCodeResponse {
  referral_code: string;
  referral_link: string;
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
   * Verify email with token from email link
   */
  verifyEmail: async (token: string): Promise<EmailVerificationResponse> => {
    const response = await apiClient.post<EmailVerificationResponse>('/community/verify-email', { token });
    return response.data;
  },

  /**
   * Resend verification email to email address
   */
  resendVerificationEmail: async (email: string): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>('/community/resend-verification', undefined, {
      params: { email },
    });
    return response.data;
  },

  /**
   * Request password reset link
   */
  requestPasswordReset: async (email: string): Promise<PasswordResetResponse> => {
    const response = await apiClient.post<PasswordResetResponse>('/community/password-reset-request', { email });
    return response.data;
  },

  /**
   * Confirm password reset with token and new password
   */
  confirmPasswordReset: async (data: PasswordResetConfirmRequest): Promise<PasswordResetResponse> => {
    const response = await apiClient.post<PasswordResetResponse>('/community/password-reset-confirm', data);
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
};
