'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { Target, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { Button, PPAmount, Skeleton, EmptyState, Badge, cn } from '@meta-jungle/ui';
import { metajungleAPI, type ApiQuest } from '@/api/metajungle';

const CATEGORY_TONE: Record<string, 'cobalt' | 'sky' | 'gold' | 'success' | 'amber' | 'neutral'> = {
  daily: 'amber',
  social: 'sky',
  partner: 'cobalt',
  nft: 'gold',
  learning: 'success',
  referral: 'cobalt',
};

export default function QuestsPage() {
  const queryClient = useQueryClient();
  const [completing, setCompleting] = useState<string | null>(null);

  const { data: quests, isLoading } = useQuery<ApiQuest[]>('mjQuests', metajungleAPI.listQuests, {
    retry: false,
  });

  const complete = async (q: ApiQuest) => {
    setCompleting(q.id);
    try {
      const res = await metajungleAPI.completeQuest(q.id);
      toast.success(`Quest complete! +${res.pp_awarded} PP`);
      queryClient.invalidateQueries('pointsHistory');
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Could not complete quest');
    } finally {
      setCompleting(null);
    }
  };

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Quests</h1>
        <p className="mt-1 text-body text-ink-muted">
          Complete verified actions to earn Panda Points.
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-lg">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      ) : quests && quests.length > 0 ? (
        <div className="space-y-lg">
          {quests.map((q) => (
            <div
              key={q.id}
              className="overflow-hidden rounded-card border border-line border-l-4 border-l-brand-cobalt bg-bg-primary p-lg shadow-card transition-shadow hover:shadow-card-hover"
            >
              <div className="flex items-start justify-between gap-md">
                <div className="min-w-0 flex-1">
                  <div className="mb-1 flex items-center gap-sm">
                    <h3 className="font-display text-h2 text-ink-primary">{q.title}</h3>
                    <Badge tone={CATEGORY_TONE[q.category] ?? 'neutral'} className="capitalize">
                      {q.category}
                    </Badge>
                  </div>
                  <p className="text-body text-ink-muted">{q.description}</p>
                </div>
                <PPAmount value={q.pp_reward} size="sm" className="shrink-0" />
              </div>
              <div className="mt-lg flex items-center justify-between">
                <span className="text-label text-ink-muted">
                  Verify: <span className="capitalize">{q.verification_type.replace('_', ' ')}</span>
                  {q.daily_limit > 1 && ` · ${q.daily_limit}×/day`}
                </span>
                <Button size="sm" onClick={() => complete(q)} disabled={completing === q.id}>
                  {completing === q.id ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" /> Claiming…
                    </>
                  ) : (
                    'Complete'
                  )}
                </Button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          title="No quests available"
          description="New quests appear here as they go live. Check back soon to start earning."
          icon={<Target className="h-12 w-12 text-brand-cobalt" />}
        />
      )}
    </div>
  );
}
