'use client';

import { useState } from 'react';
import { useMutation } from 'react-query';
import { Trash2, AlertTriangle, CheckCircle } from 'lucide-react';
import { Card, Button } from '@meta-jungle/ui';
import { adminAPI } from '../api/admin';

const DATA_CATEGORIES = [
  { key: 'points_transactions', label: 'PP Transactions', desc: 'All PP transaction history and ledger entries' },
  { key: 'quest_completions', label: 'Quest Completions', desc: 'All quest completion records' },
  { key: 'submissions', label: 'Task Submissions', desc: 'All task submissions and attached files' },
  { key: 'campaign_data', label: 'Campaign Data', desc: 'Campaign participations, tasks, completions, and rankings' },
  { key: 'leaderboard_cache', label: 'Leaderboard Cache', desc: 'Cached leaderboard data' },
  { key: 'announcements', label: 'Announcements', desc: 'All announcements' },
  { key: 'schedules', label: 'Schedules', desc: 'All scheduled events' },
  { key: 'nft_holdings', label: 'NFT Holdings', desc: 'All NFT holding records' },
  { key: 'p2p_orders', label: 'P2P Orders', desc: 'All peer-to-peer trade orders' },
  { key: 'stakes', label: 'Stakes', desc: 'All staking records' },
  { key: 'redemptions', label: 'Redemptions', desc: 'All marketplace redemptions' },
  { key: 'audit_logs', label: 'Audit Logs', desc: 'All audit log entries' },
  { key: 'idempotency_keys', label: 'Idempotency Keys', desc: 'Idempotency key cache' },
  { key: 'deadline_penalties', label: 'Deadline Penalties', desc: 'Applied deadline penalties' },
  { key: 'reset_user_points', label: 'Reset User Points', desc: 'Reset all user points, XP, and levels to zero' },
] as const;

export function ClearDataPage() {
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [result, setResult] = useState<{ cleared: Record<string, number> } | null>(null);

  const mutation = useMutation(
    () => adminAPI.clearData(selected),
    {
      onSuccess: (data) => {
        setResult(data);
        setConfirmOpen(false);
        setSelected({});
      },
    }
  );

  const toggle = (key: string) => setSelected(prev => ({ ...prev, [key]: !prev[key] }));
  const anySelected = Object.values(selected).some(Boolean);

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Clear Site Data</h1>
        <p className="mt-1 text-body text-ink-muted">
          Select data categories to permanently delete. This action cannot be undone.
        </p>
      </div>

      {result && (
        <Card className="border-forest-300 bg-forest-50">
          <div className="flex items-center gap-md">
            <CheckCircle className="h-5 w-5 text-forest-600" />
            <div>
              <p className="font-display text-body font-semibold text-forest-700">Data cleared successfully</p>
              <div className="mt-1 text-caption text-forest-600">
                {Object.entries(result.cleared).map(([k, v]) => (
                  <span key={k} className="mr-lg">{k}: {v} rows</span>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}

      <div className="grid gap-md sm:grid-cols-2 lg:grid-cols-3">
        {DATA_CATEGORIES.map(cat => (
          <button
            key={cat.key}
            onClick={() => toggle(cat.key)}
            className={`rounded-card border-2 p-lg text-left transition-all ${
              selected[cat.key]
                ? 'border-danger bg-danger/10'
                : 'border-stroke-default bg-bg-surface hover:border-stroke-hover'
            }`}
          >
            <div className="flex items-center gap-sm">
              <input
                type="checkbox"
                checked={!!selected[cat.key]}
                onChange={() => toggle(cat.key)}
                className="h-4 w-4 rounded accent-danger"
              />
              <span className="font-display text-body font-semibold text-ink-primary">{cat.label}</span>
            </div>
            <p className="mt-1 text-caption text-ink-muted">{cat.desc}</p>
          </button>
        ))}
      </div>

      <div className="flex items-center gap-md">
        <Button
          variant="cobalt"
          size="lg"
          className="bg-danger hover:bg-danger/90"
          disabled={!anySelected || mutation.isLoading}
          onClick={() => setConfirmOpen(true)}
        >
          <Trash2 className="mr-sm h-4 w-4" />
          Clear Selected Data
        </Button>
        {mutation.isLoading && <span className="text-caption text-ink-muted">Clearing...</span>}
      </div>

      {/* Confirmation modal */}
      {confirmOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-md">
          <Card className="max-w-lg">
            <div className="flex items-center gap-md">
              <AlertTriangle className="h-6 w-6 text-danger" />
              <h2 className="font-display text-h2 text-ink-primary">Confirm Deletion</h2>
            </div>
            <p className="mt-md text-body text-ink-secondary">
              You are about to permanently delete the following data categories:
            </p>
            <ul className="mt-sm list-disc pl-lg text-body text-ink-primary">
              {DATA_CATEGORIES.filter(c => selected[c.key]).map(c => (
                <li key={c.key}>{c.label}</li>
              ))}
            </ul>
            <p className="mt-md text-body font-semibold text-danger">
              This action cannot be undone.
            </p>
            <div className="mt-lg flex justify-end gap-md">
              <Button variant="ghost" onClick={() => setConfirmOpen(false)}>Cancel</Button>
              <Button variant="cobalt" onClick={() => mutation.mutate()} disabled={mutation.isLoading}>
                {mutation.isLoading ? 'Deleting...' : 'Delete Permanently'}
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

export default ClearDataPage;
