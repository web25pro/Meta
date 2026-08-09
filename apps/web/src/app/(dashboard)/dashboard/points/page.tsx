'use client';

import { useQuery } from 'react-query';
import { useRouter } from 'next/navigation';
import { Lock } from 'lucide-react';
import {
  WalletBalanceCard,
  Card,
  Skeleton,
  EmptyState,
  cn,
} from '@meta-jungle/ui';
import apiClient from '@/lib/api';
import { PointsTransaction, PaginatedResponse, TransactionType } from '@/types';
import { format } from 'date-fns';

export default function PandaWalletPage() {
  const router = useRouter();
  // The balance comes from the server, not from summing a page of history —
  // that only ever added up the transactions on the current page.
  const { data: balance } = useQuery<{ points: number; rank?: number | null }>(
    'pointsBalance',
    async () => (await apiClient.get('/points/balance')).data,
  );

  const { data, isLoading } = useQuery<PaginatedResponse<PointsTransaction>>(
    'pointsHistory',
    async () => (await apiClient.get('/points/transactions')).data,
  );

  const totalPoints = balance?.points ?? 0;

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Panda Wallet</h1>
        <p className="mt-1 text-body text-ink-muted">
          Your Panda Points balance and earn history.
        </p>
      </div>

      {/*
        Only actions that actually go somewhere are rendered. Send/Receive
        need the wallet transfer API and Swap has no implementation, so they
        stay out until they work rather than sitting here doing nothing.
      */}
      <WalletBalanceCard
        ppBalance={totalPoints}
        actions={[
          { label: 'Stake', icon: <Lock className="h-4 w-4" />, onClick: () => router.push('/dashboard/staking') },
        ]}
      />

      <Card className="p-0">
        <div className="border-b border-line px-lg py-md">
          <h2 className="font-display text-h2 text-ink-primary">History</h2>
        </div>
        {isLoading ? (
          <div className="space-y-px">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="m-md h-14" />
            ))}
          </div>
        ) : data && data.items.length > 0 ? (
          <div className="divide-y divide-line">
            {data.items.map((t) => (
              <TransactionRow key={t.id} transaction={t} />
            ))}
          </div>
        ) : (
          <div className="p-lg">
            <EmptyState
              title="No transactions yet"
              description="Complete quests to start earning Panda Points."
            />
          </div>
        )}
      </Card>
    </div>
  );
}

const typeBadge: Record<TransactionType, string> = {
  [TransactionType.TASK_APPROVAL]: 'bg-success/10 text-success',
  [TransactionType.DEADLINE_PENALTY]: 'bg-danger/10 text-danger',
  [TransactionType.ADMIN_BONUS]: 'bg-brand-ice text-brand-cobalt',
  [TransactionType.ADMIN_PENALTY]: 'bg-reward-amber/10 text-reward-amber',
};

function TransactionRow({ transaction }: { transaction: PointsTransaction }) {
  const isPositive = transaction.amount > 0;
  return (
    <div className="flex items-center justify-between gap-md px-lg py-md transition-colors hover:bg-bg-surface">
      <div className="min-w-0 flex-1">
        <div className="mb-1 flex items-center gap-sm">
          <span
            className={cn(
              'rounded-pill px-sm py-[2px] text-label font-medium',
              typeBadge[transaction.transaction_type],
            )}
          >
            {transaction.transaction_type.replace(/_/g, ' ')}
          </span>
          <span className="text-label text-ink-muted">
            {format(new Date(transaction.created_at), 'MMM d, yyyy h:mm a')}
          </span>
        </div>
        <p className="truncate text-body text-ink-primary">{transaction.reason}</p>
      </div>
      <div
        className={cn(
          'shrink-0 font-display text-h2 tabular-nums',
          isPositive ? 'text-reward-gold' : 'text-danger',
        )}
      >
        {isPositive ? '+' : ''}
        {transaction.amount.toLocaleString('en-US')}
        <span className="ml-1 text-label font-sans">PP</span>
      </div>
    </div>
  );
}
