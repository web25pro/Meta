import * as React from 'react';
import { cn } from '../lib/cn';
import { PandaMascot } from './PandaMascot';

export interface EmptyStateProps {
  title: string;
  description?: string;
  /** Custom icon; defaults to the panda mascot. */
  icon?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}

/** Empty state — panda mascot on ice-blue, title, description, optional CTA. */
export function EmptyState({
  title,
  description,
  icon,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-card border border-line bg-bg-primary px-lg py-3xl text-center',
        className,
      )}
    >
      {icon ?? <PandaMascot size={88} breathing={false} />}
      <h3 className="mt-lg font-display text-h2 text-ink-primary">{title}</h3>
      {description && (
        <p className="mt-sm max-w-sm text-body text-ink-muted">{description}</p>
      )}
      {action && <div className="mt-lg">{action}</div>}
    </div>
  );
}
