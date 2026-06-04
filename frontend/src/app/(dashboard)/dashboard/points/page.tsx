'use client';

import { useQuery } from 'react-query';
import { TrendingUp, TrendingDown, DollarSign, Calendar } from 'lucide-react';
import apiClient from '@/lib/api';
import { PointsTransaction, PaginatedResponse, TransactionType } from '@/types';
import { format } from 'date-fns';

export default function PointsPage() {
  const { data, isLoading } = useQuery<PaginatedResponse<PointsTransaction>>(
    'pointsHistory',
    async () => {
      const response = await apiClient.get('/points/transactions');
      return response.data;
    }
  );

  const totalPoints = data?.items.reduce((sum, t) => sum + t.amount, 0) || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Points History</h1>
        <p className="text-gray-600 mt-1">Track your Panda Points transactions</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          icon={<DollarSign className="h-6 w-6" />}
          title="Total Points"
          value={totalPoints}
          color="bg-primary-500"
        />
        <StatCard
          icon={<TrendingUp className="h-6 w-6" />}
          title="Earned"
          value={data?.items.filter((t) => t.amount > 0).reduce((sum, t) => sum + t.amount, 0) || 0}
          color="bg-green-500"
        />
        <StatCard
          icon={<TrendingDown className="h-6 w-6" />}
          title="Penalties"
          value={Math.abs(data?.items.filter((t) => t.amount < 0).reduce((sum, t) => sum + t.amount, 0) || 0)}
          color="bg-red-500"
        />
      </div>

      {/* Transactions */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Transaction History</h2>
        </div>
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {data?.items.map((transaction) => (
              <TransactionRow key={transaction.id} transaction={transaction} />
            ))}
            {data?.items.length === 0 && (
              <div className="text-center py-12">
                <p className="text-gray-600">No transactions yet</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({
  icon,
  title,
  value,
  color,
}: {
  icon: React.ReactNode;
  title: string;
  value: number;
  color: string;
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <div className={`${color} p-3 rounded-lg text-white`}>{icon}</div>
      </div>
      <div className="text-3xl font-bold text-gray-900 mb-1">{value}</div>
      <div className="text-sm text-gray-600">{title}</div>
    </div>
  );
}

function TransactionRow({ transaction }: { transaction: PointsTransaction }) {
  const isPositive = transaction.amount > 0;
  const typeColors: Record<TransactionType, string> = {
    [TransactionType.TASK_APPROVAL]: 'bg-green-100 text-green-800',
    [TransactionType.DEADLINE_PENALTY]: 'bg-red-100 text-red-800',
    [TransactionType.ADMIN_BONUS]: 'bg-blue-100 text-blue-800',
    [TransactionType.ADMIN_PENALTY]: 'bg-orange-100 text-orange-800',
  };

  return (
    <div className="px-6 py-4 hover:bg-gray-50 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-1">
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                typeColors[transaction.transaction_type]
              }`}
            >
              {transaction.transaction_type.replace('_', ' ')}
            </span>
            <span className="text-sm text-gray-600">
              {format(new Date(transaction.created_at), 'MMM d, yyyy h:mm a')}
            </span>
          </div>
          <p className="text-gray-900">{transaction.reason}</p>
        </div>
        <div className="ml-4 text-right">
          <div
            className={`text-2xl font-bold ${
              isPositive ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {isPositive ? '+' : ''}
            {transaction.amount}
          </div>
          <div className="text-sm text-gray-600">PP</div>
        </div>
      </div>
    </div>
  );
}
