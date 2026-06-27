'use client';

import { useState } from 'react';
import { useQuery } from 'react-query';
import { Trophy, Medal, Award } from 'lucide-react';
import apiClient from '@/lib/api';
import { LeaderboardResponse, UserType } from '@/types';

export default function LeaderboardPage() {
  const [activeTab, setActiveTab] = useState<UserType>(UserType.TEAM_MEMBER);

  const { data, isLoading } = useQuery<LeaderboardResponse>(
    ['leaderboard', activeTab],
    async () => {
      const endpoint =
        activeTab === UserType.TEAM_MEMBER
          ? '/leaderboard/team-members'
          : '/leaderboard/ambassadors';
      const response = await apiClient.get(endpoint);
      return {
        entries: response.data.entries || [],
        total: response.data.total || 0,
        page: response.data.page || 1,
        page_size: response.data.page_size || 20,
      };
    }
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Leaderboard</h1>
        <p className="text-gray-600 mt-1">See how you rank against others</p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-4 border-b border-gray-200">
        <button
          onClick={() => setActiveTab(UserType.TEAM_MEMBER)}
          className={`pb-4 px-4 font-medium transition-colors ${
            activeTab === UserType.TEAM_MEMBER
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Team Members
        </button>
        <button
          onClick={() => setActiveTab(UserType.AMBASSADOR)}
          className={`pb-4 px-4 font-medium transition-colors ${
            activeTab === UserType.AMBASSADOR
              ? 'text-primary-600 border-b-2 border-primary-600'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Ambassadors
        </button>
      </div>

      {/* Leaderboard */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {data?.entries.map((entry, index) => (
              <div
                key={entry.user_id}
                className="flex items-center justify-between p-6 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center space-x-4">
                  <div className="flex-shrink-0 w-12 text-center">
                    {entry.rank === 1 && <Trophy className="h-8 w-8 text-yellow-500 mx-auto" />}
                    {entry.rank === 2 && <Medal className="h-8 w-8 text-gray-400 mx-auto" />}
                    {entry.rank === 3 && <Award className="h-8 w-8 text-orange-600 mx-auto" />}
                    {entry.rank > 3 && (
                      <span className="text-2xl font-bold text-gray-400">#{entry.rank}</span>
                    )}
                  </div>
                  <div>
                    <div className="font-semibold text-gray-900">{entry.user_name}</div>
                    <div className="text-sm text-gray-600">{entry.user_type}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-primary-600">{entry.total_pp}</div>
                  <div className="text-sm text-gray-600">Panda Points</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
