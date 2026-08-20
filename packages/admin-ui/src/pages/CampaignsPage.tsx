'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { Plus, Pause, Play, ListChecks, Check, X, Trash2, Star } from 'lucide-react';
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
      toast.error(e?.response?.data?.error?.message || e?.response?.data?.detail || 'Failed');
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
  const emptyForm = {
    title: '', description: '', pp_reward: '', verification_type: 'manual', daily_limit: '1',
    action_url: '', screenshot_required: false, link_required: false,
  };
  const [form, setForm] = useState({
    ...emptyForm,
  });
  const [editingId, setEditingId] = useState<string | null>(null);
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
      const payload = {
        title: form.title,
        description: form.description,
        pp_reward: reward,
        verification_type: form.verification_type,
        daily_limit: parseInt(form.daily_limit, 10) || 1,
        action_url: form.action_url.trim() || undefined,
        screenshot_required: form.screenshot_required,
        link_required: form.link_required,
      };
      if (editingId) {
        await adminAPI.updateCampaignTask(campaign.id, editingId, payload);
        toast.success('Task updated');
      } else {
        await adminAPI.createCampaignTask(campaign.id, payload);
        toast.success('Task added');
      }
      setEditingId(null);
      setForm({ ...emptyForm });
      queryClient.invalidateQueries(['adminCampaignTasks', campaign.id]);
    } catch (e: any) {
      toast.error(e?.response?.data?.error?.message || e?.response?.data?.detail || 'Failed');
    }
  };

  const editTask = (task: any) => {
    setEditingId(task.id);
    setForm({
      title: task.title,
      description: task.description ?? '',
      pp_reward: String(task.pp_reward),
      verification_type: task.verification_type,
      daily_limit: String(task.daily_limit),
      action_url: task.action_url ?? '',
      screenshot_required: !!task.screenshot_required,
      link_required: !!task.link_required,
    });
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
              <div className="flex shrink-0 items-center gap-sm">
                <PPAmount value={t.pp_reward} size="sm" />
                <Button size="sm" variant="ghost" onClick={() => editTask(t)}>Edit</Button>
              </div>
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
          <Input label="Clickable task link" placeholder="https://..." value={form.action_url} onChange={(e) => setForm({ ...form, action_url: e.target.value })} />
          <div className="space-y-sm">
            <label className="flex items-center gap-sm text-label text-ink-muted"><input type="checkbox" checked={form.screenshot_required} onChange={(e) => setForm({ ...form, screenshot_required: e.target.checked })} className="h-4 w-4 accent-brand-cobalt" /> Screenshot upload required</label>
            <label className="flex items-center gap-sm text-label text-ink-muted"><input type="checkbox" checked={form.link_required} onChange={(e) => setForm({ ...form, link_required: e.target.checked })} className="h-4 w-4 accent-brand-cobalt" /> Completion link required</label>
          </div>
          <div className="flex gap-sm">
            {editingId && <Button variant="ghost" className="flex-1" onClick={() => { setEditingId(null); setForm({ ...emptyForm }); }}>Cancel edit</Button>}
            <Button className="flex-1" onClick={create}>{editingId ? 'Save task' : 'Add task'}</Button>
          </div>
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
  const [taskDraft, setTaskDraft] = useState({ title: '', description: '', pp_reward: '', verification_type: 'manual', daily_limit: '1', action_url: '', screenshot_required: false, link_required: false });
  const [draftTasks, setDraftTasks] = useState<Array<typeof taskDraft>>([]);
  const [partnerName, setPartnerName] = useState('');
  const [partnerTier, setPartnerTier] = useState('bronze');
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
      await adminAPI.createPartner({ name: partnerName, tier: partnerTier });
      toast.success('Partner created');
      setPartnerName('');
      setPartnerTier('bronze');
      setPartnerOpen(false);
      refresh();
    } catch (e: any) {
      toast.error(e?.response?.data?.error?.message || e?.response?.data?.detail || 'Failed');
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
      const campaign = await adminAPI.createCampaign({
        partner_id: form.partner_id, title: form.title, blurb: form.blurb,
        pp_budget: budget, pp_per_task: perTask, featured: form.featured, days: parseInt(form.days, 10) || 14,
      });
      for (const task of draftTasks) {
        await adminAPI.createCampaignTask(campaign.id, {
          title: task.title.trim(),
          description: task.description.trim(),
          pp_reward: parseInt(task.pp_reward, 10),
          verification_type: task.verification_type,
          daily_limit: parseInt(task.daily_limit, 10) || 1,
          action_url: task.action_url.trim() || undefined,
          screenshot_required: task.screenshot_required,
          link_required: task.link_required,
          order_index: draftTasks.indexOf(task),
        });
      }
      toast.success(`Campaign created with ${draftTasks.length} task${draftTasks.length === 1 ? '' : 's'}`);
      setOpen(false);
      setForm({ partner_id: '', title: '', blurb: '', pp_budget: '', pp_per_task: '', days: '14', featured: false });
      setTaskDraft({ title: '', description: '', pp_reward: '', verification_type: 'manual', daily_limit: '1', action_url: '', screenshot_required: false, link_required: false });
      setDraftTasks([]);
      refresh();
    } catch (e: any) {
      toast.error(e?.response?.data?.error?.message || e?.response?.data?.detail || 'Failed');
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
      toast.error(e?.response?.data?.error?.message || e?.response?.data?.detail || 'Failed');
    }
  };

  const toggleFeatured = async (c: AdminCampaign) => {
    try {
      await adminAPI.setCampaignFeatured(c.id, !c.featured);
      toast.success(c.featured ? 'Removed from featured campaigns' : 'Added to featured campaigns');
      refresh();
    } catch (e: any) {
      toast.error(e?.response?.data?.error?.message || e?.response?.data?.detail || 'Could not update featured setting');
    }
  };

  const endCampaign = async (c: AdminCampaign) => {
    try {
      await adminAPI.setCampaignStatus(c.id, 'ended');
      toast.success('Campaign ended');
      refresh();
    } catch (e: any) {
      toast.error(e?.response?.data?.error?.message || e?.response?.data?.detail || 'Failed');
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
      toast.error(e?.response?.data?.error?.message || e?.response?.data?.detail || 'Failed');
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
                <button onClick={() => toggleFeatured(c)} title={c.featured ? 'Remove from featured' : 'Add to featured'}
                  className={`inline-flex h-9 w-9 items-center justify-center rounded-card ${c.featured ? 'bg-reward-gold/15 text-reward-gold' : 'bg-bg-elevated text-ink-muted'}`}>
                  <Star className="h-4 w-4" fill={c.featured ? 'currentColor' : 'none'} />
                </button>
                <button onClick={() => setTasksFor(c)} title={c.status === 'ended' ? 'Ended campaigns cannot receive tasks' : 'Manage tasks'}
                  disabled={c.status === 'ended'}
                  className="inline-flex h-9 items-center justify-center gap-1 rounded-card bg-brand-ice px-sm text-label font-medium text-brand-cobalt disabled:cursor-not-allowed disabled:opacity-40">
                  <ListChecks className="h-4 w-4" />
                  <span>Tasks</span>
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
          <div>
            <label className="mb-2 block text-label font-medium text-ink-primary">Partner tier</label>
            <select value={partnerTier} onChange={(e) => setPartnerTier(e.target.value)} className="w-full rounded-card border border-line bg-bg-primary px-md py-3 text-body text-ink-primary">
              <option value="bronze">Bronze</option>
              <option value="silver">Silver</option>
              <option value="gold">Gold</option>
              <option value="platinum">Platinum</option>
            </select>
          </div>
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
          <div className="space-y-md rounded-card border border-line bg-bg-elevated p-md">
            <div>
              <p className="font-medium text-ink-primary">Campaign tasks</p>
              <p className="text-label text-ink-muted">Add the actions participants must complete during this campaign.</p>
            </div>
            {draftTasks.length > 0 && (
              <div className="space-y-1">
                {draftTasks.map((task, index) => (
                  <div key={`${task.title}-${index}`} className="flex items-center justify-between rounded-card bg-bg-primary px-sm py-2 text-label">
                    <span className="truncate text-ink-primary">{index + 1}. {task.title}</span>
                    <span className="ml-sm shrink-0 text-ink-muted">{task.pp_reward} PP</span>
                  </div>
                ))}
              </div>
            )}
            <Input label="Task title" value={taskDraft.title} onChange={(e) => setTaskDraft({ ...taskDraft, title: e.target.value })} />
            <Input label="Task instructions" value={taskDraft.description} onChange={(e) => setTaskDraft({ ...taskDraft, description: e.target.value })} />
            <div className="grid grid-cols-2 gap-md">
              <Input label="Task reward (PP)" type="number" value={taskDraft.pp_reward} onChange={(e) => setTaskDraft({ ...taskDraft, pp_reward: e.target.value })} />
              <Input label="Daily limit" type="number" value={taskDraft.daily_limit} onChange={(e) => setTaskDraft({ ...taskDraft, daily_limit: e.target.value })} />
            </div>
            <div>
              <label className="mb-2 block text-label font-medium text-ink-primary">Verification</label>
              <select value={taskDraft.verification_type} onChange={(e) => setTaskDraft({ ...taskDraft, verification_type: e.target.value })}
                className="w-full rounded-card border border-line bg-bg-primary px-md py-3 text-body text-ink-primary">
                <option value="manual">Manual review</option>
                <option value="screenshot">Screenshot</option>
                <option value="on_chain">On-chain transaction</option>
                <option value="oauth">OAuth review</option>
                <option value="webhook">Webhook review</option>
              </select>
            </div>
            <Input label="Task action URL (optional)" value={taskDraft.action_url} onChange={(e) => setTaskDraft({ ...taskDraft, action_url: e.target.value })} />
            <div className="space-y-sm">
              <label className="flex items-center gap-sm text-label text-ink-muted"><input type="checkbox" checked={taskDraft.screenshot_required} onChange={(e) => setTaskDraft({ ...taskDraft, screenshot_required: e.target.checked })} className="h-4 w-4 accent-brand-cobalt" /> Screenshot upload required</label>
              <label className="flex items-center gap-sm text-label text-ink-muted"><input type="checkbox" checked={taskDraft.link_required} onChange={(e) => setTaskDraft({ ...taskDraft, link_required: e.target.checked })} className="h-4 w-4 accent-brand-cobalt" /> Completion link required</label>
            </div>
            <Button variant="ghost" className="w-full" onClick={() => {
              const reward = parseInt(taskDraft.pp_reward, 10);
              if (!taskDraft.title.trim() || !reward || reward <= 0) {
                toast.error('Task title and reward are required');
                return;
              }
              setDraftTasks([...draftTasks, taskDraft]);
              setTaskDraft({ title: '', description: '', pp_reward: '', verification_type: 'manual', daily_limit: '1', action_url: '', screenshot_required: false, link_required: false });
            }}>
              <ListChecks className="h-4 w-4" /> Add task to campaign
            </Button>
          </div>
          <Button className="w-full" onClick={createCampaign}>Create Campaign</Button>
        </div>
      </Modal>
    </div>
  );
}

export default CampaignsPage;
