import * as React from 'react';
import { cn } from '../lib/cn';
import { PPAmount } from './PPAmount';

export interface LeaderboardRowProps {
  rank: number;
  username: string;
  role?: string;
  ppEarned: number;
  avatarUrl?: string;
  /** Positive = moved up (sky), negative = down (red). */
  rankChange?: number;
  isCurrentUser?: boolean;
  className?: string;
}

/** Rank color: gold #1st, silver #2nd, bronze #3rd, cobalt for the rest. */
function rankColor(rank: number): string {
  if (rank === 1) return 'text-reward-gold';
  if (rank === 2) return 'text-[#94A3B8]';
  if (rank === 3) return 'text-[#CD7F32]';
  return 'text-brand-cobalt';
}

/** Leaderboard Row (Chapter 3.6). Top 3 get a subtle cobalt→ice gradient. */
export function LeaderboardRow({
  rank,
  username,
  role,
  ppEarned,
  avatarUrl,
  rankChange,
  isCurrentUser,
  className,
}: LeaderboardRowProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-md border-b border-line px-md py-sm transition-colors',
        rank <= 3 && 'bg-gradient-to-r from-brand-ice/60 to-transparent',
        isCurrentUser && 'border-l-4 border-l-brand-cobalt bg-bg-elevated',
        className,
      )}
    >
      <div className={cn('w-10 shrink-0 text-center font-display text-h2', rankColor(rank))}>
        {rank}
      </div>
      <div className="h-9 w-9 shrink-0 overflow-hidden rounded-full ring-2 ring-bg-primary shadow-card">
        {avatarUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={avatarUrl} alt={username} className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-brand-ice text-label text-brand-cobalt">
            {username.slice(0, 2).toUpperCase()}
          </div>
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div className="truncate font-medium text-ink-primary">{username}</div>
        {role && (
          <span className="text-label text-brand-cobalt">{role}</span>
        )}
      </div>
      {typeof rankChange === 'number' && rankChange !== 0 && (
        <span
          className={cn(
            'text-label font-medium',
            rankChange > 0 ? 'text-brand-sky' : 'text-danger',
          )}
        >
          {rankChange > 0 ? '▲' : '▼'} {Math.abs(rankChange)}
        </span>
      )}
      <PPAmount value={ppEarned} size="sm" className="shrink-0" />
    </div>
  );
}
