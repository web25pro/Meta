import apiClient from '@/lib/api';
import { LeaderboardResponse, UserType } from '@/types';

export const leaderboardAPI = {
  getTeamMemberLeaderboard: async (page = 1, pageSize = 20): Promise<LeaderboardResponse> => {
    const response = await apiClient.get<LeaderboardResponse>('/leaderboard/team-members', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  getAmbassadorLeaderboard: async (page = 1, pageSize = 20): Promise<LeaderboardResponse> => {
    const response = await apiClient.get<LeaderboardResponse>('/leaderboard/ambassadors', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  getUserRank: async (userId: string): Promise<{ rank: number; total_pp: number }> => {
    const response = await apiClient.get(`/leaderboard/rank/${userId}`);
    return response.data;
  },
};
