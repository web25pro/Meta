'use client';

import { useState } from 'react';
import { useQuery } from 'react-query';
import {
  LeaderboardRow,
  Skeleton,
  EmptyState,
  PPAmount,
  Foliage,
  cn,
} from '@meta-jungle/ui';
import apiClient from '@/lib/api';
import { LeaderboardResponse, LeaderboardEntry, UserType } from '@/types';

const TABS: { key: UserType; label: string }[] = [
  { key: UserType.TEAM_MEMBER, label: 'Team Members' },
  { key: UserType.AMBASSADOR, label: 'Ambassadors' },
];

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
    },
  );

  const entries = data?.entries ?? [];
  const podium = entries.slice(0, 3);
  const rest = entries.slice(3);

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Leaderboard</h1>
        <p className="mt-1 text-body text-ink-muted">
          See how you rank across the jungle.
        </p>
      </div>

      {/* Filter pills */}
      <div className="flex gap-sm">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={cn(
              'rounded-pill px-md py-sm text-label font-medium transition-colors',
              activeTab === tab.key
                ? 'bg-brand-cobalt text-ink-inverse'
                : 'border border-line bg-bg-primary text-ink-muted hover:bg-bg-elevated',
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-lg">
          <Skeleton className="h-44 w-full" />
          <Skeleton className="h-72 w-full" />
        </div>
      ) : entries.length === 0 ? (
        <EmptyState
          title="No rankings yet"
          description="Earn Panda Points to claim your spot on the podium."
        />
      ) : (
        <>
          {/* Podium — navy + bamboo texture */}
          {podium.length > 0 && (
            <div className="relative overflow-hidden rounded-card bg-hero-gradient p-xl">
              <div className="bamboo-texture pointer-events-none absolute inset-0 opacity-40" />
              <Foliage />
              <div className="relative flex items-end justify-center gap-md sm:gap-xl">
                {podium[1] && <PodiumSpot entry={podium[1]} place={2} />}
                {podium[0] && <PodiumSpot entry={podium[0]} place={1} />}
                {podium[2] && <PodiumSpot entry={podium[2]} place={3} />}
              </div>
            </div>
          )}

          {/* Rankings */}
          {rest.length > 0 && (
            <div className="overflow-hidden rounded-card border border-line bg-bg-primary shadow-card">
              {rest.map((entry) => (
                <LeaderboardRow
                  key={entry.user_id}
                  rank={entry.rank}
                  username={entry.user_name}
                  role={entry.user_type}
                  ppEarned={entry.total_pp}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function PodiumSpot({ entry, place }: { entry: LeaderboardEntry; place: 1 | 2 | 3 }) {
  const ring = {
    1: 'ring-reward-gold animate-gold-pulse',
    2: 'ring-[#94A3B8]',
    3: 'ring-[#CD7F32]',
  }[place];
  const size = place === 1 ? 'h-20 w-20' : 'h-16 w-16';

  return (
    <div className={cn('flex flex-col items-center', place === 1 && '-mt-lg')}>
      <div
        className={cn(
          'flex items-center justify-center rounded-full bg-brand-ice ring-4',
          ring,
          size,
        )}
      >
        <span className="font-display text-h2 text-brand-cobalt">
          {entry.user_name.slice(0, 2).toUpperCase()}
        </span>
      </div>
      <span className="mt-sm font-display text-h2 text-ink-inverse">#{place}</span>
      <span className="max-w-[7rem] truncate text-label text-brand-ice">
        {entry.user_name}
      </span>
      <PPAmount value={entry.total_pp} size="sm" className="mt-1" />
    </div>
  );
}
