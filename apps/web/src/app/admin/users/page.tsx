'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { Search, Ban, ShieldCheck, Coins } from 'lucide-react';
import { toast } from 'sonner';
import { Card, Button, Input, Badge, Modal, Skeleton, PPAmount, cn } from '@meta-jungle/ui';
import { adminAPI, type AdminUser } from '@/api/admin';

const ROLES = ['Community_User', 'Ambassador', 'Team_Member', 'Ambassador_Admin', 'Overall_Admin'];

export default function AdminUsersPage() {
  const queryClient = useQueryClient();
  const [q, setQ] = useState('');
  const [search, setSearch] = useState('');
  const [ppUser, setPpUser] = useState<AdminUser | null>(null);
  const [ppAmount, setPpAmount] = useState('');
  const [ppReason, setPpReason] = useState('');

  const { data, isLoading } = useQuery(['adminUsers', search], () => adminAPI.listUsers(1, search), {
    retry: false,
  });

  const refresh = () => queryClient.invalidateQueries('adminUsers');

  const toggleBan = async (u: AdminUser) => {
    try {
      await adminAPI.updateUser(u.id, { is_active: u.is_banned });
      toast.success(u.is_banned ? 'User unbanned' : 'User banned');
      refresh();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed');
    }
  };

  const setRole = async (u: AdminUser, role: string) => {
    try {
      await adminAPI.updateUser(u.id, { role });
      toast.success(`Role set to ${role}`);
      refresh();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed');
    }
  };

  const submitPP = async () => {
    if (!ppUser) return;
    const amt = parseFloat(ppAmount);
    if (!amt || !ppReason.trim()) {
      toast.error('Enter an amount and reason');
      return;
    }
    try {
      await adminAPI.adjustPoints(ppUser.id, amt, ppReason);
      toast.success('Balance adjusted');
      setPpUser(null);
      setPpAmount('');
      setPpReason('');
      refresh();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Failed');
    }
  };

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Users</h1>
        <p className="mt-1 text-body text-ink-muted">Manage roles, balances and access.</p>
      </div>

      <form
        onSubmit={(e) => { e.preventDefault(); setSearch(q); }}
        className="flex gap-sm"
      >
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-muted" />
          <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search name, username or email…" className="pl-9" />
        </div>
        <Button type="submit">Search</Button>
      </form>

      {isLoading || !data ? (
        <div className="space-y-sm">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-16" />)}</div>
      ) : (
        <Card className="p-0">
          <div className="grid grid-cols-12 gap-md border-b border-line px-lg py-sm text-label uppercase tracking-wide text-ink-muted">
            <div className="col-span-4">User</div>
            <div className="col-span-3">Role</div>
            <div className="col-span-2">Balance</div>
            <div className="col-span-3 text-right">Actions</div>
          </div>
          <div className="divide-y divide-line">
            {data.users.map((u) => (
              <div key={u.id} className="grid grid-cols-12 items-center gap-md px-lg py-md">
                <div className="col-span-4 min-w-0">
                  <div className="flex items-center gap-sm">
                    <span className="truncate font-medium text-ink-primary">{u.username || u.name}</span>
                    {u.is_banned && <Badge tone="danger">Banned</Badge>}
                  </div>
                  <div className="truncate text-label text-ink-muted">{u.email}</div>
                </div>
                <div className="col-span-3">
                  <select
                    value={u.role}
                    onChange={(e) => setRole(u, e.target.value)}
                    className="w-full rounded-card border border-line bg-bg-primary px-sm py-1.5 text-label text-ink-primary focus:outline-none focus:ring-2 focus:ring-brand-cobalt"
                  >
                    {ROLES.map((r) => <option key={r} value={r}>{r.replace(/_/g, ' ')}</option>)}
                  </select>
                </div>
                <div className="col-span-2">
                  <PPAmount value={Math.round(u.points)} size="sm" />
                </div>
                <div className="col-span-3 flex items-center justify-end gap-sm">
                  <button
                    onClick={() => setPpUser(u)}
                    title="Adjust PP"
                    className="inline-flex h-8 w-8 items-center justify-center rounded-card bg-brand-ice text-brand-cobalt hover:bg-bg-elevated"
                  >
                    <Coins className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => toggleBan(u)}
                    title={u.is_banned ? 'Unban' : 'Ban'}
                    className={cn(
                      'inline-flex h-8 w-8 items-center justify-center rounded-card',
                      u.is_banned ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger',
                    )}
                  >
                    {u.is_banned ? <ShieldCheck className="h-4 w-4" /> : <Ban className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            ))}
            {data.users.length === 0 && (
              <div className="px-lg py-2xl text-center text-ink-muted">No users found.</div>
            )}
          </div>
        </Card>
      )}

      <Modal open={!!ppUser} onClose={() => setPpUser(null)} title={`Adjust PP — ${ppUser?.username || ppUser?.email || ''}`}>
        <div className="space-y-lg">
          <Input
            label="Amount (PP)"
            type="number"
            placeholder="Positive to credit, negative to debit"
            value={ppAmount}
            onChange={(e) => setPpAmount(e.target.value)}
          />
          <Input label="Reason" placeholder="Reason for adjustment" value={ppReason} onChange={(e) => setPpReason(e.target.value)} />
          <Button className="w-full" onClick={submitPP}>Apply adjustment</Button>
        </div>
      </Modal>
    </div>
  );
}
