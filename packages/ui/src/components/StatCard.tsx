import * as React from 'react';
import { cn } from '../lib/cn';
import { CountUp } from './CountUp';

export interface StatCardProps {
  icon?: React.ReactNode;
  label: string;
  /** Numeric value. Rendered in bamboo gold when `isPP`. */
  value: number | string;
  /** True if the stat is a PP amount (drives bamboo-gold styling). */
  isPP?: boolean;
  /** Percentage change badge, e.g. +12.4 or -3.1. */
  change?: number;
  className?: string;
}

/**
 * Stat Card (Chapter 3.6): white card, 1px border, 12px radius, 24px padding.
 * Cobalt icon top-left, Display number, muted label, change badge bottom-right,
 * cobalt left-border accent on hover.
 */
export function StatCard({
  icon,
  label,
  value,
  isPP = false,
  change,
  className,
}: StatCardProps) {
  return (
    <div
      className={cn(
        'group relative overflow-hidden rounded-card border border-line bg-bg-primary p-lg shadow-card',
        'transition-all duration-200 hover:-translate-y-0.5 hover:border-line-blue hover:shadow-card-hover',
        'before:absolute before:left-0 before:top-0 before:h-full before:w-[4px] before:bg-brand-cobalt',
        'before:scale-y-0 before:transition-transform before:duration-200 hover:before:scale-y-100',
        className,
      )}
    >
      {icon && (
        <div className="mb-md inline-flex h-10 w-10 items-center justify-center rounded-[10px] bg-brand-ice text-brand-cobalt ring-1 ring-line-blue">
          {icon}
        </div>
      )}
      <div className="font-display leading-none text-ink-primary">
        {typeof value === 'number' ? (
          isPP ? (
            <CountUp
              value={value}
              className="text-display tabular-nums text-reward-gold"
            />
          ) : (
            <CountUp value={value} className="text-display tabular-nums" />
          )
        ) : (
          // Strings (e.g. "Legendary", "#5") use Heading-1 so long words don't overflow.
          <span className="block truncate text-h1">{value}</span>
        )}
      </div>
      <div className="mt-sm text-label uppercase tracking-wide text-ink-muted">
        {label}
      </div>
      {typeof change === 'number' && (
        <span
          className={cn(
            'absolute bottom-lg right-lg rounded-pill px-sm py-[2px] text-label font-medium',
            change >= 0
              ? 'bg-success/10 text-success'
              : 'bg-danger/10 text-danger',
          )}
        >
          {change >= 0 ? '+' : ''}
          {change}%
        </span>
      )}
    </div>
  );
}
