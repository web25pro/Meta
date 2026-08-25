'use client';

import { useState, useEffect, useCallback } from 'react';
import { Loader2, X, ExternalLink, Smartphone, Monitor } from 'lucide-react';
import { Button, cn, Card } from '@meta-jungle/ui';
import { toast } from 'sonner';

interface WalletOption {
  id: string;
  name: string;
  icon: string;
  description: string;
  installed: boolean;
  downloadUrl: string;
  connect: () => Promise<string | null>;
}

interface WalletConnectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConnect: (address: string) => void;
  isConnecting?: boolean;
}

export function WalletConnectModal({
  isOpen,
  onClose,
  onConnect,
  isConnecting = false,
}: WalletConnectModalProps) {
  const [isMobile, setIsMobile] = useState(false);
  const [connectingWallet, setConnectingWallet] = useState<string | null>(null);

  useEffect(() => {
    setIsMobile(window.innerWidth < 768);
  }, []);

  const getWalletOptions = useCallback((): WalletOption[] => {
    const ethereum = typeof window !== 'undefined' ? (window as any).ethereum : null;
    const isMetaMaskInstalled = !!ethereum?.isMetaMask;
    const isCoinbaseInstalled = !!ethereum?.isCoinbaseWallet;

    return [
      {
        id: 'metamask',
        name: 'MetaMask',
        icon: '🦊',
        description: isMetaMaskInstalled ? 'Connect to MetaMask' : 'Install MetaMask',
        installed: isMetaMaskInstalled,
        downloadUrl: 'https://metamask.io/download/',
        connect: async () => {
          if (!ethereum) return null;
          try {
            const accounts = await ethereum.request({
              method: 'eth_requestAccounts',
            });
            return accounts?.[0] || null;
          } catch {
            return null;
          }
        },
      },
      {
        id: 'coinbase',
        name: 'Coinbase Wallet',
        icon: '🔵',
        description: isCoinbaseInstalled ? 'Connect to Coinbase Wallet' : 'Install Coinbase Wallet',
        installed: isCoinbaseInstalled,
        downloadUrl: 'https://www.coinbase.com/wallet',
        connect: async () => {
          if (!ethereum) return null;
          try {
            // Try Coinbase Wallet provider
            const provider = ethereum.providers?.find(
              (p: any) => p.isCoinbaseWallet
            ) || (ethereum.isCoinbaseWallet ? ethereum : null);
            if (!provider) return null;
            const accounts = await provider.request({
              method: 'eth_requestAccounts',
            });
            return accounts?.[0] || null;
          } catch {
            return null;
          }
        },
      },
      {
        id: 'walletconnect',
        name: 'WalletConnect',
        icon: '🔗',
        description: 'Scan QR code with your mobile wallet',
        installed: true, // Always available via universal link
        downloadUrl: 'https://walletconnect.com/',
        connect: async () => {
          // On mobile, use WalletConnect universal link
          if (isMobile) {
            const currentUrl = encodeURIComponent(window.location.href);
            window.open(
              `https://walletconnect.com/registry?q=${currentUrl}`,
              '_blank'
            );
            return null;
          }
          // On desktop, user needs WalletConnect compatible wallet
          toast.info('Please use a WalletConnect-compatible mobile wallet to scan the QR code');
          return null;
        },
      },
      {
        id: 'trust',
        name: 'Trust Wallet',
        icon: '🛡️',
        description: isMobile ? 'Open in Trust Wallet' : 'Connect via Trust Wallet',
        installed: true,
        downloadUrl: 'https://trustwallet.com/',
        connect: async () => {
          if (ethereum?.isTrust) {
            try {
              const accounts = await ethereum.request({
                method: 'eth_requestAccounts',
              });
              return accounts?.[0] || null;
            } catch {
              return null;
            }
          }
          // On mobile, try deep link
          if (isMobile) {
            const currentUrl = encodeURIComponent(window.location.href);
            window.open(
              `https://link.trustwallet.com/open_url?coin_id=60&url=${currentUrl}`,
              '_blank'
            );
          }
          return null;
        },
      },
    ];
  }, [isMobile]);

  const handleConnect = async (wallet: WalletOption) => {
    setConnectingWallet(wallet.id);
    try {
      const address = await wallet.connect();
      if (address) {
        onConnect(address);
      } else if (!wallet.installed) {
        // Redirect to download page
        window.open(wallet.downloadUrl, '_blank');
      }
    } catch (err: any) {
      toast.error(err?.message || 'Failed to connect wallet');
    } finally {
      setConnectingWallet(null);
    }
  };

  if (!isOpen) return null;

  const walletOptions = getWalletOptions();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-bg-dark/60 p-md">
      <Card className="relative w-full max-w-md space-y-lg p-xl">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute right-md top-md text-ink-muted hover:text-ink-primary"
        >
          <X className="h-5 w-5" />
        </button>

        <div>
          <h2 className="font-display text-h2 text-ink-primary">
            Connect Wallet
          </h2>
          <p className="mt-sm text-body text-ink-muted">
            Choose your preferred wallet to connect and verify your NFTs.
          </p>
        </div>

        {/* Device indicator */}
        <div className="flex items-center gap-sm rounded-card bg-bg-elevated p-sm text-label text-ink-muted">
          {isMobile ? (
            <>
              <Smartphone className="h-4 w-4" />
              <span>Mobile detected — deep links available</span>
            </>
          ) : (
            <>
              <Monitor className="h-4 w-4" />
              <span>Desktop detected — browser extensions</span>
            </>
          )}
        </div>

        {/* Wallet options */}
        <div className="space-y-sm">
          {walletOptions.map((wallet) => {
            const isConnectingThis = connectingWallet === wallet.id;
            return (
              <button
                key={wallet.id}
                onClick={() => handleConnect(wallet)}
                disabled={isConnecting || isConnectingThis}
                className={cn(
                  'flex w-full items-center gap-md rounded-card border p-md text-left transition-all',
                  'border-line hover:border-brand-cobalt hover:bg-brand-ice/50',
                  'disabled:opacity-50 disabled:cursor-not-allowed',
                  !wallet.installed && 'opacity-70'
                )}
              >
                <span className="text-2xl">{wallet.icon}</span>
                <div className="flex-1">
                  <p className="font-display text-body font-semibold text-ink-primary">
                    {wallet.name}
                  </p>
                  <p className="text-label text-ink-muted">
                    {wallet.description}
                  </p>
                </div>
                {isConnectingThis ? (
                  <Loader2 className="h-5 w-5 animate-spin text-brand-cobalt" />
                ) : !wallet.installed ? (
                  <ExternalLink className="h-4 w-4 text-ink-muted" />
                ) : null}
              </button>
            );
          })}
        </div>

        {/* Manual input fallback */}
        <div className="border-t border-line pt-md">
          <p className="mb-sm text-label text-ink-muted">
            Or enter your wallet address manually:
          </p>
          <ManualAddressInput
            onSubmit={onConnect}
            disabled={isConnecting}
          />
        </div>

        {/* Help text */}
        <p className="text-center text-caption text-ink-muted">
          New to crypto?{' '}
          <a
            href="https://ethereum.org/en/wallets/"
            target="_blank"
            rel="noreferrer"
            className="text-brand-cobalt hover:underline"
          >
            Learn about wallets
          </a>
        </p>
      </Card>
    </div>
  );
}

function ManualAddressInput({
  onSubmit,
  disabled,
}: {
  onSubmit: (address: string) => void;
  disabled: boolean;
}) {
  const [address, setAddress] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (address.trim() && address.trim().startsWith('0x')) {
      onSubmit(address.trim());
    } else {
      toast.error('Please enter a valid Ethereum address starting with 0x');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-sm">
      <input
        type="text"
        value={address}
        onChange={(e) => setAddress(e.target.value)}
        placeholder="0x... wallet address"
        className="flex-1 rounded-card border border-line bg-bg-primary px-md py-sm text-body text-ink-primary placeholder:text-ink-muted focus:border-brand-cobalt focus:outline-none"
        disabled={disabled}
      />
      <Button
        type="submit"
        variant="cobalt"
        size="sm"
        disabled={!address.trim() || disabled}
      >
        Verify
      </Button>
    </form>
  );
}
