import * as React from 'react';
import { cn } from '../lib/cn';

/** Base white surface card — 1px border, 12px radius, 24px padding, card shadow. */
export function Card({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'rounded-card border border-line bg-bg-primary p-lg shadow-card',
        className,
      )}
      {...props}
    />
  );
}
