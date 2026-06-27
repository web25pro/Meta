'use client';

import { useState } from 'react';
import { Lock, Plus, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';
import {
  Card,
  Button,
  Input,
  Modal,
  Badge,
  PPAmount,
  ProgressBar,
  StatCard,
  cn,
} from '@meta-jungle/ui';

interface Stake {
  id: string;
  asset: string;
  amount: number;
  multiplier: string;
  lockDays: number;
  elapsedDays: number;
  accrued: number;
}

const STAKES: Stake[] = [
  { id: '1', asset: '5,000 PP', amount: 5000, multiplier: '1.5×', lockDays: 90, elapsedDays: 54, accrued: 420 },
  { id: '2', asset: 'LPanda #1188 (Epic)', amount: 0, multiplier: '2.0×', lockDays: 180, elapsedDays: 31, accrued: 180 },
];

const TIERS = [
  { days: 30, mult: '1.2×', apr: '8%' },
  { days: 90, mult: '1.5×', apr: '14%' },
  { days: 180, mult: '2.0×', apr: '22%' },
];

export default function StakingPage() {
  const [open, setOpen] = useState(false);
  const [tier, setTier] = useState(TIERS[1]);
  const totalStaked = STAKES.reduce((s, x) => s + x.amount, 0);
  const totalAccrued = STAKES.reduce((s, x) => s + x.accrued, 0);

  return (
    <div className="animate-page-in space-y-xl">
      <div className="flex flex-wrap items-start justify-between gap-md">
        <div>
          <h1 className="font-display text-h1 text-ink-primary">Staking</h1>
          <p className="mt-1 text-body text-ink-muted">
            Lock PP and NFTs to boost your earn multiplier and grow rewards.
          </p>
        </div>
        <Button onClick={() => setOpen(true)}>
          <Plus className="h-4 w-4" /> New Stake
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-lg lg:grid-cols-3">
        <StatCard icon={<Lock className="h-6 w-6" />} label="PP Staked" value={totalStaked} isPP />
        <StatCard icon={<TrendingUp className="h-6 w-6" />} label="Rewards Accrued" value={totalAccrued} isPP />
        <StatCard icon={<TrendingUp className="h-6 w-6" />} label="Active Stakes" value={STAKES.length} />
      </div>

      <div className="space-y-lg">
        <h2 className="font-display text-h2 text-ink-primary">Active stakes</h2>
        {STAKES.map((s) => {
          const pct = Math.round((s.elapsedDays / s.lockDays) * 100);
          return (
            <Card key={s.id} className="space-y-md border-l-4 border-l-brand-cobalt">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-display text-h2 text-ink-primary">{s.asset}</h3>
                  <p className="text-label text-ink-muted">{s.lockDays}-day lock</p>
                </div>
                <Badge tone="cobalt">{s.multiplier} earn</Badge>
              </div>
              <div className="space-y-1">
                <div className="flex justify-between text-label text-ink-muted">
                  <span>{s.elapsedDays} / {s.lockDays} days</span>
                  <span>Unlocks in {s.lockDays - s.elapsedDays} days</span>
                </div>
                <ProgressBar value={pct} tone="cobalt" />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-label text-ink-muted">Accrued rewards</span>
                <PPAmount value={s.accrued} size="sm" />
              </div>
              <div className="flex gap-sm">
                <Button variant="ghost" className="flex-1" onClick={() => toast.success('Rewards claimed')}>
                  Claim
                </Button>
                <Button variant="ghost" className="flex-1" onClick={() => toast('Early exit incurs a penalty', { icon: '⚠️' })}>
                  Unstake early
                </Button>
              </div>
            </Card>
          );
        })}
      </div>

      <Modal open={open} onClose={() => setOpen(false)} title="New stake">
        <div className="space-y-lg">
          <Input label="Amount (PP)" type="number" placeholder="5000" />
          <div>
            <p className="mb-sm text-label font-medium text-ink-primary">Lock duration</p>
            <div className="grid grid-cols-3 gap-sm">
              {TIERS.map((t) => (
                <button
                  key={t.days}
                  onClick={() => setTier(t)}
                  className={cn(
                    'rounded-card border px-sm py-md text-center transition-colors',
                    tier.days === t.days
                      ? 'border-brand-cobalt bg-brand-ice'
                      : 'border-line bg-bg-primary hover:bg-bg-elevated',
                  )}
                >
                  <div className="font-display text-h2 text-ink-primary">{t.days}d</div>
                  <div className="text-label text-reward-gold">{t.mult}</div>
                  <div className="text-label text-ink-muted">{t.apr} APR</div>
                </button>
              ))}
            </div>
          </div>
          <Button
            className="w-full"
            onClick={() => {
              setOpen(false);
              toast.success(`Staked with a ${tier.mult} multiplier for ${tier.days} days`);
            }}
          >
            Confirm Stake
          </Button>
        </div>
      </Modal>
    </div>
  );
}
