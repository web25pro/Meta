import * as React from 'react';
import { cn } from '../lib/cn';

export type ToastKind = 'earn' | 'achievement' | 'info' | 'warning' | 'error';

export interface NotificationToastProps {
  kind?: ToastKind;
  message: string;
  ppAmount?: number;
  icon?: React.ReactNode;
  className?: string;
}

/** Left stripe color per kind (Chapter 3.6). */
const stripe: Record<ToastKind, string> = {
  earn: 'border-l-brand-cobalt',
  achievement: 'border-l-reward-gold',
  info: 'border-l-brand-sky',
  warning: 'border-l-reward-amber',
  error: 'border-l-danger',
};

/**
 * Notification Toast (Chapter 3.6): white card, bottom-anchored, 12px radius,
 * cobalt/gold/sky/amber/red left stripe, slide-up, auto-dismiss handled by host.
 */
export function NotificationToast({
  kind = 'info',
  message,
  ppAmount,
  icon,
  className,
}: NotificationToastProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-md rounded-card border border-line border-l-4 bg-bg-primary px-md py-sm shadow-card-hover',
        'animate-page-in',
        stripe[kind],
        className,
      )}
      role="status"
    >
      {icon && <span className="text-brand-cobalt">{icon}</span>}
      <span className="flex-1 text-body text-ink-primary">{message}</span>
      {typeof ppAmount === 'number' && (
        <span className="font-display text-body text-reward-gold">
          +{ppAmount.toLocaleString('en-US')} PP
        </span>
      )}
    </div>
  );
}
