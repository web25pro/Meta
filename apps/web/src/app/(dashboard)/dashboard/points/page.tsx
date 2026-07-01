'use client';

import { useQuery } from 'react-query';
import { Send, Download, Repeat, Lock } from 'lucide-react';
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
  const { data, isLoading } = useQuery<PaginatedResponse<PointsTransaction>>(
    'pointsHistory',
    async () => (await apiClient.get('/points/transactions')).data,
  );

  const totalPoints = data?.items.reduce((sum, t) => sum + t.amount, 0) || 0;

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Panda Wallet</h1>
        <p className="mt-1 text-body text-ink-muted">
          Your Panda Points balance and earn history.
        </p>
      </div>

      <WalletBalanceCard
        ppBalance={totalPoints}
        actions={[
          { label: 'Send', icon: <Send className="h-4 w-4" /> },
          { label: 'Receive', icon: <Download className="h-4 w-4" /> },
          { label: 'Swap', icon: <Repeat className="h-4 w-4" /> },
          { label: 'Stake', icon: <Lock className="h-4 w-4" /> },
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
