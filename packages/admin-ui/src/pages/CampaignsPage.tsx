'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { Plus, Pause, Play, ListChecks, Check, X, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { Card, Button, Input, Badge, Modal, Skeleton, PPAmount } from '@meta-jungle/ui';
import { adminAPI, type AdminCampaign, type AdminPartner, type AdminCampaignReviewItem } from '../api/admin';

/** Pending manual/screenshot completions, oldest first. */
function ReviewQueue() {
  const queryClient = useQueryClient();
  const [rejecting, setRejecting] = useState<AdminCampaignReviewItem | null>(null);
  const [reason, setReason] = useState('');
  const { data: queue, isLoading } = useQuery(
    'adminCampaignReviewQueue',
    adminAPI.campaignReviewQueue,
    { retry: false },
  );

  const review = async (id: string, approve: boolean, reviewReason?: string) => {
    try {
      await adminAPI.reviewCampaignCompletion(id, approve, reviewReason);
      toast.success(approve ? 'Approved — PP credited' : 'Rejected — budget released');
      queryClient.invalidateQueries('adminCampaignReviewQueue');
      queryClient.invalidateQueries('adminCampaigns');
      setRejecting(null);
      setReason('');
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed');
    }
  };

  if (isLoading) return <Skeleton className="h-20" />;
  if (!queue?.length) return null;

  return (
    <div className="space-y-md">
      <h2 className="font-display text-h2 text-ink-primary">
        Review queue <Badge tone="amber">{queue.length}</Badge>
      </h2>
      {queue.map((item) => (
        <Card key={item.id} className="flex items-center justify-between gap-md">
          <div className="min-w-0 flex-1">
            <p className="truncate text-ink-primary">
              <span className="font-medium">{item.username}</span> · {item.task_title}
            </p>
            <p className="mt-1 truncate text-label text-ink-muted">
              {item.campaign_title} · {item.pp_awarded} PP pending
              {item.proof ? ` · ${JSON.stringify(item.proof)}` : ''}
            </p>
          </div>
          <div className="flex shrink-0 gap-sm">
            <Button size="sm" onClick={() => review(item.id, true)}>
              <Check className="h-4 w-4" /> Approve
            </Button>
            <Button size="sm" variant="ghost" onClick={() => { setRejecting(item); setReason(''); }}>
              <X className="h-4 w-4" /> Reject
            </Button>
          </div>
        </Card>
      ))}
      <Modal open={!!rejecting} onClose={() => setRejecting(null)} title="Reject campaign submission">
        <div className="space-y-lg">
          <p className="text-body text-ink-muted">Give the participant a clear reason so they know what to fix.</p>
          <Input label="Reason" placeholder="The proof does not show the required action" value={reason} onChange={(e) => setReason(e.target.value)} />
          <div className="flex gap-sm">
            <Button variant="ghost" className="flex-1" onClick={() => setRejecting(null)}>Cancel</Button>
            <Button className="flex-1" disabled={!reason.trim() || !rejecting} onClick={() => rejecting && review(rejecting.id, false, reason.trim())}>Reject submission</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

/** Task editor for a single campaign. */
function TasksModal({ campaign, onClose }: { campaign: AdminCampaign; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    title: '',
    description: '',
    pp_reward: '',
    verification_type: 'manual',
    daily_limit: '1',
  });
  const { data: tasks } = useQuery(
    ['adminCampaignTasks', campaign.id],
    () => adminAPI.listCampaignTasks(campaign.id),
    { retry: false },
  );

  const create = async () => {
    const reward = parseInt(form.pp_reward, 10);
    if (!form.title.trim() || !reward) {
      toast.error('Title and PP reward are required');
      return;
    }
    try {
      await adminAPI.createCampaignTask(campaign.id, {
        title: form.title,
        description: form.description,
        pp_reward: reward,
        verification_type: form.verification_type,
        daily_limit: parseInt(form.daily_limit, 10) || 1,
      });
      toast.success('Task added');
      setForm({ title: '', description: '', pp_reward: '', verification_type: 'manual', daily_limit: '1' });
      queryClient.invalidateQueries(['adminCampaignTasks', campaign.id]);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed');
    }
  };

  return (
    <Modal open onClose={onClose} title={`Tasks · ${campaign.title}`}>
      <div className="space-y-lg">
        <div className="space-y-sm">
          {(tasks ?? []).map((t) => (
            <div
              key={t.id}
              className="flex items-center justify-between gap-md rounded-card bg-bg-elevated px-md py-sm"
            >
              <div className="min-w-0">
                <p className="truncate text-body text-ink-primary">{t.title}</p>
                <p className="text-label text-ink-muted">
                  {t.verification_type} · {t.daily_limit}/day
                </p>
              </div>
              <PPAmount value={t.pp_reward} size="sm" />
            </div>
          ))}
          {tasks?.length === 0 && (
            <p className="text-center text-label text-ink-muted">
              No tasks yet — users cannot earn until you add one.
            </p>
          )}
        </div>

        <div className="space-y-md border-t border-line pt-lg">
          <Input
            label="Task title"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
          />
          <Input
            label="Description"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
          <div className="grid grid-cols-3 gap-md">
            <Input
              label="PP reward"
              type="number"
              value={form.pp_reward}
              onChange={(e) => setForm({ ...form, pp_reward: e.target.value })}
            />
            <div>
              <label className="mb-2 block text-label font-medium text-ink-primary">Verify</label>
              <select
                value={form.verification_type}
                onChange={(e) => setForm({ ...form, verification_type: e.target.value })}
                className="w-full rounded-card border border-line bg-bg-primary px-md py-3 text-body text-ink-primary focus:outline-none focus:ring-2 focus:ring-brand-cobalt"
              >
                {['manual', 'screenshot', 'on_chain', 'oauth', 'webhook'].map((v) => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
            </div>
            <Input
              label="Daily limit"
              type="number"
              value={form.daily_limit}
              onChange={(e) => setForm({ ...form, daily_limit: e.target.value })}
            />
          </div>
          <Button className="w-full" onClick={create}>Add Task</Button>
        </div>
      </div>
    </Modal>
  );
}

export function CampaignsPage() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [partnerOpen, setPartnerOpen] = useState(false);
  const [form, setForm] = useState({ partner_id: '', title: '', blurb: '', pp_budget: '', pp_per_task: '', days: '14', featured: false });
  const [partnerName, setPartnerName] = useState('');
  const [tasksFor, setTasksFor] = useState<AdminCampaign | null>(null);

  const { data: campaigns, isLoading } = useQuery('adminCampaigns', adminAPI.listCampaigns, { retry: false });
  const { data: partners } = useQuery('adminPartners', adminAPI.listPartners, { retry: false });
  const refresh = () => {
    queryClient.invalidateQueries('adminCampaigns');
    queryClient.invalidateQueries('adminPartners');
  };

  const createPartner = async () => {
    if (!partnerName.trim()) return;
    try {
      await adminAPI.createPartner({ name: partnerName });
      toast.success('Partner created');
      setPartnerName('');
      setPartnerOpen(false);
      refresh();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed');
    }
  };

  const createCampaign = async () => {
    const budget = parseInt(form.pp_budget, 10);
    const perTask = parseInt(form.pp_per_task, 10);
    if (!form.partner_id || !form.title.trim() || !budget || !perTask) {
      toast.error('Partner, title, budget and per-task PP are required');
      return;
    }
    try {
      await adminAPI.createCampaign({
        partner_id: form.partner_id, title: form.title, blurb: form.blurb,
        pp_budget: budget, pp_per_task: perTask, featured: form.featured, days: parseInt(form.days, 10) || 14,
      });
      toast.success('Campaign created');
      setOpen(false);
      setForm({ partner_id: '', title: '', blurb: '', pp_budget: '', pp_per_task: '', days: '14', featured: false });
      refresh();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed');
    }
  };

  const toggleStatus = async (c: AdminCampaign) => {
    // draft/paused/ended → active; active → paused
    const next = c.status === 'active' ? 'paused' : 'active';
    try {
      await adminAPI.setCampaignStatus(c.id, next);
      toast.success(`Campaign ${next}`);
      refresh();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed');
    }
  };

  const endCampaign = async (c: AdminCampaign) => {
    try {
      await adminAPI.setCampaignStatus(c.id, 'ended');
      toast.success('Campaign ended');
      refresh();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed');
    }
  };

  const deleteCampaign = async (c: AdminCampaign) => {
    const held = c.pp_reserved > 0
      ? `\n\n${c.pp_reserved.toLocaleString('en-US')} PP is reserved for pending completions — those will be rejected and the budget released.`
      : '';
    if (!window.confirm(`Delete "${c.title}"?${held}\n\nIt disappears from the app. Already-approved PP stays credited.`)) {
      return;
    }
    try {
      const res = await adminAPI.deleteCampaign(c.id);
      toast.success(
        res.rejected_pending > 0
          ? `Campaign deleted — ${res.rejected_pending} pending completion(s) rejected`
          : 'Campaign deleted',
      );
      queryClient.invalidateQueries('adminCampaignReviewQueue');
      refresh();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed');
    }
  };

  return (
    <div className="animate-page-in space-y-xl">
      <div className="flex items-start justify-between gap-md">
        <div>
          <h1 className="font-display text-h1 text-ink-primary">Campaigns</h1>
          <p className="mt-1 text-body text-ink-muted">Partners and brand-sponsored campaigns.</p>
        </div>
        <div className="flex gap-sm">
          <Button variant="ghost" onClick={() => setPartnerOpen(true)}>New Partner</Button>
          <Button onClick={() => setOpen(true)}><Plus className="h-4 w-4" /> New Campaign</Button>
        </div>
      </div>

      <ReviewQueue />

      {isLoading || !campaigns ? (
        <div className="space-y-sm">{Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-20" />)}</div>
      ) : (
        <div className="space-y-md">
          {campaigns.map((c) => (
            <Card key={c.id} className="flex items-center justify-between gap-md">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-sm">
                  <span className="font-medium text-ink-primary">{c.brand}</span>
                  <span className="text-ink-muted">·</span>
                  <span className="truncate text-ink-primary">{c.title}</span>
                  {c.featured && <Badge tone="gold">Featured</Badge>}
                  <Badge tone={c.status === 'active' ? 'success' : 'neutral'} className="capitalize">{c.status}</Badge>
                </div>
                <div className="mt-1 flex flex-wrap items-center gap-md text-label text-ink-muted">
                  <span>Pool <PPAmount value={c.pp_budget} size="sm" /></span>
                  <span>· {c.pp_claimed.toLocaleString('en-US')} claimed</span>
                  <span>· {c.pp_reserved.toLocaleString('en-US')} reserved</span>
                  <span>· {c.pp_available.toLocaleString('en-US')} available</span>
                  <span>· {c.total_participants} joined</span>
                  {c.target_regions.length > 0 && <span>· {c.target_regions.join('/')}</span>}
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-sm">
                <button onClick={() => setTasksFor(c)} title="Manage tasks"
                  className="inline-flex h-9 w-9 items-center justify-center rounded-card bg-brand-ice text-brand-cobalt">
                  <ListChecks className="h-4 w-4" />
                </button>
                <button onClick={() => toggleStatus(c)} title={c.status === 'active' ? 'Pause' : 'Activate'}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-card bg-brand-ice text-brand-cobalt">
                  {c.status === 'active' ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                </button>
                {c.status !== 'ended' && (
                  <button onClick={() => endCampaign(c)} title="End campaign"
                    className="inline-flex h-9 w-9 items-center justify-center rounded-card bg-brand-ice text-ink-muted">
                    <X className="h-4 w-4" />
                  </button>
                )}
                <button onClick={() => deleteCampaign(c)} title="Delete campaign"
                  className="inline-flex h-9 w-9 items-center justify-center rounded-card bg-danger/10 text-danger">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </Card>
          ))}
          {campaigns.length === 0 && <Card><p className="text-center text-ink-muted">No campaigns yet.</p></Card>}
        </div>
      )}

      {tasksFor && <TasksModal campaign={tasksFor} onClose={() => setTasksFor(null)} />}

      <Modal open={partnerOpen} onClose={() => setPartnerOpen(false)} title="New partner">
        <div className="space-y-lg">
          <Input label="Partner name" value={partnerName} onChange={(e) => setPartnerName(e.target.value)} />
          <Button className="w-full" onClick={createPartner}>Create Partner</Button>
        </div>
      </Modal>

      <Modal open={open} onClose={() => setOpen(false)} title="New campaign">
        <div className="space-y-lg">
          <div>
            <label className="mb-2 block text-label font-medium text-ink-primary">Partner</label>
            <select value={form.partner_id} onChange={(e) => setForm({ ...form, partner_id: e.target.value })}
              className="w-full rounded-card border border-line bg-bg-primary px-md py-3 text-body text-ink-primary focus:outline-none focus:ring-2 focus:ring-brand-cobalt">
              <option value="">Select a partner…</option>
              {(partners ?? []).map((p: AdminPartner) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
          <Input label="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <Input label="Description" value={form.blurb} onChange={(e) => setForm({ ...form, blurb: e.target.value })} />
          <div className="grid grid-cols-3 gap-md">
            <Input label="Budget (PP)" type="number" value={form.pp_budget} onChange={(e) => setForm({ ...form, pp_budget: e.target.value })} />
            <Input label="Per task" type="number" value={form.pp_per_task} onChange={(e) => setForm({ ...form, pp_per_task: e.target.value })} />
            <Input label="Days" type="number" value={form.days} onChange={(e) => setForm({ ...form, days: e.target.value })} />
          </div>
          <label className="flex items-center gap-sm text-label text-ink-muted">
            <input type="checkbox" checked={form.featured} onChange={(e) => setForm({ ...form, featured: e.target.checked })} className="h-4 w-4 accent-brand-cobalt" />
            Feature this campaign
          </label>
          <Button className="w-full" onClick={createCampaign}>Create Campaign</Button>
        </div>
      </Modal>
    </div>
  );
}

export default CampaignsPage;
