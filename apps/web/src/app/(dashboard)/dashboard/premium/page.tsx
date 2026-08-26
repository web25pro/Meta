'use client';

import { useQuery } from 'react-query';
import Link from 'next/link';
import {
  Crown,
  Star,
  Shield,
  Zap,
  CheckCircle2,
  X,
  ExternalLink,
  ArrowRight,
} from 'lucide-react';
import { cn, Card, Button, Badge, Skeleton } from '@meta-jungle/ui';
import { premiumAPI, TierInfo, MembershipStatus } from '@/api/premium';
import { ConnectWalletButton } from '@/components/connect-wallet-button';
import { MembershipStatusCard } from '@/components/membership-status';

const TIER_ORDER = ['standard', 'panda_plus', 'panda_pro', 'panda_elite'];

const TIER_ICONS: Record<string, typeof Crown> = {
  standard: Shield,
  panda_plus: Star,
  panda_pro: Crown,
  panda_elite: Zap,
};

function TierCard({
  tier,
  isCurrentTier,
}: {
  tier: TierInfo;
  isCurrentTier: boolean;
}) {
  const Icon = TIER_ICONS[tier.key] || Shield;

  const benefits: { label: string; available: boolean }[] = [
    {
      label: tier.daily_quest_limit
        ? `${tier.daily_quest_limit} daily quests`
        : 'Unlimited quests',
      available: true,
    },
    {
      label: tier.monthly_campaign_limit
        ? `${tier.monthly_campaign_limit} campaigns monthly`
        : 'Unlimited campaigns',
      available: true,
    },
    { label: 'Launch campaigns', available: tier.can_create_campaign },
    { label: 'Campaign creator tools', available: tier.campaign_feature_level !== 'none' },
    { label: 'Image campaigns', available: tier.can_use_media },
    { label: 'Video campaigns', available: tier.can_use_media },
    { label: 'Video contests', available: tier.can_create_video_contest },
    { label: 'Bounties', available: tier.can_create_bounty },
  ];

  return (
    <Card
      className={cn(
        'relative flex flex-col p-lg transition-all',
        isCurrentTier && 'ring-2 ring-brand-cobalt shadow-lg',
      )}
    >
      {isCurrentTier && (
        <Badge tone="cobalt" className="absolute -top-3 left-1/2 -translate-x-1/2">
          Current Plan
        </Badge>
      )}

      <div className="mb-md flex items-center gap-md">
        <div className={cn(
          'flex h-12 w-12 items-center justify-center rounded-full',
          tier.key === 'panda_elite' ? 'bg-reward-jungle/10' :
          tier.key === 'panda_pro' ? 'bg-reward-amber/10' :
          tier.key === 'panda_plus' ? 'bg-brand-cobalt/10' :
          'bg-bg-elevated',
        )}>
          <Icon className={cn(
            'h-6 w-6',
            tier.key === 'panda_elite' ? 'text-reward-jungle' :
            tier.key === 'panda_pro' ? 'text-reward-amber' :
            tier.key === 'panda_plus' ? 'text-brand-cobalt' :
            'text-ink-muted',
          )} />
        </div>
        <div>
          <h3 className="font-display text-h2 text-ink-primary">{tier.name}</h3>
          <p className="text-body text-ink-muted">
            {tier.nft_required === 0
              ? 'Free'
              : `Hold ${tier.nft_required} LPanda NFT${tier.nft_required > 1 ? 's' : ''}`}
          </p>
        </div>
      </div>

      <p className="mb-md text-body text-ink-muted">{tier.description}</p>

      <ul className="mb-lg flex-1 space-y-sm">
        {benefits.map((b) => (
          <li key={b.label} className="flex items-center gap-sm text-body">
            {b.available ? (
              <CheckCircle2 className="h-4 w-4 shrink-0 text-reward-jungle" />
            ) : (
              <X className="h-4 w-4 shrink-0 text-ink-muted/40" />
            )}
            <span className={b.available ? 'text-ink-primary' : 'text-ink-muted/60'}>
              {b.label}
            </span>
          </li>
        ))}
      </ul>

      {tier.key !== 'standard' && !isCurrentTier && (
        <Link href="https://opensea.io/collection/lpanda" target="_blank" rel="noopener noreferrer">
          <Button variant="jungle" className="w-full">
            <ExternalLink className="h-4 w-4" />
            <span>View LPanda NFT</span>
          </Button>
        </Link>
      )}
    </Card>
  );
}

export default function PremiumPage() {
  const { data: tiers, isLoading: tiersLoading } = useQuery<TierInfo[]>(
    'premiumTiers',
    () => premiumAPI.getTiers(),
    { staleTime: 300_000 },
  );

  const { data: status, isLoading: statusLoading } = useQuery<MembershipStatus>(
    'membershipStatus',
    () => premiumAPI.getStatus(),
    { staleTime: 60_000 },
  );

  const isLoading = tiersLoading || statusLoading;

  return (
    <div className="animate-page-in space-y-xl">
      {/* Header */}
      <div className="flex flex-col gap-md sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-h1 text-ink-primary">LPanda Premium</h1>
          <p className="text-body text-ink-muted">
            Unlock exclusive features by holding LPanda NFTs in your wallet.
          </p>
        </div>
        <div className="flex gap-sm">
          <ConnectWalletButton variant="jungle" />
          {status?.wallet_address && (
            <Button
              variant="ghost"
              onClick={() => premiumAPI.revalidate()}
            >
              Verify NFT Holdings
            </Button>
          )}
        </div>
      </div>

      {/* Current membership status */}
      {status && <MembershipStatusCard />}

      {/* Tier comparison */}
      <div>
        <h2 className="mb-lg font-display text-h2 text-ink-primary">Membership Tiers</h2>
        {isLoading ? (
          <div className="grid gap-lg sm:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <Card key={i} className="p-lg space-y-md">
                <Skeleton className="h-12 w-12 rounded-full" />
                <Skeleton className="h-6 w-32" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
              </Card>
            ))}
          </div>
        ) : tiers ? (
          <div className="grid gap-lg sm:grid-cols-2 lg:grid-cols-4">
            {tiers.map((tier) => (
              <TierCard
                key={tier.key}
                tier={tier}
                isCurrentTier={status?.tier === tier.key}
              />
            ))}
          </div>
        ) : null}
      </div>

      {/* How it works */}
      <Card className="p-lg">
        <h2 className="mb-md font-display text-h2 text-ink-primary">How It Works</h2>
        <div className="grid gap-lg sm:grid-cols-3">
          <div className="space-y-sm">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-cobalt/10">
              <span className="font-display text-h3 text-brand-cobalt">1</span>
            </div>
            <h3 className="font-display text-h3 text-ink-primary">Acquire LPanda NFTs</h3>
            <p className="text-body text-ink-muted">
              Purchase LPanda NFTs from OpenSea or other NFT marketplaces.
            </p>
          </div>
          <div className="space-y-sm">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-cobalt/10">
              <span className="font-display text-h3 text-brand-cobalt">2</span>
            </div>
            <h3 className="font-display text-h3 text-ink-primary">Connect Your Wallet</h3>
            <p className="text-body text-ink-muted">
              Link your EVM wallet to your LPanda account. We verify NFT ownership on-chain.
            </p>
          </div>
          <div className="space-y-sm">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-cobalt/10">
              <span className="font-display text-h3 text-brand-cobalt">3</span>
            </div>
            <h3 className="font-display text-h3 text-ink-primary">Unlock Premium</h3>
            <p className="text-body text-ink-muted">
              Your tier is assigned automatically. Hold more NFTs to upgrade anytime.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
