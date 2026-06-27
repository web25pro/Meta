import * as React from 'react';
import { cn } from '../lib/cn';

export interface ProgressBarProps {
  /** 0–100. */
  value: number;
  tone?: 'sky' | 'cobalt' | 'gold';
  className?: string;
}

const tones = {
  sky: 'bg-brand-sky',
  cobalt: 'bg-brand-cobalt',
  gold: 'bg-reward-gold',
};

/** Sky-blue progress on an ice-blue track (Chapter 3.6). */
export function ProgressBar({ value, tone = 'sky', className }: ProgressBarProps) {
  return (
    <div className={cn('h-2 w-full overflow-hidden rounded-pill bg-brand-ice', className)}>
      <div
        className={cn('h-full rounded-pill transition-all duration-700', tones[tone])}
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  );
}
