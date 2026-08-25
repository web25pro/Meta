'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from 'react-query';
import { Wallet, Loader2, CheckCircle2, ExternalLink } from 'lucide-react';
import { Button, cn } from '@meta-jungle/ui';
import { premiumAPI, WalletConnectResponse } from '@/api/premium';
import { toast } from 'sonner';

interface ConnectWalletButtonProps {
  onConnected?: (result: WalletConnectResponse) => void;
  variant?: 'cobalt' | 'jungle' | 'gold' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function ConnectWalletButton({
  onConnected,
  variant = 'jungle',
  size = 'md',
  className,
}: ConnectWalletButtonProps) {
  const queryClient = useQueryClient();
  const [walletAddress, setWalletAddress] = useState('');
  const [showInput, setShowInput] = useState(false);

  const connectMutation = useMutation(
    (address: string) => premiumAPI.connectWallet(address),
    {
      onSuccess: (data) => {
        toast.success(`Connected! You're now ${data.tier_name} with ${data.nft_count} NFTs.`);
        queryClient.invalidateQueries('membershipStatus');
        queryClient.invalidateQueries('currentUser');
        setShowInput(false);
        setWalletAddress('');
        onConnected?.(data);
      },
      onError: (err: any) => {
        toast.error(err?.response?.data?.detail || 'Failed to connect wallet');
      },
    },
  );

  const handleConnect = async () => {
    // Try to connect via browser wallet (MetaMask / WalletConnect)
    if (typeof window !== 'undefined' && (window as any).ethereum) {
      try {
        const accounts = await (window as any).ethereum.request({
          method: 'eth_requestAccounts',
        });
        if (accounts && accounts.length > 0) {
          connectMutation.mutate(accounts[0]);
          return;
        }
      } catch {
        // User rejected or no wallet — fall through to manual input
      }
    }
    // No browser wallet detected — show manual input
    setShowInput(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (walletAddress.trim()) {
      connectMutation.mutate(walletAddress.trim());
    }
  };

  if (showInput) {
    return (
      <form onSubmit={handleSubmit} className={cn('flex flex-col gap-sm', className)}>
        <input
          type="text"
          value={walletAddress}
          onChange={(e) => setWalletAddress(e.target.value)}
          placeholder="0x... wallet address"
          className="w-full rounded-card border border-line bg-bg-primary px-md py-sm text-body text-ink-primary placeholder:text-ink-muted focus:border-brand-cobalt focus:outline-none"
          disabled={connectMutation.isLoading}
        />
        <div className="flex gap-sm">
          <Button
            type="submit"
            variant={variant}
            size={size}
            disabled={!walletAddress.trim() || connectMutation.isLoading}
            className="flex-1"
          >
            {connectMutation.isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              'Verify NFTs'
            )}
          </Button>
          <Button
            type="button"
            variant="ghost"
            size={size}
            onClick={() => { setShowInput(false); setWalletAddress(''); }}
            disabled={connectMutation.isLoading}
          >
            Cancel
          </Button>
        </div>
      </form>
    );
  }

  return (
    <Button
      variant={variant}
      size={size}
      onClick={handleConnect}
      disabled={connectMutation.isLoading}
      className={className}
    >
      {connectMutation.isLoading ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <Wallet className="h-4 w-4" />
      )}
      <span>{connectMutation.isLoading ? 'Verifying...' : 'Connect Wallet'}</span>
    </Button>
  );
}
