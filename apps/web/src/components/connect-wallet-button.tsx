'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from 'react-query';
import { Wallet, Loader2, CheckCircle2 } from 'lucide-react';
import { Button, cn } from '@meta-jungle/ui';
import { premiumAPI, WalletConnectResponse } from '@/api/premium';
import { toast } from 'sonner';
import { WalletConnectModal } from '@/components/wallet-connect-modal';

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
  const [showModal, setShowModal] = useState(false);

  const connectMutation = useMutation(
    (address: string) => premiumAPI.connectWallet(address),
    {
      onSuccess: (data) => {
        toast.success(
          `Connected! You're now ${data.tier_name} with ${data.nft_count} NFTs.`
        );
        queryClient.invalidateQueries('membershipStatus');
        queryClient.invalidateQueries('currentUser');
        setShowModal(false);
        onConnected?.(data);
      },
      onError: (err: any) => {
        toast.error(err?.response?.data?.detail || 'Failed to connect wallet');
      },
    },
  );

  const handleConnect = (address: string) => {
    connectMutation.mutate(address);
  };

  return (
    <>
      <Button
        variant={variant}
        size={size}
        onClick={() => setShowModal(true)}
        disabled={connectMutation.isLoading}
        className={className}
      >
        {connectMutation.isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Wallet className="h-4 w-4" />
        )}
        <span>
          {connectMutation.isLoading ? 'Verifying...' : 'Connect Wallet'}
        </span>
      </Button>

      <WalletConnectModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onConnect={handleConnect}
        isConnecting={connectMutation.isLoading}
      />
    </>
  );
}
