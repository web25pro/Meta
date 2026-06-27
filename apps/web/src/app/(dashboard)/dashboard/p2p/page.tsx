'use client';

import { useState } from 'react';
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

const ORDERS: Order[] = [
  { id: '1', trader: 'panda_king', verified: true, reputation: 5, ppAmount: 10000, price: '₦18,500', methods: ['Bank', 'OPay'], postedAgo: '2m ago', side: 'sell' },
  { id: '2', trader: 'bamboo.eth', verified: true, reputation: 4, ppAmount: 5000, price: '₦9,400', methods: ['Bank'], postedAgo: '11m ago', side: 'sell' },
  { id: '3', trader: 'mistwalker', verified: false, reputation: 3, ppAmount: 2500, price: '$24.50', methods: ['Wise'], postedAgo: '34m ago', side: 'sell' },
  { id: '4', trader: 'cobalt_fox', verified: true, reputation: 5, ppAmount: 8000, price: '₦15,000', methods: ['Bank', 'Momo'], postedAgo: '1h ago', side: 'buy' },
  { id: '5', trader: 'ivory_paw', verified: true, reputation: 4, ppAmount: 3000, price: '$29.10', methods: ['PayPal'], postedAgo: '2h ago', side: 'buy' },
];

export default function P2PPage() {
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  const [createOpen, setCreateOpen] = useState(false);

  // On the Buy tab, show traders selling PP; on Sell, show traders buying PP.
  const list = ORDERS.filter((o) => (side === 'buy' ? o.side === 'sell' : o.side === 'buy'));

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
          <Input label="PP amount" type="number" placeholder="5000" />
          <Input label="Price per 1,000 PP" placeholder="₦1,850" />
          <Input label="Payment method" placeholder="Bank transfer, OPay…" />
          <p className="text-label text-ink-muted">A 50 PP listing fee applies (refunded on completion).</p>
          <Button
            className="w-full"
            onClick={() => {
              setCreateOpen(false);
              toast.success('Order posted to the P2P book');
            }}
          >
            Post Order
          </Button>
        </div>
      </Modal>
    </div>
  );
}
