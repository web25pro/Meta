'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { Check, X, ChevronLeft, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';
import { Card, Button, Badge, Skeleton, EmptyState, PPAmount, cn } from '@meta-jungle/ui';
import { adminAPI } from '@/api/admin';

const TABS = ['pending', 'approved', 'rejected'] as const;

export default function AdminReviewsPage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<(typeof TABS)[number]>('pending');
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery(
    ['adminCompletions', tab, page],
    () => adminAPI.listCompletions(tab, page),
    { retry: false },
  );

  const review = async (id: string, approve: boolean) => {
    try {
      await adminAPI.reviewCompletion(id, approve);
      toast.success(approve ? 'Approved' : 'Rejected');
      queryClient.invalidateQueries('adminCompletions');
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed');
    }
  };

  const items = data?.completions ?? [];
  const total = data?.total ?? 0;
  const pageSize = 20;
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Quest Reviews</h1>
        <p className="mt-1 text-body text-ink-muted">Approve or reject submitted quest completions.</p>
      </div>

      <div className="flex gap-sm">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => { setTab(t); setPage(1); }}
            className={cn(
              'rounded-pill px-md py-sm text-label font-medium capitalize transition-colors',
              tab === t
                ? 'bg-brand-cobalt text-ink-inverse'
                : 'border border-line bg-bg-primary text-ink-muted hover:bg-bg-elevated',
            )}
          >
            {t}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-sm">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-16" />)}</div>
      ) : items.length === 0 ? (
        <EmptyState title={`No ${tab} completions`} description="Submitted quest completions appear here for review." />
      ) : (
        <>
          <Card className="p-0">
            <div className="divide-y divide-line">
              {items.map((c: any) => (
                <div key={c.id} className="flex items-center justify-between gap-md px-lg py-md">
                  <div className="min-w-0">
                    <div className="font-medium text-ink-primary">
                      {c.quest_title || `Quest ${String(c.quest_id).slice(0, 8)}`}
                    </div>
                    <div className="mt-0.5 text-label text-ink-muted">
                      {c.user_name || c.user_email || `User ${String(c.user_id).slice(0, 8)}`}
                    </div>
                    <div className="mt-1 flex items-center gap-sm">
                      <PPAmount value={Math.round(c.pp_awarded)} size="sm" />
                      <Badge
                        tone={c.status === 'approved' ? 'success' : c.status === 'rejected' ? 'danger' : 'amber'}
                        className="capitalize"
                      >
                        {c.status}
                      </Badge>
                    </div>
                  </div>
                  {tab === 'pending' && (
                    <div className="flex items-center gap-sm">
                      <button onClick={() => review(c.id, true)} title="Approve"
                        className="inline-flex h-8 w-8 items-center justify-center rounded-card bg-success/10 text-success">
                        <Check className="h-4 w-4" />
                      </button>
                      <button onClick={() => review(c.id, false)} title="Reject"
                        className="inline-flex h-8 w-8 items-center justify-center rounded-card bg-danger/10 text-danger">
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Card>

          {/* Pagination controls */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <span className="text-label text-ink-muted">
                Page {page} of {totalPages} · {total} total
              </span>
              <div className="flex items-center gap-sm">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                >
                  <ChevronLeft className="h-4 w-4" /> Prev
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                >
                  Next <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
