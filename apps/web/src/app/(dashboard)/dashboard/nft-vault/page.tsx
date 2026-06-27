'use client';

import { useState } from 'react';
import { toast } from 'sonner';
import {
  NFTVaultTile,
  Modal,
  Button,
  Badge,
  PPAmount,
  StatCard,
  cn,
  type NFTTier,
} from '@meta-jungle/ui';
import { Sparkles, Send } from 'lucide-react';

interface VaultNFT {
  id: string;
  name: string;
  tier: NFTTier;
  dailyPP: number;
  collection: string;
  traits: { label: string; value: string }[];
  utilities: string[];
}

const NFTS: VaultNFT[] = [
  {
    id: '1', name: 'LPanda #0421', tier: 'legendary', dailyPP: 60, collection: 'LPanda Genesis',
    traits: [
      { label: 'Fur', value: 'Arctic White' }, { label: 'Eyes', value: 'Cobalt Glow' },
      { label: 'Background', value: 'Midnight Jungle' }, { label: 'Accessory', value: 'Bamboo Crown' },
    ],
    utilities: ['2× earn multiplier', 'DAO vote weight ×3', 'Partner mint WL', 'Revenue share'],
  },
  {
    id: '2', name: 'LPanda #1188', tier: 'epic', dailyPP: 40, collection: 'LPanda Genesis',
    traits: [
      { label: 'Fur', value: 'Snow' }, { label: 'Eyes', value: 'Sky' },
      { label: 'Background', value: 'Bamboo Grove' }, { label: 'Accessory', value: 'Explorer Scarf' },
    ],
    utilities: ['1.5× earn multiplier', 'DAO vote', 'Partner mint WL'],
  },
  {
    id: '3', name: 'LPanda #2390', tier: 'rare', dailyPP: 30, collection: 'LPanda Genesis',
    traits: [
      { label: 'Fur', value: 'Ivory' }, { label: 'Eyes', value: 'Calm' },
      { label: 'Background', value: 'Dawn Mist' }, { label: 'Accessory', value: 'None' },
    ],
    utilities: ['1.2× earn multiplier', 'P2P basic'],
  },
  {
    id: '4', name: 'LPanda #4501', tier: 'common', dailyPP: 20, collection: 'LPanda Genesis',
    traits: [
      { label: 'Fur', value: 'White' }, { label: 'Eyes', value: 'Round' },
      { label: 'Background', value: 'Forest' }, { label: 'Accessory', value: 'None' },
    ],
    utilities: ['Daily PP earn', 'Holder badge'],
  },
];

const TIER_TONE: Record<NFTTier, 'cobalt' | 'sky' | 'gold'> = {
  common: 'cobalt', rare: 'sky', epic: 'gold', legendary: 'gold',
};

export default function NFTVaultPage() {
  const [selected, setSelected] = useState<VaultNFT | null>(null);
  const totalDaily = NFTS.reduce((s, n) => s + n.dailyPP, 0);

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">NFT Vault</h1>
        <p className="mt-1 text-body text-ink-muted">
          Your LPanda NFTs and the utilities they unlock.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-lg lg:grid-cols-3">
        <StatCard icon={<Sparkles className="h-6 w-6" />} label="NFTs Held" value={NFTS.length} />
        <StatCard icon={<Sparkles className="h-6 w-6" />} label="Daily PP Yield" value={totalDaily} isPP />
        <StatCard icon={<Sparkles className="h-6 w-6" />} label="Top Tier" value="Legendary" />
      </div>

      <div className="grid grid-cols-2 gap-lg sm:grid-cols-3 lg:grid-cols-4">
        {NFTS.map((n) => (
          <NFTVaultTile
            key={n.id}
            name={n.name}
            tier={n.tier}
            dailyPP={n.dailyPP}
            onClick={() => setSelected(n)}
          />
        ))}
      </div>

      <Modal open={!!selected} onClose={() => setSelected(null)} title={selected?.name}>
        {selected && (
          <div className="space-y-lg">
            <div
              className={cn(
                'flex aspect-video items-center justify-center rounded-card bg-bg-dark text-6xl',
                selected.tier === 'legendary' && 'animate-gold-pulse',
              )}
            >
              🐼
            </div>
            <div className="flex items-center justify-between">
              <span className="text-label text-ink-muted">{selected.collection}</span>
              <Badge tone={TIER_TONE[selected.tier]} className="capitalize">{selected.tier}</Badge>
            </div>

            <div>
              <p className="mb-sm text-label font-medium text-ink-primary">Traits</p>
              <div className="grid grid-cols-2 gap-sm">
                {selected.traits.map((t, i) => (
                  <div key={t.label} className={cn('rounded-card px-md py-sm', i % 2 ? 'bg-bg-primary' : 'bg-bg-elevated')}>
                    <p className="text-label text-ink-muted">{t.label}</p>
                    <p className="text-body text-ink-primary">{t.value}</p>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <p className="mb-sm text-label font-medium text-ink-primary">Utilities unlocked</p>
              <div className="flex flex-wrap gap-sm">
                {selected.utilities.map((u) => (
                  <Badge key={u} tone="cobalt">{u}</Badge>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-between rounded-card bg-bg-surface px-md py-sm">
              <span className="text-label text-ink-muted">Daily yield</span>
              <PPAmount value={selected.dailyPP} size="sm" />
            </div>

            <div className="flex gap-sm">
              <Button variant="ghost" className="flex-1" onClick={() => toast.success('Listing flow coming soon')}>
                List for Sale
              </Button>
              <Button className="flex-1" onClick={() => toast.success('Transfer flow coming soon')}>
                <Send className="h-4 w-4" /> Transfer
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
