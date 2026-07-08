'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { Plus } from 'lucide-react';
import { toast } from 'sonner';
import {
  P2POrderCard,
  Button,
  Input,
  Modal,
  Badge,
  cn,
} from '@meta-jungle/ui';
import { metajungleAPI, type ApiP2POrder } from '@/api/metajungle';

interface Order {
  id: string;
  trader: string;
  verified: boolean;
  reputation: number;
  ppAmount: number;
  price: string;
  methods: string[];
  postedAgo: string;
  side: 'buy' | 'sell';
}

function fromApi(o: ApiP2POrder): Order {
  const sym = o.currency === 'NGN' ? '₦' : o.currency === 'USD' ? '$' : '';
  return {
    id: o.id,
    trader: `Trader ${o.id.slice(0, 4)}`,
    verified: false,
    reputation: 4,
    ppAmount: o.pp_amount,
    price: `${sym}${Number(o.price).toLocaleString()}`,
    methods: o.payment_method ? o.payment_method.split(',').map((m) => m.trim()) : [],
    postedAgo: new Date(o.created_at).toLocaleDateString(),
    side: o.side,
  };
}

export default function P2PPage() {
  const queryClient = useQueryClient();
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({ pp_amount: '', price: '', payment_method: '' });
  const [posting, setPosting] = useState(false);

  // Buy tab shows sell-side orders (traders selling PP) and vice versa.
  const apiSide = side === 'buy' ? 'sell' : 'buy';
  const { data: apiOrders, isLoading } = useQuery(['mjOrders', apiSide], () => metajungleAPI.listOrders(apiSide), {
    retry: false,
  });
  const list: Order[] = apiOrders ? apiOrders.map(fromApi) : [];

  const postOrder = async () => {
    const pp = parseInt(form.pp_amount, 10);
    const price = parseFloat(form.price);
    if (!pp || !price || !form.payment_method.trim()) {
      toast.error('Fill in amount, price and payment method');
      return;
    }
    setPosting(true);
    try {
      await metajungleAPI.createOrder({
        side,
        pp_amount: pp,
        price,
        currency: 'NGN',
        payment_method: form.payment_method,
      });
      toast.success('Order posted to the P2P book');
      queryClient.invalidateQueries(['mjOrders']);
      queryClient.invalidateQueries('pointsHistory');
      setCreateOpen(false);
      setForm({ pp_amount: '', price: '', payment_method: '' });
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Could not post order');
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className="animate-page-in space-y-xl">
      <div className="flex flex-wrap items-start justify-between gap-md">
        <div>
          <h1 className="font-display text-h1 text-ink-primary">P2P Trade</h1>
          <p className="mt-1 text-body text-ink-muted">
            Buy and sell Panda Points peer-to-peer with on-chain escrow.
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4" /> Create Order
        </Button>
      </div>

      {/* Escrow trust banner */}
      <div className="flex items-center gap-sm rounded-card border border-line-blue bg-bg-elevated px-md py-sm">
        <Badge tone="cobalt">🔒 Escrow protected</Badge>
        <span className="text-label text-ink-muted">
          PP is locked in smart-contract escrow until both sides confirm. 1.5% trade fee.
        </span>
      </div>

      {/* Buy / Sell toggle */}
      <div className="inline-flex rounded-pill border border-line bg-bg-primary p-1">
        {(['buy', 'sell'] as const).map((s) => (
          <button
            key={s}
            onClick={() => setSide(s)}
            className={cn(
              'rounded-pill px-lg py-sm text-label font-medium capitalize transition-colors',
              side === s ? 'bg-brand-cobalt text-ink-inverse' : 'text-ink-muted hover:text-ink-primary',
            )}
          >
            {s} PP
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="grid gap-lg sm:grid-cols-2">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-48 animate-pulse rounded-card bg-bg-elevated" />
          ))}
        </div>
      ) : list.length === 0 ? (
        <div className="rounded-card border border-line bg-bg-primary p-xl text-center text-ink-muted">
          No {apiSide} orders available. Create one to get started!
        </div>
      ) : (
        <div className="grid gap-lg sm:grid-cols-2">
          {list.map((o) => (
            <P2POrderCard
              key={o.id}
              trader={o.trader}
              verified={o.verified}
              reputation={o.reputation}
              ppAmount={o.ppAmount}
              price={o.price}
              paymentMethods={o.methods}
              postedAgo={o.postedAgo}
              onTrade={() => toast.success(`Trade request sent to ${o.trader}`)}
            />
          ))}
        </div>
      )}

      <Modal open={createOpen} onClose={() => setCreateOpen(false)} title="Create P2P order">
        <div className="space-y-lg">
          <div className="inline-flex w-full rounded-pill border border-line bg-bg-primary p-1">
            {(['buy', 'sell'] as const).map((s) => (
              <button
                key={s}
                onClick={() => setSide(s)}
                className={cn(
                  'flex-1 rounded-pill py-sm text-label font-medium capitalize transition-colors',
                  side === s ? 'bg-brand-cobalt text-ink-inverse' : 'text-ink-muted',
                )}
              >
                {s}
              </button>
            ))}
          </div>
          <Input
            label="PP amount"
            type="number"
            placeholder="5000"
            value={form.pp_amount}
            onChange={(e) => setForm({ ...form, pp_amount: e.target.value })}
          />
          <Input
            label="Total price"
            placeholder="9250"
            value={form.price}
            onChange={(e) => setForm({ ...form, price: e.target.value })}
          />
          <Input
            label="Payment method"
            placeholder="Bank transfer, OPay…"
            value={form.payment_method}
            onChange={(e) => setForm({ ...form, payment_method: e.target.value })}
          />
          <p className="text-label text-ink-muted">A 50 PP listing fee applies (refunded on completion).</p>
          <Button className="w-full" onClick={postOrder} disabled={posting}>
            {posting ? 'Posting…' : 'Post Order'}
          </Button>
        </div>
      </Modal>
    </div>
  );
}
