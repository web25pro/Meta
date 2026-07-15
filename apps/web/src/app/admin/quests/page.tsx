'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { Plus, Trash2, Power, Target } from 'lucide-react';
import { toast } from 'sonner';
import { Card, Button, Input, Badge, Modal, Skeleton, PPAmount, EmptyState, cn } from '@meta-jungle/ui';
import { adminAPI, type AdminQuest } from '@/api/admin';

const CATEGORIES = ['daily', 'social', 'partner', 'nft', 'learning', 'referral'];
const VERIFICATION_TYPES = ['manual', 'oauth', 'screenshot', 'on_chain', 'webhook'];
const MIN_ROLES = ['Explorer', 'Tracker', 'Hunter', 'Whitelist', 'OG Panda', 'Alpha OG'];

export default function AdminQuestsPage() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    title: '',
    description: '',
    pp_reward: '',
    category: 'social',
    verification_type: 'manual',
    min_role: 'Explorer',
    daily_limit: '1',
    action_url: '',
    starts_at: '',
    ends_at: '',
  });

  const { data: quests, isLoading } = useQuery<AdminQuest[]>('adminQuests', adminAPI.listQuests, { retry: false });
  const refresh = () => queryClient.invalidateQueries('adminQuests');

  const resetForm = () =>
    setForm({
      title: '',
      description: '',
      pp_reward: '',
      category: 'social',
      verification_type: 'manual',
      min_role: 'Explorer',
      daily_limit: '1',
      action_url: '',
      starts_at: '',
      ends_at: '',
    });

  const create = async () => {
    const pp = parseInt(form.pp_reward, 10);
    if (!form.title.trim() || !pp) {
      toast.error('Title and PP reward are required');
      return;
    }
    try {
      const body: Record<string, unknown> = {
        title: form.title,
        description: form.description,
        pp_reward: pp,
        category: form.category,
        verification_type: form.verification_type,
        min_role: form.min_role,
        daily_limit: parseInt(form.daily_limit, 10) || 1,
      };
      if (form.action_url.trim()) body.action_url = form.action_url.trim();
      if (form.starts_at) body.starts_at = new Date(form.starts_at).toISOString();
      if (form.ends_at) body.ends_at = new Date(form.ends_at).toISOString();

      await adminAPI.createQuest(body as any);
      toast.success('Quest created');
      setOpen(false);
      resetForm();
      refresh();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed to create quest');
    }
  };

  const toggle = async (q: AdminQuest) => {
    try {
      await adminAPI.updateQuest(q.id, { is_active: !q.is_active });
      refresh();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed');
    }
  };

  const remove = async (q: AdminQuest) => {
    if (!confirm(`Delete "${q.title}"? This will soft-delete the quest.`)) return;
    try {
      await adminAPI.deleteQuest(q.id);
      toast.success('Quest deleted');
      refresh();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed');
    }
  };

  return (
    <div className="animate-page-in space-y-xl">
      {/* Page header — matches overview page pattern */}
      <div className="flex flex-col gap-md sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="font-display text-h1 text-ink-primary">Quests</h1>
          <p className="mt-1 text-body text-ink-muted">
            Create and manage earn actions for your community.
          </p>
        </div>
        <Button className="w-full sm:w-auto" onClick={() => setOpen(true)}>
          <Plus className="h-4 w-4" /> New Quest
        </Button>
      </div>

      {/* Quest list */}
      {isLoading ? (
        <div className="space-y-md">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-20" />
          ))}
        </div>
      ) : quests && quests.length > 0 ? (
        <div className="space-y-md">
          {quests.map((q) => (
            <Card key={q.id} className="p-0">
              <div className="flex flex-col gap-md px-lg py-md sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-sm">
                    <span className="font-medium text-ink-primary">{q.title}</span>
                    <Badge tone="cobalt" className="capitalize">{q.category}</Badge>
                    <Badge tone="sky" className="capitalize">
                      {q.verification_type.replace('_', ' ')}
                    </Badge>
                    {q.min_role !== 'Explorer' && (
                      <Badge tone="gold" className="capitalize">{q.min_role}+</Badge>
                    )}
                    <Badge tone={q.is_active ? 'success' : 'neutral'}>
                      {q.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                  {q.description && (
                    <p className="mt-1 text-label text-ink-muted line-clamp-2 sm:truncate">{q.description}</p>
                  )}
                </div>
                <div className="flex items-center gap-md sm:shrink-0">
                  <PPAmount value={q.pp_reward} size="sm" />
                  <div className="flex items-center gap-sm">
                    <button
                      onClick={() => toggle(q)}
                      title={q.is_active ? 'Deactivate' : 'Activate'}
                      className={cn(
                        'inline-flex h-8 w-8 items-center justify-center rounded-card transition-colors',
                        q.is_active
                          ? 'bg-success/10 text-success hover:bg-success/20'
                          : 'bg-bg-elevated text-ink-muted hover:bg-bg-surface'
                      )}
                    >
                      <Power className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => remove(q)}
                      title="Delete"
                      className="inline-flex h-8 w-8 items-center justify-center rounded-card bg-danger/10 text-danger transition-colors hover:bg-danger/20"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState
          title="No quests yet"
          description="Create your first quest to start engaging your community."
          icon={<Target className="h-12 w-12 text-brand-cobalt" />}
        />
      )}

      {/* Create quest modal — uses design system Modal */}
      <Modal open={open} onClose={() => { setOpen(false); resetForm(); }} title="New Quest">
        <div className="space-y-lg">
          <Input
            label="Title"
            placeholder="e.g. Follow us on X"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
          />
          <Input
            label="Description"
            placeholder="What does the user need to do?"
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
          />
          <Input
            label="Action Link (optional)"
            placeholder="https://x.com/username"
            value={form.action_url}
            onChange={(e) => setForm({ ...form, action_url: e.target.value })}
          />
          <div className="grid grid-cols-1 gap-md sm:grid-cols-2">
            <Input
              label="PP Reward"
              type="number"
              placeholder="50"
              value={form.pp_reward}
              onChange={(e) => setForm({ ...form, pp_reward: e.target.value })}
            />
            <Input
              label="Daily Limit"
              type="number"
              placeholder="1"
              value={form.daily_limit}
              onChange={(e) => setForm({ ...form, daily_limit: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-1 gap-md sm:grid-cols-2">
            <div>
              <label className="mb-2 block text-label font-medium text-ink-primary">Category</label>
              <select
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="w-full rounded-card border border-line bg-bg-primary px-md py-3 text-body text-ink-primary focus:outline-none focus:ring-2 focus:ring-brand-cobalt"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c} className="capitalize">{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-2 block text-label font-medium text-ink-primary">Verification</label>
              <select
                value={form.verification_type}
                onChange={(e) => setForm({ ...form, verification_type: e.target.value })}
                className="w-full rounded-card border border-line bg-bg-primary px-md py-3 text-body text-ink-primary focus:outline-none focus:ring-2 focus:ring-brand-cobalt"
              >
                {VERIFICATION_TYPES.map((v) => (
                  <option key={v} value={v}>{v.replace('_', ' ')}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="mb-2 block text-label font-medium text-ink-primary">Minimum Role</label>
            <select
              value={form.min_role}
              onChange={(e) => setForm({ ...form, min_role: e.target.value })}
              className="w-full rounded-card border border-line bg-bg-primary px-md py-3 text-body text-ink-primary focus:outline-none focus:ring-2 focus:ring-brand-cobalt"
            >
              {MIN_ROLES.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-1 gap-md sm:grid-cols-2">
            <Input
              label="Start Date (optional)"
              type="datetime-local"
              value={form.starts_at}
              onChange={(e) => setForm({ ...form, starts_at: e.target.value })}
            />
            <Input
              label="End Date (optional)"
              type="datetime-local"
              value={form.ends_at}
              onChange={(e) => setForm({ ...form, ends_at: e.target.value })}
            />
          </div>
          <div className="flex gap-md pt-sm">
            <Button variant="ghost" className="flex-1" onClick={() => { setOpen(false); resetForm(); }}>
              Cancel
            </Button>
            <Button className="flex-1" onClick={create}>
              Create Quest
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
