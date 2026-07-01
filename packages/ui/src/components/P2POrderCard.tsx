import * as React from 'react';
import { cn } from '../lib/cn';
import { PPAmount } from './PPAmount';

export interface P2POrderCardProps {
  trader: string;
  verified?: boolean;
  reputation?: number; // 0–5 stars
  ppAmount: number;
  price: string; // formatted, e.g. "₦18,500"
  paymentMethods?: string[];
  postedAgo?: string;
  escrowActive?: boolean;
  onTrade?: () => void;
  className?: string;
}

/**
 * P2P Order Card (Chapter 3.6): white card, 4px cobalt left border, trader +
 * verified checkmark, reputation stars, PP in bamboo gold, price in navy,
 * payment methods, escrow lock when active, cobalt "Trade" CTA.
 */
export function P2POrderCard({
  trader,
  verified,
  reputation = 0,
  ppAmount,
  price,
  paymentMethods = [],
  postedAgo,
  escrowActive,
  onTrade,
  className,
}: P2POrderCardProps) {
  return (
    <div
      className={cn(
        'rounded-card border border-line border-l-4 border-l-brand-cobalt bg-bg-primary p-lg shadow-card',
        className,
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-sm">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-ice text-label text-brand-cobalt">
            {trader.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-1 font-medium text-ink-primary">
              {trader}
              {verified && <span className="text-brand-cobalt" title="Verified">✓</span>}
            </div>
            <div className="text-label text-reward-gold">
              {'★'.repeat(Math.round(reputation))}
              <span className="text-line">{'★'.repeat(5 - Math.round(reputation))}</span>
            </div>
          </div>
        </div>
        {escrowActive && <span className="text-brand-cobalt" title="Escrow active">🔒</span>}
      </div>

      <div className="mt-md flex items-end justify-between">
        <PPAmount value={ppAmount} size="md" />
        <span className="font-display text-h2 text-ink-primary">{price}</span>
      </div>

      <div className="mt-sm flex items-center justify-between">
        <div className="flex gap-1 text-label text-ink-muted">
          {paymentMethods.map((m) => (
            <span key={m} className="rounded-pill bg-bg-elevated px-sm py-[2px]">{m}</span>
          ))}
        </div>
        {postedAgo && <span className="text-label text-ink-muted">{postedAgo}</span>}
      </div>

      <button
        onClick={onTrade}
        className="mt-md w-full rounded-pill bg-brand-cobalt py-sm text-body font-medium text-ink-inverse transition-transform active:scale-[0.98]"
      >
        Trade
      </button>
    </div>
  );
}
