'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { ArrowDownUp, Loader2, History, AlertCircle } from 'lucide-react';
import { cn, Card, Button, Skeleton, EmptyState } from '@meta-jungle/ui';
import { swapAPI, SwapQuote, SwapHistory } from '@/api/swap';
import { toast } from 'sonner';

export default function SwapPage() {
  const queryClient = useQueryClient();
  const [amount, setAmount] = useState('');
  const [direction, setDirection] = useState<'pp_to_token' | 'token_to_pp'>('pp_to_token');
  const [quote, setQuote] = useState<SwapQuote | null>(null);
  const [quoteLoading, setQuoteLoading] = useState(false);

  const { data: history, isLoading: historyLoading } = useQuery<SwapHistory>(
    'swapHistory',
    () => swapAPI.getHistory(),
    { staleTime: 30_000 },
  );

  // Fetch quote when amount changes (debounced)
  useEffect(() => {
    const ppAmount = parseFloat(amount);
    if (!ppAmount || ppAmount <= 0) {
      setQuote(null);
      return;
    }

    const timer = setTimeout(async () => {
      setQuoteLoading(true);
      try {
        const q = await swapAPI.getQuote(ppAmount, direction);
        setQuote(q);
      } catch {
        setQuote(null);
      } finally {
        setQuoteLoading(false);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [amount, direction]);

  const swapMutation = useMutation(
    () => swapAPI.executeSwap(parseFloat(amount), direction),
    {
      onSuccess: (data) => {
        toast.success(`Swapped ${data.pp_amount} PP for ${data.token_amount} tokens!`);
        setAmount('');
        setQuote(null);
        queryClient.invalidateQueries('swapHistory');
        queryClient.invalidateQueries('membershipStatus');
        queryClient.invalidateQueries('pointsBalance');
      },
      onError: (err: any) => {
        toast.error(err?.response?.data?.detail || 'Swap failed');
      },
    },
  );

  const toggleDirection = () => {
    setDirection(d => d === 'pp_to_token' ? 'token_to_pp' : 'pp_to_token');
    setQuote(null);
  };

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Swap</h1>
        <p className="text-body text-ink-muted">
          Convert between Panda Points and tokens.
        </p>
      </div>

      <div className="grid gap-lg lg:grid-cols-2">
        {/* Swap form */}
        <Card className="p-lg space-y-lg">
          <h2 className="font-display text-h2 text-ink-primary">Convert</h2>

          {/* Direction toggle */}
          <div className="flex items-center gap-md">
            <div className="flex-1 rounded-card bg-bg-elevated p-md text-center">
              <p className="text-caption text-ink-muted">
                {direction === 'pp_to_token' ? 'You Pay' : 'You Receive'}
              </p>
              <p className="font-display text-h3 text-ink-primary">
                {direction === 'pp_to_token' ? 'Panda Points' : 'Tokens'}
              </p>
            </div>

            <button
              onClick={toggleDirection}
              className="flex h-10 w-10 items-center justify-center rounded-full bg-bg-elevated text-ink-muted transition-colors hover:bg-brand-cobalt/10 hover:text-brand-cobalt"
            >
              <ArrowDownUp className="h-5 w-5" />
            </button>

            <div className="flex-1 rounded-card bg-bg-elevated p-md text-center">
              <p className="text-caption text-ink-muted">
                {direction === 'pp_to_token' ? 'You Receive' : 'You Pay'}
              </p>
              <p className="font-display text-h3 text-ink-primary">
                {direction === 'pp_to_token' ? 'Tokens' : 'Panda Points'}
              </p>
            </div>
          </div>

          {/* Amount input */}
          <div className="space-y-sm">
            <label className="text-label text-ink-muted">
              Amount ({direction === 'pp_to_token' ? 'PP' : 'Tokens'})
            </label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              min="10"
              step="1"
              className="w-full rounded-card border border-line bg-bg-primary px-lg py-md text-h2 text-ink-primary placeholder:text-ink-muted focus:border-brand-cobalt focus:outline-none"
            />
          </div>

          {/* Quote preview */}
          {quote && (
            <div className="space-y-sm rounded-card bg-bg-elevated p-md">
              <div className="flex justify-between text-body">
                <span className="text-ink-muted">Rate</span>
                <span className="text-ink-primary">{quote.rate} PP = 1 Token</span>
              </div>
              <div className="flex justify-between text-body">
                <span className="text-ink-muted">Fee ({quote.fee_percent}%)</span>
                <span className="text-ink-primary">{quote.fee_pp} PP</span>
              </div>
              <div className="border-t border-line pt-sm flex justify-between text-body font-medium">
                <span className="text-ink-muted">You receive</span>
                <span className="text-reward-jungle">{quote.token_amount} Tokens</span>
              </div>
            </div>
          )}

          {quoteLoading && (
            <div className="flex items-center gap-sm text-body text-ink-muted">
              <Loader2 className="h-4 w-4 animate-spin" />
              Getting quote...
            </div>
          )}

          {/* Execute button */}
          <Button
            variant="jungle"
            className="w-full"
            disabled={!quote || swapMutation.isLoading || parseFloat(amount) < 10}
            onClick={() => swapMutation.mutate()}
          >
            {swapMutation.isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <ArrowDownUp className="h-4 w-4" />
            )}
            <span>{swapMutation.isLoading ? 'Swapping...' : 'Swap'}</span>
          </Button>

          <p className="flex items-center gap-sm text-caption text-ink-muted">
            <AlertCircle className="h-3 w-3" />
            Minimum swap: 10 PP. Daily limit: 50,000 PP.
          </p>
        </Card>

        {/* Swap history */}
        <Card className="p-lg">
          <h2 className="mb-lg font-display text-h2 text-ink-primary">
            <History className="mr-sm inline h-5 w-5" />
            Swap History
          </h2>

          {historyLoading ? (
            <div className="space-y-sm">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : history && history.items.length > 0 ? (
            <div className="space-y-sm">
              {history.items.map((tx) => (
                <div
                  key={tx.id}
                  className="flex items-center justify-between rounded-card bg-bg-elevated p-md"
                >
                  <div>
                    <p className="text-body font-medium text-ink-primary">{tx.reason}</p>
                    <p className="text-caption text-ink-muted">
                      {tx.created_at ? new Date(tx.created_at).toLocaleString() : ''}
                    </p>
                  </div>
                  <span className={cn(
                    'font-display text-body',
                    tx.amount < 0 ? 'text-danger' : 'text-reward-jungle',
                  )}>
                    {tx.amount > 0 ? '+' : ''}{tx.amount} PP
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No swaps yet"
              description="Your swap transactions will appear here."
            />
          )}
        </Card>
      </div>
    </div>
  );
}
