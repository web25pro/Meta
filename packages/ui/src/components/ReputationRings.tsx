import * as React from 'react';
import { cn } from '../lib/cn';

export interface ReputationRingsProps {
  /** Activity Score 0–1000 — outer ring, sky blue. */
  activity: number;
  /** Reputation Score 0–1000 — middle ring, cobalt. */
  reputation: number;
  /** Influence Score 0–1000 — inner ring, bamboo gold. */
  influence: number;
  size?: number;
  /** Optional avatar to render inside the rings. */
  avatarUrl?: string;
  className?: string;
}

const MAX = 1000;

function Ring({
  radius,
  value,
  color,
  size,
}: {
  radius: number;
  value: number;
  color: string;
  size: number;
}) {
  const circumference = 2 * Math.PI * radius;
  const pct = Math.min(1, Math.max(0, value / MAX));
  const c = size / 2;
  return (
    <>
      <circle cx={c} cy={c} r={radius} fill="none" stroke="#DBEAFE" strokeWidth={6} />
      <circle
        cx={c}
        cy={c}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={6}
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={circumference * (1 - pct)}
        transform={`rotate(-90 ${c} ${c})`}
        style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.16,1,0.3,1)' }}
      />
    </>
  );
}

/**
 * Reputation Rings (Chapter 3.6 / Chapter 6): three concentric arcs around a
 * circular avatar — Activity (sky, outer), Reputation (cobalt, middle),
 * Influence (bamboo gold, inner). Each animates from 0 to value on mount.
 */
export function ReputationRings({
  activity,
  reputation,
  influence,
  size = 96,
  avatarUrl,
  className,
}: ReputationRingsProps) {
  const c = size / 2;
  const avatarSize = size * 0.58;
  return (
    <div className={cn('relative inline-block', className)} style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <Ring radius={c - 6} value={activity} color="#3B82F6" size={size} />
        <Ring radius={c - 16} value={reputation} color="#1E5FA8" size={size} />
        <Ring radius={c - 26} value={influence} color="#B8860B" size={size} />
      </svg>
      <div
        className="absolute overflow-hidden rounded-full bg-brand-ice"
        style={{
          width: avatarSize,
          height: avatarSize,
          left: c - avatarSize / 2,
          top: c - avatarSize / 2,
        }}
      >
        {avatarUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={avatarUrl} alt="avatar" className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-xl">🐼</div>
        )}
      </div>
    </div>
  );
}
