'use client';

import { useQuery } from 'react-query';
import {
  Users, Wallet, ShoppingBag, Megaphone, Target, CheckCircle, Image as ImageIcon, Ban,
} from 'lucide-react';
import { StatCard, Skeleton, Card } from '@meta-jungle/ui';
import { adminAPI } from '@/api/admin';

export default function AdminOverviewPage() {
  const { data, isLoading } = useQuery('adminOverview', adminAPI.overview, { retry: false });

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Overview</h1>
        <p className="mt-1 text-body text-ink-muted">Ecosystem health at a glance.</p>
      </div>

      {isLoading || !data ? (
        <div className="grid grid-cols-2 gap-lg lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-32" />)}
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-lg lg:grid-cols-4">
            <StatCard icon={<Users className="h-5 w-5" />} label="Total Users" value={data.total_users} />
            <StatCard icon={<Wallet className="h-5 w-5" />} label="PP Issued" value={Math.round(data.pp_issued)} isPP />
            <StatCard icon={<ShoppingBag className="h-5 w-5" />} label="PP Spent" value={Math.round(data.pp_spent)} isPP />
            <StatCard icon={<Megaphone className="h-5 w-5" />} label="Active Campaigns" value={data.active_campaigns} />
            <StatCard icon={<Target className="h-5 w-5" />} label="Quests" value={data.quests} />
            <StatCard icon={<CheckCircle className="h-5 w-5" />} label="Completions" value={data.quest_completions} />
            <StatCard icon={<ImageIcon className="h-5 w-5" />} label="NFTs Held" value={data.nfts_held} />
            <StatCard icon={<Ban className="h-5 w-5" />} label="Banned Users" value={data.banned_users} />
          </div>

          <Card>
            <h2 className="font-display text-h2 text-ink-primary">Economy</h2>
            <div className="mt-md grid gap-md sm:grid-cols-3">
              <Metric label="PP issued" value={Math.round(data.pp_issued).toLocaleString()} tone="text-forest-600" />
              <Metric label="PP spent" value={Math.round(data.pp_spent).toLocaleString()} tone="text-reward-gold" />
              <Metric label="Net in circulation" value={Math.round(data.pp_issued - data.pp_spent).toLocaleString()} tone="text-brand-cobalt" />
            </div>
          </Card>
        </>
      )}
    </div>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <div className="rounded-card bg-bg-surface px-lg py-md">
      <div className={`font-display text-h1 ${tone}`}>{value}</div>
      <div className="text-label text-ink-muted">{label}</div>
    </div>
  );
}
