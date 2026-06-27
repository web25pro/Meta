import * as React from 'react';
import { cn } from '../lib/cn';

/** Roles from the reputation system (Chapter 6.2). */
export type Role =
  | 'Explorer'
  | 'Tracker'
  | 'Hunter'
  | 'Whitelist'
  | 'OG Panda'
  | 'Alpha OG';

export interface RoleBadgeProps {
  role: Role;
  className?: string;
}

const roleStyle: Record<Role, string> = {
  Explorer: 'bg-bg-elevated text-ink-muted',
  Tracker: 'bg-brand-ice text-brand-cobalt',
  Hunter: 'bg-brand-sky/15 text-brand-sky',
  Whitelist: 'bg-brand-cobalt/15 text-brand-cobalt',
  'OG Panda': 'bg-reward-gold/15 text-reward-gold',
  'Alpha OG': 'bg-reward-gold text-ink-inverse',
};

export function RoleBadge({ role, className }: RoleBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-pill px-sm py-[2px] text-label font-medium',
        roleStyle[role],
        className,
      )}
    >
      {role}
    </span>
  );
}
