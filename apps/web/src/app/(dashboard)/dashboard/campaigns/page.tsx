'use client';

import { useQuery, useQueryClient } from 'react-query';
import { toast } from 'sonner';
import { Clock, Users } from 'lucide-react';
import {
  Card,
  Button,
  Badge,
  PPAmount,
  ProgressBar,
  Foliage,
  cn,
} from '@meta-jungle/ui';
import { metajungleAPI, type ApiCampaign } from '@/api/metajungle';

interface Campaign {
  id: string;
  brand: string;
  title: string;
  blurb: string;
  pool: number;
  perTask: number;
  daysLeft: number;
  participants: number;
  filled: number; // %
  regions: string[];
  featured?: boolean;
}

const CAMPAIGNS: Campaign[] = [
  { id: '1', brand: 'Aerodrome', title: 'Provide liquidity & earn', blurb: 'Add liquidity to the LPANDA/USDC pool and verify on-chain.', pool: 500000, perTask: 500, daysLeft: 6, participants: 1240, filled: 62, regions: ['Global'], featured: true },
  { id: '2', brand: 'Jumia', title: 'Shop & review challenge', blurb: 'Make a verified purchase and leave a review to earn PP.', pool: 120000, perTask: 200, daysLeft: 12, participants: 880, filled: 41, regions: ['NG', 'GH', 'KE'] },
  { id: '3', brand: 'Base', title: 'Bridge to Base quest', blurb: 'Bridge any asset to Base and complete a swap.', pool: 250000, perTask: 350, daysLeft: 3, participants: 2010, filled: 88, regions: ['Global'] },
  { id: '4', brand: 'Duolingo', title: 'Learn a language streak', blurb: 'Hit a 7-day streak in any course to claim the reward.', pool: 80000, perTask: 150, daysLeft: 20, participants: 540, filled: 23, regions: ['Global'] },
];

function fromApi(c: ApiCampaign): Campaign {
  const daysLeft = c.ends_at
    ? Math.max(0, Math.ceil((new Date(c.ends_at).getTime() - Date.now()) / 86400000))
    : 0;
  return {
    id: c.id,
    brand: c.brand || 'Partner',
    title: c.title,
    blurb: c.blurb,
    pool: c.pp_budget,
    perTask: c.pp_per_task,
    daysLeft,
    participants: c.total_participants,
    filled: c.pp_budget > 0 ? Math.round((c.pp_claimed / c.pp_budget) * 100) : 0,
    regions: ['Global'],
    featured: c.featured,
  };
}

export default function CampaignsPage() {
  const queryClient = useQueryClient();
  const { data } = useQuery('mjCampaigns', metajungleAPI.listCampaigns, { retry: false });
  const all: Campaign[] = data && data.length > 0 ? data.map(fromApi) : CAMPAIGNS;
  const featured = all.find((c) => c.featured);
  const rest = all.filter((c) => !c.featured);

  const join = async (c: Campaign) => {
    try {
      await metajungleAPI.joinCampaign(c.id);
      toast.success(`Joined ${c.brand} campaign`);
      queryClient.invalidateQueries('mjCampaigns');
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || `Could not join ${c.brand}`);
    }
  };

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Campaigns</h1>
        <p className="mt-1 text-body text-ink-muted">
          Brand-sponsored campaigns with big Panda Point pools.
        </p>
      </div>

      {/* Featured spotlight — navy gradient */}
      {featured && (
        <div className="relative overflow-hidden rounded-card bg-hero-gradient p-xl text-ink-inverse">
          <div className="bamboo-texture pointer-events-none absolute inset-0 opacity-40" />
          <Foliage />
          <div className="relative space-y-md">
            <div className="flex items-center gap-sm">
              <span className="rounded-pill bg-white/15 px-sm py-[2px] text-label">{featured.brand}</span>
              <Badge tone="gold">Featured</Badge>
            </div>
            <h2 className="font-display text-h1">{featured.title}</h2>
            <p className="max-w-lg text-brand-ice">{featured.blurb}</p>
            <div className="flex flex-wrap items-center gap-lg pt-sm">
              <div>
                <p className="text-label text-brand-ice">Reward pool</p>
                <p className="font-display text-h1 text-reward-gold">
                  {featured.pool.toLocaleString('en-US')}<span className="ml-1 text-label">PP</span>
                </p>
              </div>
              <div>
                <p className="text-label text-brand-ice">Per task</p>
                <p className="font-display text-h2">{featured.perTask} PP</p>
              </div>
              <div className="flex items-center gap-sm text-label text-brand-ice">
                <Clock className="h-4 w-4" /> {featured.daysLeft} days left
              </div>
            </div>
            <Button variant="gold" onClick={() => join(featured)}>
              Join Campaign
            </Button>
          </div>
        </div>
      )}

      <div className="grid gap-lg sm:grid-cols-2">
        {rest.map((c) => (
          <Card key={c.id} className="flex flex-col gap-md">
            <div className="flex items-center justify-between">
              <span className="font-display text-h2 text-ink-primary">{c.brand}</span>
              <Badge tone={c.daysLeft <= 3 ? 'amber' : 'cobalt'}>
                <Clock className="h-3 w-3" /> {c.daysLeft}d left
              </Badge>
            </div>
            <div>
              <h3 className="text-body font-medium text-ink-primary">{c.title}</h3>
              <p className="text-label text-ink-muted">{c.blurb}</p>
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-label text-ink-muted">
                <span>Pool {c.filled}% claimed</span>
                <span className="flex items-center gap-1"><Users className="h-3 w-3" /> {c.participants.toLocaleString('en-US')}</span>
              </div>
              <ProgressBar value={c.filled} tone={c.filled > 80 ? 'gold' : 'jungle'} />
            </div>
            <div className="mt-auto flex items-center justify-between">
              <PPAmount value={c.perTask} size="sm" />
              <Button size="sm" onClick={() => join(c)}>Join</Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
