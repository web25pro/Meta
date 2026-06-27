import * as React from 'react';
import { cn } from '../lib/cn';

export interface WalletBalanceCardProps {
  ppBalance: number;
  lpandaBalance?: number;
  usdcBalance?: number;
  /** Action pills: Send · Receive · Swap · Stake. */
  actions?: { label: string; icon?: React.ReactNode; onClick?: () => void }[];
  className?: string;
}

/**
 * Panda Wallet Balance Card (Chapter 3.6 / 4.5): full-bleed panda-navy card with
 * diagonal bamboo texture overlay, PP balance in Display 64px bamboo gold,
 * LPanda + USDC in white, four white action pills with cobalt icons.
 */
export function WalletBalanceCard({
  ppBalance,
  lpandaBalance = 0,
  usdcBalance = 0,
  actions,
  className,
}: WalletBalanceCardProps) {
  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-card bg-bg-dark p-lg text-ink-inverse',
        className,
      )}
    >
      {/* bamboo texture overlay @ 8% */}
      <div className="pointer-events-none absolute inset-0 bg-bamboo opacity-30" />
      <div className="relative">
        <div className="text-label text-brand-ice">Panda Wallet</div>
        <div className="mt-sm font-display text-display-lg leading-none text-reward-gold">
          {ppBalance.toLocaleString('en-US')}
          <span className="ml-2 align-top text-h2 font-sans text-reward-gold/80">PP</span>
        </div>
        <div className="mt-md flex gap-lg text-h2">
          <span>{lpandaBalance.toLocaleString('en-US')} <span className="text-label text-brand-ice">LPANDA</span></span>
          <span>{usdcBalance.toLocaleString('en-US')} <span className="text-label text-brand-ice">USDC</span></span>
        </div>

        {actions && actions.length > 0 && (
          <div className="mt-lg flex flex-wrap gap-sm">
            {actions.map((a) => (
              <button
                key={a.label}
                onClick={a.onClick}
                className="inline-flex items-center gap-sm rounded-pill bg-bg-primary px-md py-sm text-label font-medium text-ink-primary transition-transform active:scale-[0.97]"
              >
                {a.icon && <span className="text-brand-cobalt">{a.icon}</span>}
                {a.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
