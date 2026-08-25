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
} from 'lucide-react';
import { Button, cn, Card } from '@meta-jungle/ui';
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
        // Check if the wallet has enough NFTs for the selected tier
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
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-bg-dark/60 p-md">
        <Card className="relative w-full max-w-lg space-y-lg overflow-y-auto max-h-[90vh] p-xl">
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
              Select the tier you want to upgrade to, then connect your wallet to
              verify NFT ownership.
            </p>
          </div>

          {/* Tier selection */}
          {tiersLoading ? (
            <div className="flex items-center gap-md">
              <Loader2 className="h-5 w-5 animate-spin" />
              <span className="text-body text-ink-muted">Loading tiers...</span>
            </div>
          ) : availableTiers.length === 0 ? (
            <div className="rounded-card border border-reward-jungle/30 bg-reward-jungle/10 p-md text-body text-reward-jungle">
              <CheckCircle2 className="mr-sm inline h-4 w-4" />
              You&apos;re already on the highest tier!
            </div>
          ) : (
            <div className="space-y-sm">
              <p className="text-label text-ink-muted">Select target tier:</p>
              {tiers
                ?.filter((t) => availableTiers.includes(t.key))
                .map((tier) => {
                  const TierIcon = TIER_ICONS[tier.key] || Shield;
                  const isSelected = selectedTier === tier.key;
                  return (
                    <button
                      key={tier.key}
                      onClick={() => {
                        setSelectedTier(tier.key);
                        setInsufficientNfts(false);
                      }}
                      className={cn(
                        'flex w-full items-center gap-md rounded-card border p-md text-left transition-colors',
                        isSelected
                          ? 'border-brand-cobalt bg-brand-ice'
                          : 'border-line hover:border-brand-cobalt/50',
                      )}
                    >
                      <div
                        className={cn(
                          'flex h-10 w-10 items-center justify-center rounded-full',
                          tier.key === 'panda_elite'
                            ? 'bg-reward-jungle/10'
                            : tier.key === 'panda_pro'
                              ? 'bg-reward-amber/10'
                              : tier.key === 'panda_plus'
                                ? 'bg-brand-cobalt/10'
                                : 'bg-bg-elevated',
                        )}
                      >
                        <TierIcon
                          className={cn(
                            'h-5 w-5',
                            tier.key === 'panda_elite'
                              ? 'text-reward-jungle'
                              : tier.key === 'panda_pro'
                                ? 'text-reward-amber'
                                : tier.key === 'panda_plus'
                                  ? 'text-brand-cobalt'
                                  : 'text-ink-muted',
                          )}
                        />
                      </div>
                      <div className="flex-1">
                        <p className="font-display text-body font-semibold text-ink-primary">
                          {tier.name}
                        </p>
                        <p className="text-label text-ink-muted">
                          {tier.nft_required} NFT{tier.nft_required !== 1 ? 's' : ''}{' '}
                          required
                        </p>
                      </div>
                      {isSelected && (
                        <CheckCircle2 className="h-5 w-5 text-brand-cobalt" />
                      )}
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

      {/* Wallet connection modal */}
      <WalletConnectModal
        isOpen={showWalletModal}
        onClose={() => setShowWalletModal(false)}
        onConnect={handleWalletConnect}
        isConnecting={connectMutation.isLoading}
      />
    </>
  );
}
