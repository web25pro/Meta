'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { toast } from 'sonner';
import { Clock, Users, Lock, Check } from 'lucide-react';
import {
  Card,
  Button,
  Badge,
  PPAmount,
  ProgressBar,
  Foliage,
  cn,
} from '@meta-jungle/ui';
import {
  metajungleAPI,
  type ApiCampaign,
  type ApiCampaignTask,
} from '@/api/metajungle';

/** Proof payload each verification type expects, mirroring the backend rules. */
function proofFor(task: ApiCampaignTask): Record<string, unknown> | undefined {
  switch (task.verification_type) {
    case 'oauth':
    case 'webhook':
      return { verified: true };
    case 'on_chain':
      return { tx_hash: window.prompt('Paste the transaction hash') ?? '' };
    case 'screenshot':
      return { screenshot_url: window.prompt('Paste a link to your screenshot') ?? '' };
    default:
      return { note: 'submitted for review' };
  }
}

function daysLeft(endsAt?: string | null): number | null {
  if (!endsAt) return null;
  return Math.max(0, Math.ceil((new Date(endsAt).getTime() - Date.now()) / 86400000));
}

function claimedPct(c: ApiCampaign): number {
  if (c.pp_budget <= 0) return 0;
  return Math.round(((c.pp_claimed + c.pp_reserved) / c.pp_budget) * 100);
}

function DeadlineBadge({ campaign }: { campaign: ApiCampaign }) {
  const d = daysLeft(campaign.ends_at);
  if (d === null) return <Badge tone="cobalt">Ongoing</Badge>;
  return (
    <Badge tone={d <= 3 ? 'amber' : 'cobalt'}>
      <Clock className="h-3 w-3" /> {d}d left
    </Badge>
  );
}

/** Task list for a joined campaign — the actual earn loop. */
function TaskList({ campaign }: { campaign: ApiCampaign }) {
  const queryClient = useQueryClient();
  const [busy, setBusy] = useState<string | null>(null);
  const { data: tasks, isLoading } = useQuery(
    ['mjCampaignTasks', campaign.id],
    () => metajungleAPI.listCampaignTasks(campaign.id),
    { retry: false },
  );

  const complete = async (task: ApiCampaignTask) => {
    setBusy(task.id);
    try {
      const result = await metajungleAPI.completeCampaignTask(
        campaign.id,
        task.id,
        proofFor(task),
      );
      if (result.status === 'approved') {
        toast.success(`+${result.pp_awarded} PP — ${task.title}`);
      } else {
        toast.success(`Submitted for review — ${task.title}`);
      }
      queryClient.invalidateQueries(['mjCampaignTasks', campaign.id]);
      queryClient.invalidateQueries('mjCampaigns');
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Could not complete this task');
    } finally {
      setBusy(null);
    }
  };

  if (isLoading) {
    return <div className="h-16 animate-pulse rounded-card bg-bg-elevated" />;
  }
  if (!tasks?.length) {
    return <p className="text-label text-ink-muted">No tasks in this campaign yet.</p>;
  }

  return (
    <ul className="space-y-sm">
      {tasks.map((task) => (
        <li
          key={task.id}
          className="flex items-center justify-between gap-md rounded-card bg-bg-elevated px-md py-sm"
        >
          <div className="min-w-0">
            <p className="truncate text-body text-ink-primary">{task.title}</p>
            {task.description && (
              <p className="truncate text-label text-ink-muted">{task.description}</p>
            )}
          </div>
          <div className="flex shrink-0 items-center gap-sm">
            <PPAmount value={task.pp_reward} size="sm" />
            {task.can_complete ? (
              <Button size="sm" disabled={busy === task.id} onClick={() => complete(task)}>
                {busy === task.id ? '…' : 'Complete'}
              </Button>
            ) : (
              <Badge tone="jungle">
                <Check className="h-3 w-3" /> Done today
              </Badge>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}

export default function CampaignsPage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery('mjCampaigns', metajungleAPI.listCampaigns, {
    retry: false,
  });
  const all = data ?? [];
  const featured = all.find((c) => c.featured);
  const rest = all.filter((c) => !c.featured);

  const join = async (c: ApiCampaign) => {
    try {
      await metajungleAPI.joinCampaign(c.id);
      toast.success(`Joined ${c.brand || 'campaign'}`);
      queryClient.invalidateQueries('mjCampaigns');
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Could not join this campaign');
    }
  };

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Campaigns</h1>
        <p className="mt-1 text-body text-ink-muted">
          Brand-sponsored campaigns with big Panda Point pools.
        </p>
      </div>

      {/* Featured spotlight — navy gradient */}
      {featured && (
        <div className="relative overflow-hidden rounded-card bg-hero-gradient p-xl text-ink-inverse">
          <div className="bamboo-texture pointer-events-none absolute inset-0 opacity-40" />
          <Foliage />
          <div className="relative space-y-md">
            <div className="flex items-center gap-sm">
              <span className="rounded-pill bg-white/15 px-sm py-[2px] text-label">
                {featured.brand}
              </span>
              <Badge tone="gold">Featured</Badge>
            </div>
            <h2 className="font-display text-h1">{featured.title}</h2>
            <p className="max-w-lg text-brand-ice">{featured.blurb}</p>
            <div className="flex flex-wrap items-center gap-lg pt-sm">
              <div>
                <p className="text-label text-brand-ice">Reward pool</p>
                <p className="font-display text-h1 text-reward-gold">
                  {featured.pp_budget.toLocaleString('en-US')}
                  <span className="ml-1 text-label">PP</span>
                </p>
              </div>
              <div>
                <p className="text-label text-brand-ice">Still available</p>
                <p className="font-display text-h2">
                  {featured.pp_available.toLocaleString('en-US')} PP
                </p>
              </div>
              {daysLeft(featured.ends_at) !== null && (
                <div className="flex items-center gap-sm text-label text-brand-ice">
                  <Clock className="h-4 w-4" /> {daysLeft(featured.ends_at)} days left
                </div>
              )}
            </div>
            {featured.joined ? (
              <div className="rounded-card bg-white/10 p-md">
                <TaskList campaign={featured} />
              </div>
            ) : (
              <Button variant="gold" onClick={() => join(featured)}>
                Join Campaign
              </Button>
            )}
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="grid gap-lg sm:grid-cols-2">
          {[0, 1].map((i) => (
            <Card key={i} className="h-64 animate-pulse bg-bg-elevated" />
          ))}
        </div>
      ) : rest.length === 0 && !featured ? (
        <Card className="p-xl text-center text-ink-muted">
          No campaigns available right now. Check back soon!
        </Card>
      ) : (
        <div className="grid gap-lg sm:grid-cols-2">
          {rest.map((c) => {
            const pct = claimedPct(c);
            return (
              <Card key={c.id} className="flex flex-col gap-md">
                <div className="flex items-center justify-between">
                  <span className="font-display text-h2 text-ink-primary">{c.brand}</span>
                  <DeadlineBadge campaign={c} />
                </div>
                <div>
                  <h3 className="text-body font-medium text-ink-primary">{c.title}</h3>
                  <p className="text-label text-ink-muted">{c.blurb}</p>
                </div>

                {c.target_regions.length > 0 && (
                  <p className="flex items-center gap-1 text-label text-ink-muted">
                    <Lock className="h-3 w-3" /> {c.target_regions.join(', ')} only
                  </p>
                )}

                <div className="space-y-1">
                  <div className="flex justify-between text-label text-ink-muted">
                    <span>Pool {pct}% claimed</span>
                    <span className="flex items-center gap-1">
                      <Users className="h-3 w-3" />
                      {c.total_participants.toLocaleString('en-US')}
                      {c.max_participants ? ` / ${c.max_participants.toLocaleString('en-US')}` : ''}
                    </span>
                  </div>
                  <ProgressBar value={pct} tone={pct > 80 ? 'gold' : 'jungle'} />
                </div>

                {c.joined ? (
                  <TaskList campaign={c} />
                ) : (
                  <div className="mt-auto flex items-center justify-between">
                    <PPAmount value={c.pp_per_task} size="sm" />
                    <Button size="sm" onClick={() => join(c)}>
                      Join
                    </Button>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
