import * as React from 'react';
import { cn } from '../lib/cn';

export type NFTTier = 'common' | 'rare' | 'epic' | 'legendary';

export interface NFTVaultTileProps {
  name: string;
  imageUrl?: string;
  tier: NFTTier;
  dailyPP: number;
  onClick?: () => void;
  className?: string;
}

/** Tier ring styling (Chapter 3.6). */
const tierRing: Record<NFTTier, string> = {
  common: 'ring-2 ring-brand-cobalt',
  rare: 'ring-2 ring-brand-sky animate-pulse',
  epic: 'ring-2 ring-reward-gold shadow-glow',
  legendary: 'ring-2 ring-reward-gold animate-gold-pulse',
};

const tierLabel: Record<NFTTier, string> = {
  common: 'Common',
  rare: 'Rare',
  epic: 'Epic',
  legendary: 'Legendary',
};

/** NFT Vault Tile (Chapter 3.6): white card, image with tier ring, overlay
 * footer showing daily PP in bamboo gold over semi-transparent navy. */
export function NFTVaultTile({
  name,
  imageUrl,
  tier,
  dailyPP,
  onClick,
  className,
}: NFTVaultTileProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'group relative aspect-square w-full overflow-hidden rounded-card bg-bg-surface',
        tierRing[tier],
        className,
      )}
    >
      {imageUrl ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={imageUrl} alt={name} className="h-full w-full object-cover" />
      ) : (
        <div className="flex h-full w-full items-center justify-center text-4xl">🐼</div>
      )}
      <div className="absolute inset-x-0 bottom-0 flex items-center justify-between bg-bg-dark/80 px-md py-sm backdrop-blur-sm">
        <span className="truncate text-label text-ink-inverse">{name}</span>
        <span className="shrink-0 font-display text-label text-reward-gold">
          +{dailyPP} PP/day
        </span>
      </div>
      <span className="absolute right-sm top-sm rounded-pill bg-bg-primary/90 px-sm py-[2px] text-label font-medium text-brand-cobalt">
        {tierLabel[tier]}
      </span>
    </button>
  );
}
