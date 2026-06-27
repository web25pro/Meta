'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { Plus, Pause, Play } from 'lucide-react';
import { toast } from 'sonner';
import { Card, Button, Input, Badge, Modal, Skeleton, PPAmount } from '@meta-jungle/ui';
import { adminAPI, type AdminCampaign, type AdminPartner } from '@/api/admin';

export default function AdminCampaignsPage() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [partnerOpen, setPartnerOpen] = useState(false);
  const [form, setForm] = useState({ partner_id: '', title: '', blurb: '', pp_budget: '', pp_per_task: '', days: '14', featured: false });
  const [partnerName, setPartnerName] = useState('');

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
    const next = c.status === 'active' ? 'paused' : 'active';
    try {
      await adminAPI.setCampaignStatus(c.id, next);
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
                <div className="mt-1 flex items-center gap-md text-label text-ink-muted">
                  <span>Pool <PPAmount value={c.pp_budget} size="sm" /></span>
                  <span>· {c.pp_per_task} PP/task</span>
                  <span>· {c.total_participants} joined</span>
                </div>
              </div>
              <button onClick={() => toggleStatus(c)} title={c.status === 'active' ? 'Pause' : 'Activate'}
                className="inline-flex h-9 w-9 items-center justify-center rounded-card bg-brand-ice text-brand-cobalt">
                {c.status === 'active' ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              </button>
            </Card>
          ))}
          {campaigns.length === 0 && <Card><p className="text-center text-ink-muted">No campaigns yet.</p></Card>}
        </div>
      )}

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
