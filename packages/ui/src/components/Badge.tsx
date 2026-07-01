import * as React from 'react';
import { cn } from '../lib/cn';

type Tone = 'neutral' | 'cobalt' | 'sky' | 'gold' | 'success' | 'danger' | 'amber' | 'jungle';

export interface BadgeProps {
  tone?: Tone;
  children: React.ReactNode;
  className?: string;
}

const tones: Record<Tone, string> = {
  neutral: 'bg-bg-elevated text-ink-muted',
  cobalt: 'bg-brand-cobalt/15 text-brand-cobalt',
  sky: 'bg-brand-sky/15 text-brand-sky',
  gold: 'bg-reward-gold/15 text-reward-gold',
  success: 'bg-success/10 text-success',
  danger: 'bg-danger/10 text-danger',
  amber: 'bg-reward-amber/15 text-reward-amber',
  jungle: 'bg-forest-500/15 text-forest-700',
};

export function Badge({ tone = 'neutral', children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-pill px-sm py-[2px] text-label font-medium',
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
