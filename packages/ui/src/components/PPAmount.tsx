import * as React from 'react';
import { cn } from '../lib/cn';

export interface PPAmountProps {
  /** Raw Panda Points value. */
  value: number;
  /** Display size. `display` = the largest element on screen (Chapter 3.1). */
  size?: 'sm' | 'md' | 'lg' | 'display';
  showUnit?: boolean;
  /** Sign prefix for ledger deltas. */
  signed?: boolean;
  className?: string;
}

const sizeMap = {
  sm: 'text-label',
  md: 'text-h2',
  lg: 'text-h1',
  display: 'text-display',
};

/**
 * Panda Points amount — ALWAYS bamboo gold, ALWAYS display/mono-weighted.
 * Bamboo gold is reserved exclusively for PP / rewards / premium (Chapter 3.2).
 */
export function PPAmount({
  value,
  size = 'md',
  showUnit = true,
  signed = false,
  className,
}: PPAmountProps) {
  const sign = signed ? (value >= 0 ? '+' : '') : '';
  return (
    <span
      className={cn(
        'font-display tabular-nums text-reward-gold',
        sizeMap[size],
        className,
      )}
    >
      {sign}
      {value.toLocaleString('en-US')}
      {showUnit && <span className="ml-1 text-[0.5em] font-sans align-top">PP</span>}
    </span>
  );
}
