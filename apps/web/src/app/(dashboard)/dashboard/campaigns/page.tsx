'use client';

import { useEffect, useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { toast } from 'sonner';
import { Clock, Users, Lock, Check, ChevronLeft, ChevronRight, ExternalLink } from 'lucide-react';
import {
  Card,
  Button,
  Badge,
  PPAmount,
  ProgressBar,
  Foliage,
  Modal,
  Input,
  cn,
} from '@meta-jungle/ui';
import {
  metajungleAPI,
  type ApiCampaign,
  type ApiCampaignTask,
} from '@/api/metajungle';
import { fileToDataUrl, validateScreenshotFile } from '@/lib/screenshot-proof';

/**
 * Proof payload each verification type expects, mirroring the backend rules.
 *
 * oauth/webhook send nothing: the browser never asserts that the action
 * happened. Those tasks submit and wait for review like the rest.
 */
function proofFor(task: ApiCampaignTask): Record<string, unknown> | undefined {
  switch (task.verification_type) {
    case 'oauth':
    case 'webhook':
      return {};
    case 'on_chain':
      return { tx_hash: window.prompt('Paste the transaction hash') ?? '' };
    case 'screenshot':
      return {};
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

const TIER_RANK: Record<string, number> = { platinum: 0, gold: 1, silver: 2, bronze: 3 };

function tierLabel(tier?: string | null): string {
  return tier ? `${tier.charAt(0).toUpperCase()}${tier.slice(1)} partner` : 'Featured partner';
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
  const [proofTask, setProofTask] = useState<ApiCampaignTask | null>(null);
  const [proofInput, setProofInput] = useState('');
  const [proofFile, setProofFile] = useState<File | null>(null);
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

  const submitScreenshotProof = async () => {
    if (!proofTask) return;
    const proof: Record<string, unknown> = {};
    if (proofInput.trim()) proof.proof_url = proofInput.trim();
    if (proofFile) proof.screenshot_image = await fileToDataUrl(proofFile);
    if (proofTask.link_required && !proofInput.trim()) {
      toast.error('Paste the link showing the completed task');
      return;
    }
    if (proofTask.screenshot_required && !proofFile) {
      toast.error('Upload a screenshot showing the completed task');
      return;
    }
    if (proofTask.verification_type === 'screenshot' && !proofInput.trim() && !proofFile) {
      toast.error('Upload a screenshot or paste a completion link');
      return;
    }
    setProofTask(null);
    setProofInput('');
    setProofFile(null);
    await completeWithProof(proofTask, proof);
  };

  const completeWithProof = async (task: ApiCampaignTask, proof: Record<string, unknown>) => {
    setBusy(task.id);
    try {
      const result = await metajungleAPI.completeCampaignTask(campaign.id, task.id, proof);
      toast.success(result.status === 'approved'
        ? `+${result.pp_awarded} PP — ${task.title}`
        : `Submitted for review — ${task.title}`);
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
    <>
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
            {task.action_url && (
              <a href={task.action_url} target="_blank" rel="noopener noreferrer" className="mt-1 inline-flex items-center gap-1 text-label font-medium text-brand-cobalt hover:underline">
                <ExternalLink className="h-3 w-3" /> Open task link
              </a>
            )}
          </div>
          <div className="flex shrink-0 items-center gap-sm">
            <PPAmount value={task.pp_reward} size="sm" />
            {campaign.status === 'active' && task.can_complete ? (
              <Button
                size="sm"
                disabled={busy === task.id}
                onClick={() => {
                  if (task.verification_type === 'screenshot' || task.screenshot_required || task.link_required) {
                    setProofTask(task);
                    setProofInput('');
                    setProofFile(null);
                  } else {
                    complete(task);
                  }
                }}
              >
                {busy === task.id ? '…' : 'Complete'}
              </Button>
            ) : campaign.status === 'ended' ? (
              <Badge tone="neutral">Campaign ended</Badge>
            ) : (
              <Badge tone="jungle">
                <Check className="h-3 w-3" /> Done today
              </Badge>
            )}
          </div>
        </li>
      ))}
      </ul>
      <Modal
      open={!!proofTask}
      onClose={() => setProofTask(null)}
      title={proofTask ? `Complete: ${proofTask.title}` : 'Submit screenshot'}
    >
      <div className="space-y-md">
        <Input
          label={`Completion link ${proofTask?.link_required ? '(required)' : '(optional)'}`}
          placeholder="https://..."
          value={proofInput}
          onChange={(e) => setProofInput(e.target.value)}
        />
        <div>
          <label className="mb-1 block text-label font-medium text-ink-primary">
            Upload screenshot {proofTask?.screenshot_required ? '(required)' : '(optional)'}
          </label>
          <input
            type="file"
            accept="image/png,image/jpeg,image/gif,image/webp"
            onChange={(e) => {
              const file = e.target.files?.[0] ?? null;
              if (!file) return setProofFile(null);
              const error = validateScreenshotFile(file);
              if (error) {
                toast.error(error);
                e.currentTarget.value = '';
                return setProofFile(null);
              }
              setProofFile(file);
            }}
            className="block w-full rounded-card border border-line bg-bg-primary px-md py-sm text-label text-ink-muted"
          />
          {proofFile && <p className="mt-1 text-label text-ink-muted">Attached: {proofFile.name}</p>}
        </div>
        <p className="text-label text-ink-muted">
          {proofTask?.link_required || proofTask?.screenshot_required
            ? 'Provide the evidence marked required above. Optional evidence can also be added.'
            : 'Attach an image, paste a link, provide both, or submit without an attachment.'}
        </p>
        <div className="flex gap-sm">
          <Button variant="ghost" className="flex-1" onClick={() => setProofTask(null)}>Cancel</Button>
          <Button className="flex-1" disabled={busy === proofTask?.id} onClick={submitScreenshotProof}>
            Submit
          </Button>
        </div>
      </div>
      </Modal>
    </>
  );
}

function FeaturedCarousel({
  campaigns,
  onJoin,
  onWithdraw,
}: {
  campaigns: ApiCampaign[];
  onJoin: (campaign: ApiCampaign) => void;
  onWithdraw: (campaign: ApiCampaign) => void;
}) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (index >= campaigns.length) setIndex(0);
  }, [campaigns.length, index]);

  useEffect(() => {
    if (campaigns.length < 2) return;
    const timer = window.setInterval(() => setIndex((current) => (current + 1) % campaigns.length), 6000);
    return () => window.clearInterval(timer);
  }, [campaigns.length]);

  return (
    <section className="space-y-sm">
      <div className="relative overflow-hidden rounded-card bg-hero-gradient text-ink-inverse">
        <div className="flex transition-transform duration-700 ease-out" style={{ transform: `translateX(-${index * 100}%)` }}>
          {campaigns.map((campaign) => (
            <div key={campaign.id} className="relative min-w-full p-xl">
              <div className="bamboo-texture pointer-events-none absolute inset-0 opacity-40" />
              <Foliage />
              <div className="relative space-y-md">
                <div className="flex items-center gap-sm"><span className="rounded-pill bg-white/15 px-sm py-[2px] text-label">{campaign.brand}</span><Badge tone="gold">{tierLabel(campaign.partner_tier)}</Badge></div>
                <h2 className="font-display text-h1">{campaign.title}</h2>
                <p className="max-w-lg text-brand-ice">{campaign.blurb}</p>
                <div className="flex flex-wrap items-center gap-lg pt-sm"><div><p className="text-label text-brand-ice">Reward pool</p><p className="font-display text-h1 text-reward-gold">{campaign.pp_budget.toLocaleString('en-US')}<span className="ml-1 text-label">PP</span></p></div><div><p className="text-label text-brand-ice">Still available</p><p className="font-display text-h2">{campaign.pp_available.toLocaleString('en-US')} PP</p></div>{daysLeft(campaign.ends_at) !== null && <div className="flex items-center gap-sm text-label text-brand-ice"><Clock className="h-4 w-4" /> {daysLeft(campaign.ends_at)} days left</div>}</div>
                {campaign.joined ? <div className="rounded-card bg-white/10 p-md">{campaign.status === 'ended' && campaign.my_pp_available > 0 && <div className="mb-md flex items-center justify-between gap-md rounded-card bg-white/10 p-md"><span className="text-label">Available to withdraw: {campaign.my_pp_available.toLocaleString('en-US')} PP</span><Button variant="gold" size="sm" onClick={() => onWithdraw(campaign)}>Withdraw PP</Button></div>}<TaskList campaign={campaign} /></div> : <Button variant="gold" onClick={() => onJoin(campaign)}>Join Campaign</Button>}
              </div>
            </div>
          ))}
        </div>
        {campaigns.length > 1 && <><button aria-label="Previous featured campaign" onClick={() => setIndex((index - 1 + campaigns.length) % campaigns.length)} className="absolute left-md top-1/2 rounded-full bg-black/20 p-sm text-white hover:bg-black/40"><ChevronLeft className="h-5 w-5" /></button><button aria-label="Next featured campaign" onClick={() => setIndex((index + 1) % campaigns.length)} className="absolute right-md top-1/2 rounded-full bg-black/20 p-sm text-white hover:bg-black/40"><ChevronRight className="h-5 w-5" /></button></>}
      </div>
      {campaigns.length > 1 && <div className="flex justify-center gap-1.5" aria-label="Featured campaign slides">{campaigns.map((campaign, slide) => <button key={campaign.id} aria-label={`Show ${campaign.title}`} onClick={() => setIndex(slide)} className={cn('h-1.5 rounded-pill transition-all', slide === index ? 'w-6 bg-brand-cobalt' : 'w-1.5 bg-line')} />)}</div>}
    </section>
  );
}

export default function CampaignsPage() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery('mjCampaigns', metajungleAPI.listCampaigns, {
    retry: false,
  });
  const all = data ?? [];
  const featuredCampaigns = all
    .filter((c) => c.featured)
    .sort((a, b) => (TIER_RANK[a.partner_tier ?? 'bronze'] ?? 3) - (TIER_RANK[b.partner_tier ?? 'bronze'] ?? 3));
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

  const withdraw = async (c: ApiCampaign) => {
    try {
      const result = await metajungleAPI.withdrawCampaignPoints(c.id);
      toast.success(`${result.amount.toLocaleString('en-US')} PP moved to your main balance`);
      queryClient.invalidateQueries('mjCampaigns');
      queryClient.invalidateQueries('pointsHistory');
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Could not withdraw campaign PP');
    }
  };

  return (
    <div className="animate-page-in space-y-xl">
      {featuredCampaigns.length > 0 && <FeaturedCarousel campaigns={featuredCampaigns} onJoin={join} onWithdraw={withdraw} />}
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Campaigns</h1>
        <p className="mt-1 text-body text-ink-muted">
          Brand-sponsored campaigns with big Panda Point pools.
        </p>
      </div>

      {featuredCampaigns.length > 1 && (
        <section className="space-y-md">
          <div>
            <h2 className="font-display text-h2 text-ink-primary">Featured campaigns</h2>
            <p className="text-label text-ink-muted">Priority follows partner tier set by administrators.</p>
          </div>
          <div className="grid gap-md sm:grid-cols-2 lg:grid-cols-4">
            {featuredCampaigns.map((campaign) => (
              <Card key={campaign.id} className="space-y-sm border-t-4 border-t-reward-gold">
                <div className="flex items-center justify-between gap-sm"><Badge tone="gold">{tierLabel(campaign.partner_tier)}</Badge><span className="text-label text-ink-muted">{campaign.brand}</span></div>
                <h3 className="font-display text-body text-ink-primary">{campaign.title}</h3>
                <p className="line-clamp-2 text-label text-ink-muted">{campaign.blurb}</p>
                <div className="flex items-center justify-between"><PPAmount value={campaign.pp_per_task} size="sm" />{campaign.joined ? <Badge tone="success">Joined</Badge> : <Button size="sm" onClick={() => join(campaign)}>Join</Button>}</div>
              </Card>
            ))}
          </div>
        </section>
      )}

      {isLoading ? (
        <div className="grid gap-lg sm:grid-cols-2">
          {[0, 1].map((i) => (
            <Card key={i} className="h-64 animate-pulse bg-bg-elevated" />
          ))}
        </div>
      ) : rest.length === 0 && featuredCampaigns.length === 0 ? (
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
                  <>
                    {c.status === 'ended' && c.my_pp_available > 0 && (
                      <div className="flex items-center justify-between gap-md rounded-card bg-bg-elevated p-md">
                        <span className="text-label text-ink-muted">Available after campaign: {c.my_pp_available.toLocaleString('en-US')} PP</span>
                        <Button size="sm" onClick={() => withdraw(c)}>Withdraw PP</Button>
                      </div>
                    )}
                    <TaskList campaign={c} />
                  </>
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
