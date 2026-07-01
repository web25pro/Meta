'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { Plus, Trash2, Power } from 'lucide-react';
import { toast } from 'sonner';
import { Card, Button, Input, Badge, Modal, Skeleton, PPAmount, cn } from '@meta-jungle/ui';
import { adminAPI, type AdminQuest } from '@/api/admin';

const CATEGORIES = ['daily', 'social', 'partner', 'nft', 'learning', 'referral'];

export default function AdminQuestsPage() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ title: '', description: '', pp_reward: '', category: 'social', daily_limit: '1' });

  const { data, isLoading } = useQuery('adminQuests', adminAPI.listQuests, { retry: false });
  const refresh = () => queryClient.invalidateQueries('adminQuests');

  const create = async () => {
    const pp = parseInt(form.pp_reward, 10);
    if (!form.title.trim() || !pp) {
      toast.error('Title and PP reward are required');
      return;
    }
    try {
      await adminAPI.createQuest({
        title: form.title,
        description: form.description,
        pp_reward: pp,
        category: form.category,
        daily_limit: parseInt(form.daily_limit, 10) || 1,
      });
      toast.success('Quest created');
      setOpen(false);
      setForm({ title: '', description: '', pp_reward: '', category: 'social', daily_limit: '1' });
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
    if (!confirm(`Delete "${q.title}"?`)) return;
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
      <div className="flex items-start justify-between gap-md">
        <div>
          <h1 className="font-display text-h1 text-ink-primary">Quests</h1>
          <p className="mt-1 text-body text-ink-muted">Create and manage earn actions.</p>
        </div>
        <Button onClick={() => setOpen(true)}><Plus className="h-4 w-4" /> New Quest</Button>
      </div>

      {isLoading || !data ? (
        <div className="space-y-sm">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-16" />)}</div>
      ) : (
        <Card className="p-0">
          <div className="divide-y divide-line">
            {data.map((q) => (
              <div key={q.id} className="flex items-center justify-between gap-md px-lg py-md">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-sm">
                    <span className="truncate font-medium text-ink-primary">{q.title}</span>
                    <Badge tone="cobalt" className="capitalize">{q.category}</Badge>
                    <Badge tone={q.is_active ? 'success' : 'neutral'}>{q.is_active ? 'Active' : 'Inactive'}</Badge>
                  </div>
                  {q.description && <p className="truncate text-label text-ink-muted">{q.description}</p>}
                </div>
                <PPAmount value={q.pp_reward} size="sm" className="shrink-0" />
                <div className="flex items-center gap-sm">
                  <button onClick={() => toggle(q)} title="Toggle active"
                    className={cn('inline-flex h-8 w-8 items-center justify-center rounded-card',
                      q.is_active ? 'bg-success/10 text-success' : 'bg-bg-elevated text-ink-muted')}>
                    <Power className="h-4 w-4" />
                  </button>
                  <button onClick={() => remove(q)} title="Delete"
                    className="inline-flex h-8 w-8 items-center justify-center rounded-card bg-danger/10 text-danger">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
            {data.length === 0 && <div className="px-lg py-2xl text-center text-ink-muted">No quests yet.</div>}
          </div>
        </Card>
      )}

      <Modal open={open} onClose={() => setOpen(false)} title="New quest">
        <div className="space-y-lg">
          <Input label="Title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <Input label="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          <div className="grid grid-cols-2 gap-md">
            <Input label="PP reward" type="number" value={form.pp_reward} onChange={(e) => setForm({ ...form, pp_reward: e.target.value })} />
            <Input label="Daily limit" type="number" value={form.daily_limit} onChange={(e) => setForm({ ...form, daily_limit: e.target.value })} />
          </div>
          <div>
            <label className="mb-2 block text-label font-medium text-ink-primary">Category</label>
            <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}
              className="w-full rounded-card border border-line bg-bg-primary px-md py-3 text-body text-ink-primary focus:outline-none focus:ring-2 focus:ring-brand-cobalt">
              {CATEGORIES.map((c) => <option key={c} value={c} className="capitalize">{c}</option>)}
            </select>
          </div>
          <Button className="w-full" onClick={create}>Create Quest</Button>
        </div>
      </Modal>
    </div>
  );
}
