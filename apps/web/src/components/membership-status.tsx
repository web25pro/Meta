'use client';

import { useQuery } from 'react-query';
import { Crown, Star, Shield, Zap, Lock, CheckCircle2, ArrowRight } from 'lucide-react';
import { cn, Card, Badge, Button, Skeleton } from '@meta-jungle/ui';
import { premiumAPI, MembershipStatus as MembershipStatusType } from '@/api/premium';

const TIER_ICONS: Record<string, typeof Crown> = {
  standard: Shield,
  panda_plus: Star,
  panda_pro: Crown,
  panda_elite: Zap,
};

const TIER_COLORS: Record<string, string> = {
  standard: 'neutral',
  panda_plus: 'cobalt',
  panda_pro: 'gold',
  panda_elite: 'jungle',
};

function UsageBar({ used, limit, unlimited, label }: {
  used: number;
  limit: number | null;
  unlimited: boolean;
  label: string;
}) {
  if (unlimited) {
    return (
      <div className="flex items-center justify-between text-body">
        <span className="text-ink-muted">{label}</span>
        <span className="font-medium text-reward-jungle">Unlimited</span>
      </div>
    );
  }
  const pct = limit ? Math.min(100, (used / limit) * 100) : 0;
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-body">
        <span className="text-ink-muted">{label}</span>
        <span className="font-medium text-ink-primary">{used} / {limit}</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-bg-elevated">
        <div
          className={cn(
            'h-full rounded-full transition-all',
            pct >= 90 ? 'bg-danger' : pct >= 70 ? 'bg-reward-amber' : 'bg-brand-cobalt',
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function MembershipStatusCard() {
  const { data: status, isLoading } = useQuery<MembershipStatusType>(
    'membershipStatus',
    () => premiumAPI.getStatus(),
    { staleTime: 60_000 },
  );

  if (isLoading) {
    return (
      <Card className="p-lg space-y-md">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
      </Card>
    );
  }

  if (!status) return null;

  const TierIcon = TIER_ICONS[status.tier] || Shield;
  const tierColor = TIER_COLORS[status.tier] || 'neutral';

  return (
    <Card className="p-lg space-y-md">
      {/* Tier header */}
      <div className="flex items-center gap-md">
        <div className={cn(
          'flex h-10 w-10 items-center justify-center rounded-full',
          status.tier === 'panda_elite' ? 'bg-reward-jungle/10' :
          status.tier === 'panda_pro' ? 'bg-reward-amber/10' :
          status.tier === 'panda_plus' ? 'bg-brand-cobalt/10' :
          'bg-bg-elevated',
        )}>
          <TierIcon className={cn(
            'h-5 w-5',
            status.tier === 'panda_elite' ? 'text-reward-jungle' :
            status.tier === 'panda_pro' ? 'text-reward-amber' :
            status.tier === 'panda_plus' ? 'text-brand-cobalt' :
            'text-ink-muted',
          )} />
        </div>
        <div>
          <h3 className="font-display text-h3 text-ink-primary">{status.tier_name}</h3>
          <p className="text-body text-ink-muted">
            {status.nft_count} LPanda NFT{status.nft_count !== 1 ? 's' : ''} detected
          </p>
        </div>
        <Badge tone={tierColor as any} className="ml-auto">
          {status.tier_name}
        </Badge>
      </div>

      {/* Usage */}
      <div className="space-y-sm">
        <UsageBar
          used={status.usage.quests_today.used}
          limit={status.usage.quests_today.limit}
          unlimited={status.usage.quests_today.unlimited}
          label="Quests Today"
        />
        <UsageBar
          used={status.usage.campaigns_this_month.used}
          limit={status.usage.campaigns_this_month.limit}
          unlimited={status.usage.campaigns_this_month.unlimited}
          label="Campaigns This Month"
        />
      </div>

      {/* PP Balance */}
      <div className="flex items-center justify-between rounded-card bg-bg-elevated p-md">
        <span className="text-body text-ink-muted">Panda Points</span>
        <span className="font-display text-h3 text-ink-primary">
          {status.available_points.toLocaleString()} PP
        </span>
      </div>

      {/* Next tier progress */}
      {status.next_tier && (
        <div className="space-y-sm rounded-card border border-line p-md">
          <div className="flex items-center gap-sm text-body">
            <ArrowRight className="h-4 w-4 text-brand-cobalt" />
            <span className="font-medium text-ink-primary">Next Level: {status.next_tier.name}</span>
          </div>
          <p className="text-body text-ink-muted">
            Hold {status.next_tier.nfts_needed} more LPanda NFT{status.next_tier.nfts_needed !== 1 ? 's' : ''} to unlock.
          </p>
          <div className="h-2 w-full overflow-hidden rounded-full bg-bg-elevated">
            <div
              className="h-full rounded-full bg-brand-cobalt"
              style={{
                width: `${Math.min(100, ((status.next_tier.nfts_required - status.next_tier.nfts_needed) / status.next_tier.nfts_required) * 100)}%`,
              }}
            />
          </div>
          <p className="text-caption text-ink-muted">
            {status.nft_count} / {status.next_tier.nfts_required} NFTs required
          </p>
        </div>
      )}

      {/* Benefits unlocked */}
      <div className="space-y-1">
        <p className="text-label text-ink-muted">Benefits Unlocked</p>
        <ul className="space-y-1">
          {status.permissions.daily_quest_limit !== null ? (
            <li className="flex items-center gap-sm text-body text-ink-primary">
              <CheckCircle2 className="h-4 w-4 text-reward-jungle" />
              Up to {status.permissions.daily_quest_limit} quests per day
            </li>
          ) : (
            <li className="flex items-center gap-sm text-body text-ink-primary">
              <CheckCircle2 className="h-4 w-4 text-reward-jungle" />
              Unlimited quests
            </li>
          )}
          {status.permissions.can_create_campaign && (
            <li className="flex items-center gap-sm text-body text-ink-primary">
              <CheckCircle2 className="h-4 w-4 text-reward-jungle" />
              Launch campaigns
            </li>
          )}
          {status.permissions.can_use_media && (
            <li className="flex items-center gap-sm text-body text-ink-primary">
              <CheckCircle2 className="h-4 w-4 text-reward-jungle" />
              Image & video campaigns
            </li>
          )}
          {status.permissions.can_create_video_contest && (
            <li className="flex items-center gap-sm text-body text-ink-primary">
              <CheckCircle2 className="h-4 w-4 text-reward-jungle" />
              Video contests
            </li>
          )}
          {status.permissions.can_create_bounty && (
            <li className="flex items-center gap-sm text-body text-ink-primary">
              <CheckCircle2 className="h-4 w-4 text-reward-jungle" />
              Bounties
            </li>
          )}
        </ul>
      </div>
    </Card>
  );
}
