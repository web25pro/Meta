import * as React from 'react';
import { cn } from '../lib/cn';

/**
 * Loading skeleton — ice-blue base with sky-blue shimmer pass.
 * Never use spinners (Chapter 3.7).
 */
export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'rounded-card bg-brand-ice animate-shimmer',
        'bg-[linear-gradient(90deg,#DBEAFE_0%,#EFF6FF_20%,#3B82F6/20_40%,#DBEAFE_60%)]',
        'bg-[length:200%_100%]',
        className,
      )}
    />
  );
}
