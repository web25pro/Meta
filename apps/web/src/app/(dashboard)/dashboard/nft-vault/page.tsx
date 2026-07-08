'use client';

import { useState } from 'react';
import { useQuery } from 'react-query';
import { toast } from 'sonner';
import { metajungleAPI } from '@/api/metajungle';
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

const TIER_TONE: Record<NFTTier, 'cobalt' | 'sky' | 'gold'> = {
  common: 'cobalt', rare: 'sky', epic: 'gold', legendary: 'gold',
};

const TIER_RANK: NFTTier[] = ['common', 'rare', 'epic', 'legendary'];
function topTier(nfts: { tier: NFTTier }[]): string {
  if (!nfts.length) return '—';
  const best = nfts.reduce((b, n) => Math.max(b, TIER_RANK.indexOf(n.tier)), 0);
  const label = TIER_RANK[best];
  return label.charAt(0).toUpperCase() + label.slice(1);
}

export default function NFTVaultPage() {
  const [selected, setSelected] = useState<VaultNFT | null>(null);

  // Live holdings from the backend.
  const { data, isLoading } = useQuery('mjNfts', metajungleAPI.listNFTs, { retry: false });
  const nfts: VaultNFT[] = data
    ? data.nfts.map((n) => ({
        id: n.id,
        name: n.name,
        tier: n.tier,
        dailyPP: n.daily_pp_rate,
        collection: 'LPanda Genesis',
        traits: n.traits ?? [],
        utilities: n.utilities ?? [],
      }))
    : [];
  const totalDaily = nfts.reduce((s, n) => s + n.dailyPP, 0);

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">NFT Vault</h1>
        <p className="mt-1 text-body text-ink-muted">
          Your LPanda NFTs and the utilities they unlock.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-lg lg:grid-cols-3">
        <StatCard icon={<Sparkles className="h-6 w-6" />} label="NFTs Held" value={nfts.length} />
        <StatCard icon={<Sparkles className="h-6 w-6" />} label="Daily PP Yield" value={totalDaily} isPP />
        <StatCard icon={<Sparkles className="h-6 w-6" />} label="Top Tier" value={topTier(nfts)} />
      </div>

      {isLoading ? (
        <div className="grid grid-cols-2 gap-lg sm:grid-cols-3 lg:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-48 animate-pulse rounded-card bg-bg-elevated" />
          ))}
        </div>
      ) : nfts.length === 0 ? (
        <div className="rounded-card border border-line bg-bg-primary p-xl text-center text-ink-muted">
          No NFTs in your vault yet. Mint or acquire an LPanda NFT to get started!
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-lg sm:grid-cols-3 lg:grid-cols-4">
          {nfts.map((n) => (
            <NFTVaultTile
              key={n.id}
              name={n.name}
              tier={n.tier}
              dailyPP={n.dailyPP}
              onClick={() => setSelected(n)}
            />
          ))}
        </div>
      )}

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
