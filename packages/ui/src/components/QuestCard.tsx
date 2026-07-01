import * as React from 'react';
import { cn } from '../lib/cn';
import { PPAmount } from './PPAmount';

export interface QuestCardProps {
  title: string;
  description?: string;
  ppReward: number;
  brandLogo?: React.ReactNode;
  /** 0–100 completion progress. */
  progress?: number;
  status?: 'available' | 'in-progress' | 'completed';
  onClick?: () => void;
  className?: string;
}

const statusDot: Record<NonNullable<QuestCardProps['status']>, string> = {
  available: 'bg-line',
  'in-progress': 'bg-brand-sky',
  completed: 'bg-success',
};

/**
 * Quest Card (Chapter 3.6): white card, 4px cobalt left accent, brand logo +
 * title + description, bamboo-gold PP badge + status dot, sky-blue progress bar
 * on ice-blue track.
 */
export function QuestCard({
  title,
  description,
  ppReward,
  brandLogo,
  progress,
  status = 'available',
  onClick,
  className,
}: QuestCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'group w-full overflow-hidden rounded-card border border-line bg-bg-primary text-left shadow-card',
        'border-l-4 border-l-brand-cobalt transition-all hover:shadow-card-hover active:scale-[0.99]',
        className,
      )}
    >
      <div className="flex items-start gap-md p-lg">
        {brandLogo && (
          <div className="flex h-8 w-8 shrink-0 items-center justify-center overflow-hidden rounded-full bg-bg-elevated">
            {brandLogo}
          </div>
        )}
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-md">
            <h3 className="text-h2 text-ink-primary">{title}</h3>
            <div className="flex shrink-0 items-center gap-sm">
              <PPAmount value={ppReward} size="sm" />
              <span className={cn('h-2 w-2 rounded-full', statusDot[status])} />
            </div>
          </div>
          {description && (
            <p className="mt-1 text-body text-ink-muted line-clamp-2">{description}</p>
          )}
          {typeof progress === 'number' && (
            <div className="mt-md h-2 w-full overflow-hidden rounded-pill bg-brand-ice">
              <div
                className="h-full rounded-pill bg-brand-sky transition-all"
                style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
              />
            </div>
          )}
        </div>
      </div>
    </button>
  );
}
