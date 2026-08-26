'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import {
  Wallet,
  Loader2,
  CheckCircle2,
  Crown,
  Star,
  Shield,
  Zap,
  ExternalLink,
  AlertTriangle,
  X,
  ArrowRight,
} from 'lucide-react';
import { Button, cn, Card, Badge } from '@meta-jungle/ui';
import { premiumAPI, TierInfo, WalletConnectResponse } from '@/api/premium';
import { toast } from 'sonner';
import { WalletConnectModal } from '@/components/wallet-connect-modal';

const TIER_ICONS: Record<string, typeof Crown> = {
  standard: Shield,
  panda_plus: Star,
  panda_pro: Crown,
  panda_elite: Zap,
};

const TIER_ORDER = ['standard', 'panda_plus', 'panda_pro', 'panda_elite'];

const TIER_COLORS: Record<string, { bg: string; text: string; ring: string; glow: string }> = {
  standard: { bg: 'bg-bg-elevated', text: 'text-ink-muted', ring: 'ring-line', glow: '' },
  panda_plus: { bg: 'bg-brand-cobalt/10', text: 'text-brand-cobalt', ring: 'ring-brand-cobalt/40', glow: '' },
  panda_pro: { bg: 'bg-reward-amber/10', text: 'text-reward-amber', ring: 'ring-reward-amber/40', glow: 'shadow-[0_0_20px_rgba(217,119,6,0.15)]' },
  panda_elite: { bg: 'bg-reward-jungle/10', text: 'text-reward-jungle', ring: 'ring-reward-jungle/40', glow: 'shadow-[0_0_24px_rgba(22,160,99,0.2)]' },
};

const TIER_BENEFITS: Record<string, string[]> = {
  panda_plus: ['15 daily quests', '5 campaigns/month', 'Campaign creator tools'],
  panda_pro: ['30 daily quests', '15 campaigns/month', 'Image campaigns', 'Video contests'],
  panda_elite: ['Unlimited quests', 'Unlimited campaigns', 'Video campaigns', 'Bounties', 'Priority support'],
};

interface UpgradeTierModalProps {
  isOpen: boolean;
  onClose: () => void;
  currentTier: string;
  currentNftCount: number;
}

export function UpgradeTierModal({
  isOpen,
  onClose,
  currentTier,
  currentNftCount,
}: UpgradeTierModalProps) {
  const queryClient = useQueryClient();
  const [selectedTier, setSelectedTier] = useState<string | null>(null);
  const [showWalletModal, setShowWalletModal] = useState(false);
  const [insufficientNfts, setInsufficientNfts] = useState(false);
  const [requiredNfts, setRequiredNfts] = useState(0);

  const { data: tiers, isLoading: tiersLoading } = useQuery<TierInfo[]>(
    'tierConfigs',
    () => premiumAPI.getTiers(),
    { enabled: isOpen },
  );

  const connectMutation = useMutation(
    (address: string) => premiumAPI.connectWallet(address),
    {
      onSuccess: (data: WalletConnectResponse) => {
        const targetTier = tiers?.find((t) => t.key === selectedTier);
        if (targetTier && data.nft_count < targetTier.nft_required) {
          setInsufficientNfts(true);
          setRequiredNfts(targetTier.nft_required);
          toast.error(
            `Insufficient NFTs in wallet. You need ${targetTier.nft_required} NFTs but only have ${data.nft_count}.`,
          );
          return;
        }

        setInsufficientNfts(false);
        toast.success(
          `Upgraded to ${data.tier_name}! You have ${data.nft_count} NFTs.`,
        );
        queryClient.invalidateQueries('membershipStatus');
        queryClient.invalidateQueries('currentUser');
        setShowWalletModal(false);
        onClose();
      },
      onError: (err: any) => {
        toast.error(
          err?.response?.data?.detail || 'Failed to connect wallet',
        );
      },
    },
  );

  const handleConnectClick = () => {
    if (!selectedTier) {
      toast.error('Please select a tier first');
      return;
    }
    setShowWalletModal(true);
  };

  const handleWalletConnect = (address: string) => {
    connectMutation.mutate(address);
  };

  if (!isOpen) return null;

  const availableTiers = TIER_ORDER.filter(
    (key) => TIER_ORDER.indexOf(key) > TIER_ORDER.indexOf(currentTier),
  );

  return (
    <>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-bg-dark/60 p-md backdrop-blur-sm">
        <Card className="relative w-full max-w-2xl space-y-lg overflow-y-auto max-h-[90vh] p-xl">
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute right-md top-md text-ink-muted hover:text-ink-primary"
          >
            <X className="h-5 w-5" />
          </button>

          <div>
            <h2 className="font-display text-h2 text-ink-primary">
              Upgrade Your Tier
            </h2>
            <p className="mt-sm text-body text-ink-muted">
              Hold more LPanda NFTs to unlock higher tiers with more earning power.
            </p>
          </div>

          {/* Current tier indicator */}
          <div className="flex items-center gap-sm rounded-card bg-bg-elevated px-md py-sm">
            <span className="text-label text-ink-muted">Current tier:</span>
            <Badge tone="cobalt">{currentTier.replace('panda_', 'Panda ').replace('standard', 'Standard')}</Badge>
            <span className="text-label text-ink-muted ml-auto">{currentNftCount} NFTs held</span>
          </div>

          {/* Tier selection cards */}
          {tiersLoading ? (
            <div className="flex items-center gap-md">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span className="text-body text-ink-muted">Loading tiers...</span>
            </div>
          ) : availableTiers.length === 0 ? (
            <div className="rounded-card border border-reward-jungle/30 bg-reward-jungle/10 p-lg text-center">
              <CheckCircle2 className="mx-auto mb-sm h-8 w-8 text-reward-jungle" />
              <p className="font-display text-body font-semibold text-reward-jungle">
                You&apos;re on the highest tier!
              </p>
              <p className="mt-xs text-caption text-ink-muted">
                Enjoy all premium features and unlimited access.
              </p>
            </div>
          ) : (
            <div className="grid gap-md sm:grid-cols-2">
              {tiers
                ?.filter((t) => availableTiers.includes(t.key))
                .map((tier) => {
                  const TierIcon = TIER_ICONS[tier.key] || Shield;
                  const colors = TIER_COLORS[tier.key] || TIER_COLORS.standard;
                  const benefits = TIER_BENEFITS[tier.key] || [];
                  const isSelected = selectedTier === tier.key;

                  return (
                    <button
                      key={tier.key}
                      onClick={() => {
                        setSelectedTier(tier.key);
                        setInsufficientNfts(false);
                      }}
                      className={cn(
                        'group relative flex flex-col rounded-card border-2 p-lg text-left transition-all',
                        isSelected
                          ? `border-reward-gold bg-reward-gold/5 ${colors.glow}`
                          : `border-transparent bg-bg-surface hover:border-stroke-hover`,
                      )}
                    >
                      {/* Selected indicator */}
                      {isSelected && (
                        <div className="absolute -right-2 -top-2">
                          <div className="flex h-6 w-6 items-center justify-center rounded-full bg-reward-gold text-white">
                            <CheckCircle2 className="h-4 w-4" />
                          </div>
                        </div>
                      )}

                      {/* Tier header */}
                      <div className="mb-md flex items-center gap-md">
                        <div className={cn(
                          'flex h-12 w-12 items-center justify-center rounded-full transition-transform group-hover:scale-110',
                          colors.bg,
                        )}>
                          <TierIcon className={cn('h-6 w-6', colors.text)} />
                        </div>
                        <div>
                          <h3 className="font-display text-body font-semibold text-ink-primary">
                            {tier.name}
                          </h3>
                          <p className="text-caption text-ink-muted">
                            {tier.nft_required} NFT{tier.nft_required !== 1 ? 's' : ''} required
                          </p>
                        </div>
                      </div>

                      {/* Benefits preview */}
                      <ul className="flex-1 space-y-xs">
                        {benefits.map((b) => (
                          <li key={b} className="flex items-center gap-xs text-caption text-ink-muted">
                            <ArrowRight className="h-3 w-3 text-forest-500" />
                            {b}
                          </li>
                        ))}
                      </ul>

                      {/* NFT progress */}
                      <div className="mt-md pt-md border-t border-line">
                        <div className="flex items-center justify-between text-caption">
                          <span className="text-ink-muted">Your NFTs</span>
                          <span className={cn(
                            'font-display font-semibold',
                            currentNftCount >= tier.nft_required ? 'text-success' : 'text-reward-amber',
                          )}>
                            {currentNftCount}/{tier.nft_required}
                          </span>
                        </div>
                        <div className="mt-xs h-1.5 overflow-hidden rounded-full bg-bg-elevated">
                          <div
                            className={cn(
                              'h-full rounded-full transition-all',
                              currentNftCount >= tier.nft_required ? 'bg-success' : 'bg-reward-amber',
                            )}
                            style={{ width: `${Math.min(100, (currentNftCount / tier.nft_required) * 100)}%` }}
                          />
                        </div>
                      </div>
                    </button>
                  );
                })}
            </div>
          )}

          {/* Insufficient NFTs error */}
          {insufficientNfts && (
            <div className="space-y-sm rounded-card border border-danger/30 bg-danger/10 p-md">
              <div className="flex items-center gap-sm text-body font-medium text-danger">
                <AlertTriangle className="h-5 w-5" />
                Insufficient NFTs in wallet
              </div>
              <p className="text-body text-ink-muted">
                You need {requiredNfts} NFTs but your wallet only has{' '}
                {currentNftCount}. Mint more NFTs to upgrade.
              </p>
              <a
                href="https://lpanda-mint.vercel.app/"
                target="_blank"
                rel="noreferrer"
              >
                <Button variant="jungle" size="sm" className="mt-sm">
                  Mint More NFTs <ExternalLink className="ml-1 h-4 w-4" />
                </Button>
              </a>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex flex-col gap-sm">
            <Button
              variant="jungle"
              onClick={handleConnectClick}
              disabled={!selectedTier || connectMutation.isLoading || availableTiers.length === 0}
              className="w-full"
            >
              {connectMutation.isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Verifying...
                </>
              ) : (
                <>
                  <Wallet className="h-4 w-4" /> Connect Wallet & Upgrade
                </>
              )}
            </Button>

            <a
              href="https://lpanda-mint.vercel.app/"
              target="_blank"
              rel="noreferrer"
              className="w-full"
            >
              <Button variant="gold" className="w-full">
                Mint NFTs <ExternalLink className="ml-1 h-4 w-4" />
              </Button>
            </a>
          </div>
        </Card>
      </div>

      {/* Wallet connection modal — higher z-index to appear above upgrade modal */}
      <div className="z-[60]">
        <WalletConnectModal
          isOpen={showWalletModal}
          onClose={() => setShowWalletModal(false)}
          onConnect={handleWalletConnect}
          isConnecting={connectMutation.isLoading}
        />
      </div>
    </>
  );
}
