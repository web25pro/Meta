'use client';

import { useMemo, useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import {
  Phone,
  Wifi,
  Zap,
  Tv,
  Gift,
  Smartphone,
  Check,
  Copy,
  Loader2,
} from 'lucide-react';
import { toast } from 'sonner';
import {
  Card,
  Button,
  Input,
  Modal,
  PPAmount,
  PandaMascot,
  cn,
} from '@meta-jungle/ui';
import apiClient from '@/lib/api';
import { metajungleAPI } from '@/api/metajungle';
import { PointsTransaction, PaginatedResponse } from '@/types';
import {
  CATEGORIES,
  FLAG,
  INPUT_LABEL,
  type MarketCategory,
  type Product,
} from '@/lib/marketplace';

const CATEGORY_ICON: Record<MarketCategory, React.ReactNode> = {
  airtime: <Phone className="h-6 w-6" />,
  data: <Smartphone className="h-6 w-6" />,
  electricity: <Zap className="h-6 w-6" />,
  cable: <Tv className="h-6 w-6" />,
  giftcards: <Gift className="h-6 w-6" />,
};

type Step = 'confirm' | 'input' | 'processing' | 'success';

export default function MarketplacePage() {
  const [active, setActive] = useState<MarketCategory>('airtime');
  const [selected, setSelected] = useState<Product | null>(null);
  const [step, setStep] = useState<Step>('confirm');
  const [inputValue, setInputValue] = useState('');
  const [voucher, setVoucher] = useState('');

  const queryClient = useQueryClient();

  // Current PP balance (sum of ledger) — mirrors the Panda Wallet page.
  const { data: ledger } = useQuery<PaginatedResponse<PointsTransaction>>(
    'pointsHistory',
    async () => (await apiClient.get('/points/transactions')).data,
  );
  const balance = useMemo(
    () => ledger?.items.reduce((s, t) => s + t.amount, 0) ?? 0,
    [ledger],
  );

  // Live catalog from the backend.
  const { data: catalog, isLoading } = useQuery('mjCatalog', metajungleAPI.getCatalog, {
    retry: false,
  });
  const products = (catalog as Product[] | undefined) ?? [];
  const items = products.filter((p) => p.category === active);

  const openRedeem = (p: Product) => {
    setSelected(p);
    setStep('confirm');
    setInputValue('');
    setVoucher('');
  };

  const close = () => setSelected(null);

  const confirm = () => {
    if (!selected) return;
    if (balance < selected.pp) {
      toast.error('Not enough Panda Points for this redemption.');
      return;
    }
    setStep(INPUT_LABEL[selected.input] ? 'input' : 'processing');
    if (!INPUT_LABEL[selected.input]) runProcessing();
  };

  const submitInput = () => {
    if (!inputValue.trim()) {
      toast.error('Please fill in the required field.');
      return;
    }
    runProcessing();
  };

  const runProcessing = async () => {
    if (!selected) return;
    setStep('processing');
    try {
      const result = await metajungleAPI.redeem(selected.id, inputValue || undefined);
      setVoucher(result.voucher_code);
      // Refresh balance after the PP debit settles.
      queryClient.invalidateQueries('pointsHistory');
      setStep('success');
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err?.message || 'Redemption failed';
      toast.error(msg);
      setStep('confirm');
    }
  };

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Marketplace</h1>
        <p className="mt-1 text-body text-ink-muted">
          Spend Panda Points on airtime, data, electricity and gift cards.
        </p>
      </div>

      {/* Balance strip */}
      <Card className="flex items-center justify-between bg-bg-dark">
        <span className="text-label text-brand-ice">Available to spend</span>
        <span className="font-display text-h1 text-reward-gold">
          {balance.toLocaleString('en-US')}
          <span className="ml-1 text-label font-sans text-reward-gold/80">PP</span>
        </span>
      </Card>

      {/* Category tabs */}
      <div className="flex flex-wrap gap-sm">
        {CATEGORIES.map((c) => (
          <button
            key={c.key}
            onClick={() => setActive(c.key)}
            className={cn(
              'inline-flex items-center gap-sm rounded-pill px-md py-sm text-label font-medium transition-colors',
              active === c.key
                ? 'bg-brand-cobalt text-ink-inverse'
                : 'border border-line bg-bg-primary text-ink-muted hover:bg-bg-elevated',
            )}
          >
            <span className={active === c.key ? 'text-ink-inverse' : 'text-brand-cobalt'}>
              {CATEGORY_ICON[c.key]}
            </span>
            {c.label}
          </button>
        ))}
      </div>

      <p className="-mt-md text-label text-ink-muted">
        {CATEGORIES.find((c) => c.key === active)?.blurb}
      </p>

      {/* Product grid */}
      {isLoading ? (
        <div className="grid gap-lg sm:grid-cols-2 lg:grid-cols-3">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-48 animate-pulse rounded-card bg-bg-elevated" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <div className="rounded-card border border-line bg-bg-primary p-xl text-center text-ink-muted">
          No products available in this category.
        </div>
      ) : (
        <div className="grid gap-lg sm:grid-cols-2 lg:grid-cols-3">
          {items.map((p) => (
            <ProductCard key={p.id} product={p} onRedeem={() => openRedeem(p)} />
          ))}
        </div>
      )}

      {/* Redemption flow */}
      <Modal
        open={!!selected}
        onClose={close}
        title={step === 'success' ? undefined : 'Redeem'}
      >
        {selected && (
          <RedeemFlow
            product={selected}
            step={step}
            balance={balance}
            inputValue={inputValue}
            setInputValue={setInputValue}
            voucher={voucher}
            onConfirm={confirm}
            onSubmitInput={submitInput}
            onClose={close}
          />
        )}
      </Modal>
    </div>
  );
}

function ProductCard({ product, onRedeem }: { product: Product; onRedeem: () => void }) {
  const icon =
    product.category === 'giftcards' ? (
      <Gift className="h-6 w-6" />
    ) : product.category === 'electricity' ? (
      <Zap className="h-6 w-6" />
    ) : product.category === 'cable' ? (
      <Wifi className="h-6 w-6" />
    ) : product.category === 'data' ? (
      <Smartphone className="h-6 w-6" />
    ) : (
      <Phone className="h-6 w-6" />
    );

  return (
    <Card className="flex flex-col gap-md transition-shadow hover:shadow-card-hover">
      <div className="flex items-start justify-between">
        <div className="text-brand-cobalt">{icon}</div>
        <div className="flex gap-1 text-sm">
          {product.regions.slice(0, 4).map((r) => (
            <span key={r} title={r}>{FLAG[r] ?? r}</span>
          ))}
        </div>
      </div>
      <div>
        <h3 className="font-display text-h2 text-ink-primary">{product.name}</h3>
        <p className="text-label text-ink-muted">via {product.provider}</p>
      </div>
      <div className="mt-auto flex items-end justify-between">
        <div>
          <PPAmount value={product.pp} size="md" />
          <p className="text-label text-ink-muted">{product.fiat}</p>
        </div>
        <Button size="sm" onClick={onRedeem}>
          Redeem
        </Button>
      </div>
    </Card>
  );
}

function RedeemFlow({
  product,
  step,
  balance,
  inputValue,
  setInputValue,
  voucher,
  onConfirm,
  onSubmitInput,
  onClose,
}: {
  product: Product;
  step: Step;
  balance: number;
  inputValue: string;
  setInputValue: (v: string) => void;
  voucher: string;
  onConfirm: () => void;
  onSubmitInput: () => void;
  onClose: () => void;
}) {
  const after = balance - product.pp;
  const insufficient = after < 0;
  const inputLabel = INPUT_LABEL[product.input];

  if (step === 'confirm') {
    return (
      <div className="space-y-lg">
        <Row label="Item" value={product.name} />
        <Row
          label="Cost"
          value={<PPAmount value={product.pp} size="sm" />}
        />
        <Row label="Current balance" value={`${balance.toLocaleString('en-US')} PP`} />
        <Row
          label="Balance after"
          value={
            <span className={insufficient ? 'text-danger' : 'text-ink-primary'}>
              {after.toLocaleString('en-US')} PP
            </span>
          }
        />
        {insufficient && (
          <p className="rounded-card bg-danger/10 px-md py-sm text-label text-danger">
            You need {Math.abs(after).toLocaleString('en-US')} more PP to redeem this.
          </p>
        )}
        <Button className="w-full" onClick={onConfirm} disabled={insufficient}>
          Confirm
        </Button>
      </div>
    );
  }

  if (step === 'input') {
    return (
      <div className="space-y-lg">
        <p className="text-body text-ink-muted">
          Enter where we should deliver <strong className="text-ink-primary">{product.name}</strong>.
        </p>
        <Input
          label={inputLabel ?? 'Details'}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder={
            product.input === 'phone'
              ? '+234 800 000 0000'
              : product.input === 'email'
                ? 'you@example.com'
                : product.input === 'meter'
                  ? 'Meter number'
                  : 'Smartcard / IUC number'
          }
        />
        <Button className="w-full" onClick={onSubmitInput}>
          Pay {product.pp.toLocaleString('en-US')} PP
        </Button>
      </div>
    );
  }

  if (step === 'processing') {
    return (
      <div className="flex flex-col items-center gap-lg py-lg text-center">
        <div className="relative">
          <PandaMascot size={96} />
          <Loader2 className="absolute -right-1 -top-1 h-7 w-7 animate-spin text-brand-cobalt" />
        </div>
        <p className="text-body text-ink-muted">Processing your redemption…</p>
      </div>
    );
  }

  // success
  return (
    <div className="space-y-lg text-center">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-success/15">
        <Check className="h-8 w-8 text-success" />
      </div>
      <div>
        <h2 className="font-display text-h2 text-ink-primary">Redemption complete</h2>
        <p className="mt-1 text-body text-ink-muted">
          {product.name} is on its way. Your voucher / reference:
        </p>
      </div>
      <div className="flex items-center justify-between gap-sm rounded-card border border-line bg-bg-surface px-md py-sm">
        <code className="font-mono text-body text-ink-primary">{voucher}</code>
        <button
          onClick={() => {
            navigator.clipboard?.writeText(voucher);
            toast.success('Code copied!');
          }}
          className="inline-flex items-center gap-1 text-label font-medium text-brand-cobalt"
        >
          <Copy className="h-4 w-4" /> Copy
        </button>
      </div>
      <Button className="w-full" onClick={onClose}>
        Done
      </Button>
    </div>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b border-line pb-sm text-body">
      <span className="text-ink-muted">{label}</span>
      <span className="font-medium text-ink-primary">{value}</span>
    </div>
  );
}
