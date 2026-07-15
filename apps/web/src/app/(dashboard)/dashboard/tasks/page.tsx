'use client';

import { useState } from 'react';
import { useQuery, useQueryClient } from 'react-query';
import { Target, Loader2, ChevronDown, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';
import { Button, PPAmount, Skeleton, EmptyState, Badge, Modal, Input, cn } from '@meta-jungle/ui';
import { metajungleAPI, type ApiQuest } from '@/api/metajungle';

const CATEGORY_TONE: Record<string, 'cobalt' | 'sky' | 'gold' | 'success' | 'amber' | 'neutral'> = {
  daily: 'amber',
  social: 'sky',
  partner: 'cobalt',
  nft: 'gold',
  learning: 'success',
  referral: 'cobalt',
};

const ALL_CATEGORIES = ['all', 'daily', 'social', 'partner', 'nft', 'learning', 'referral'] as const;

/** Verification types that auto-approve (no admin review needed). */
const AUTO_APPROVE_TYPES = new Set(['oauth', 'webhook']);

export default function QuestsPage() {
  const queryClient = useQueryClient();
  const [completing, setCompleting] = useState<string | null>(null);
  const [category, setCategory] = useState<string>('all');

  // Proof modal state
  const [proofModal, setProofModal] = useState<ApiQuest | null>(null);
  const [proofInput, setProofInput] = useState('');
  const [stepsCompleted, setStepsCompleted] = useState<boolean[]>([]);

  const { data: quests, isLoading } = useQuery<ApiQuest[]>('mjQuests', metajungleAPI.listQuests, {
    retry: false,
  });

  const filtered = category === 'all'
    ? quests
    : quests?.filter((q) => q.category === category);

  /** Complete an auto-approve quest directly. */
  const completeDirect = async (q: ApiQuest) => {
    setCompleting(q.id);
    try {
      const proof: Record<string, unknown> = {};
      // For oauth/webhook, send verified flag
      if (AUTO_APPROVE_TYPES.has(q.verification_type)) {
        proof.verified = true;
      }
      const res = await metajungleAPI.completeQuest(q.id, proof);
      if (res.status === 'pending') {
        toast.success('Submitted for review! You\'ll receive PP once approved.');
      } else {
        toast.success(`Quest complete! +${res.pp_awarded} PP`);
      }
      queryClient.invalidateQueries('mjQuests');
      queryClient.invalidateQueries('pointsHistory');
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Could not complete quest');
    } finally {
      setCompleting(null);
    }
  };

  /** Open proof modal for quests that need it. */
  const openProofModal = (q: ApiQuest) => {
    setProofModal(q);
    setProofInput('');
    setStepsCompleted(q.steps ? q.steps.map(() => false) : []);
  };

  /** Submit proof from modal. */
  const submitProof = async () => {
    if (!proofModal) return;
    setCompleting(proofModal.id);
    try {
      const proof: Record<string, unknown> = {};

      if (proofModal.verification_type === 'on_chain') {
        if (!proofInput.trim()) {
          toast.error('Please provide a transaction hash');
          setCompleting(null);
          return;
        }
        proof.tx_hash = proofInput.trim();
      } else if (proofModal.verification_type === 'screenshot' || proofModal.verification_type === 'manual') {
        if (proofInput.trim()) {
          proof.note = proofInput.trim();
        }
      }

      // Include steps if quest has them
      if (proofModal.steps && proofModal.steps.length > 0) {
        proof.steps_completed = stepsCompleted;
      }

      const res = await metajungleAPI.completeQuest(proofModal.id, proof);
      if (res.status === 'pending') {
        toast.success('Submitted for review! You\'ll receive PP once approved.');
      } else {
        toast.success(`Quest complete! +${res.pp_awarded} PP`);
      }
      setProofModal(null);
      queryClient.invalidateQueries('mjQuests');
      queryClient.invalidateQueries('pointsHistory');
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || 'Could not complete quest');
    } finally {
      setCompleting(null);
    }
  };

  const handleComplete = (q: ApiQuest) => {
    if (AUTO_APPROVE_TYPES.has(q.verification_type)) {
      completeDirect(q);
    } else {
      openProofModal(q);
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

      {/* Category filter */}
      <div className="flex flex-wrap gap-sm">
        {ALL_CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setCategory(cat)}
            className={cn(
              'rounded-pill px-md py-sm text-label font-medium capitalize transition-colors',
              category === cat
                ? 'bg-brand-cobalt text-ink-inverse'
                : 'border border-line bg-bg-primary text-ink-muted hover:bg-bg-elevated',
            )}
          >
            {cat}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-lg">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      ) : filtered && filtered.length > 0 ? (
        <div className="space-y-lg">
          {filtered.map((q) => (
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
                    {q.min_role !== 'Explorer' && (
                      <Badge tone="gold" className="capitalize">
                        {q.min_role}+
                      </Badge>
                    )}
                  </div>
                  <p className="text-body text-ink-muted">{q.description}</p>
                </div>
                <PPAmount value={q.pp_reward} size="sm" className="shrink-0" />
              </div>
              <div className="mt-lg flex items-center justify-between">
                <div className="flex items-center gap-sm text-label text-ink-muted">
                  <span className="capitalize">{q.verification_type.replace('_', ' ')}</span>
                  {q.daily_limit > 1 && <span>· {q.daily_limit}×/day</span>}
                  {q.ends_at && (
                    <span>
                      · ends {new Date(q.ends_at).toLocaleDateString()}
                    </span>
                  )}
                  {!AUTO_APPROVE_TYPES.has(q.verification_type) && (
                    <Badge tone="amber" className="text-xs">Requires review</Badge>
                  )}
                </div>
                <div className="flex items-center gap-sm">
                  {q.action_url && (
                    <a
                      href={q.action_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 rounded-card border border-line bg-bg-primary px-3 py-1.5 text-label font-medium text-ink-muted transition-colors hover:bg-bg-elevated hover:text-ink-primary"
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                      Open link
                    </a>
                  )}
                  <Button
                    size="sm"
                    onClick={() => handleComplete(q)}
                    disabled={completing === q.id}
                  >
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
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          title="No quests available"
          description={
            category !== 'all'
              ? `No ${category} quests available. Try a different category.`
              : 'New quests appear here as they go live. Check back soon to start earning.'
          }
          icon={<Target className="h-12 w-12 text-brand-cobalt" />}
        />
      )}

      {/* Proof submission modal */}
      <Modal
        open={!!proofModal}
        onClose={() => setProofModal(null)}
        title={proofModal ? `Complete: ${proofModal.title}` : 'Submit Proof'}
      >
        <div className="space-y-lg">
          {proofModal?.verification_type === 'on_chain' && (
            <div>
              <Input
                label="Transaction Hash"
                placeholder="0x..."
                value={proofInput}
                onChange={(e) => setProofInput(e.target.value)}
              />
              <p className="mt-1 text-label text-ink-muted">
                Paste the transaction hash from your on-chain action.
              </p>
            </div>
          )}

          {(proofModal?.verification_type === 'manual' || proofModal?.verification_type === 'screenshot') && (
            <div>
              <Input
                label="Notes (optional)"
                placeholder="Describe how you completed this quest..."
                value={proofInput}
                onChange={(e) => setProofInput(e.target.value)}
              />
              <p className="mt-1 text-label text-ink-muted">
                {proofModal.verification_type === 'screenshot'
                  ? 'Your submission will be reviewed by an admin. Include any relevant details.'
                  : 'An admin will verify your completion and approve it.'}
              </p>
            </div>
          )}

          {/* Steps checklist */}
          {proofModal?.steps && proofModal.steps.length > 0 && (
            <div>
              <label className="mb-2 block text-label font-medium text-ink-primary">
                Complete each step:
              </label>
              <div className="space-y-sm">
                {proofModal.steps.map((step, i) => (
                  <label
                    key={i}
                    className="flex items-center gap-sm rounded-card bg-bg-surface px-md py-2"
                  >
                    <input
                      type="checkbox"
                      checked={stepsCompleted[i] || false}
                      onChange={(e) => {
                        const updated = [...stepsCompleted];
                        updated[i] = e.target.checked;
                        setStepsCompleted(updated);
                      }}
                      className="h-4 w-4 rounded border-line text-brand-cobalt focus:ring-brand-cobalt"
                    />
                    <span className="text-body text-ink-primary">{step.label}</span>
                  </label>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-md">
            <Button variant="ghost" className="flex-1" onClick={() => setProofModal(null)}>
              Cancel
            </Button>
            <Button
              className="flex-1"
              onClick={submitProof}
              disabled={completing === proofModal?.id}
            >
              {completing === proofModal?.id ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Submitting…
                </>
              ) : (
                'Submit'
              )}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
