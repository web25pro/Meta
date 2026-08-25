'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from 'react-query';
import {
  Megaphone,
  Image as ImageIcon,
  Video,
  Trophy,
  Target,
  Loader2,
  ArrowLeft,
  ArrowRight,
  Check,
  Lock,
} from 'lucide-react';
import { cn, Card, Button, Badge, Skeleton } from '@meta-jungle/ui';
import { premiumAPI, MembershipStatus } from '@/api/premium';
import apiClient from '@/lib/api';
import { toast } from 'sonner';

const CAMPAIGN_TYPES = [
  { key: 'text', label: 'Text Campaign', icon: Megaphone, minTier: 'panda_pro' },
  { key: 'engagement', label: 'Engagement', icon: Target, minTier: 'panda_pro' },
  { key: 'image', label: 'Image Campaign', icon: ImageIcon, minTier: 'panda_elite' },
  { key: 'video', label: 'Video Campaign', icon: Video, minTier: 'panda_elite' },
  { key: 'video_contest', label: 'Video Contest', icon: Trophy, minTier: 'panda_elite' },
  { key: 'bounty', label: 'Bounty', icon: Target, minTier: 'panda_elite' },
];

export default function CreateCampaignPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [step, setStep] = useState(1);

  // Form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [campaignType, setCampaignType] = useState('text');
  const [numQualifiers, setNumQualifiers] = useState(10);
  const [ppPerQualifier, setPpPerQualifier] = useState(50);
  const [startsAt, setStartsAt] = useState('');
  const [endsAt, setEndsAt] = useState('');

  const { data: status, isLoading } = useQuery<MembershipStatus>(
    'membershipStatus',
    () => premiumAPI.getStatus(),
    { staleTime: 60_000 },
  );

  const createMutation = useMutation(
    async () => {
      const { data } = await apiClient.post('/campaigns/create', {
        title,
        description,
        campaign_type: campaignType,
        num_qualifiers: numQualifiers,
        pp_per_qualifier: ppPerQualifier,
        starts_at: startsAt || null,
        ends_at: endsAt || null,
      });
      return data;
    },
    {
      onSuccess: (data) => {
        toast.success('Campaign created! Now fund it to make it active.');
        queryClient.invalidateQueries('myCampaigns');
        router.push('/dashboard/campaigns/my-campaigns');
      },
      onError: (err: any) => {
        toast.error(err?.response?.data?.detail || 'Failed to create campaign');
      },
    },
  );

  const fundMutation = useMutation(
    async (campaignId: string) => {
      const { data } = await apiClient.post(`/campaigns/${campaignId}/fund`);
      return data;
    },
    {
      onSuccess: () => {
        toast.success('Campaign funded and now active!');
        queryClient.invalidateQueries('myCampaigns');
        queryClient.invalidateQueries('membershipStatus');
      },
      onError: (err: any) => {
        toast.error(err?.response?.data?.detail || 'Failed to fund campaign');
      },
    },
  );

  if (isLoading) {
    return (
      <div className="animate-page-in space-y-xl">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!status?.permissions.can_create_campaign) {
    return (
      <div className="animate-page-in space-y-xl">
        <h1 className="font-display text-h1 text-ink-primary">Create Campaign</h1>
        <Card className="p-xl text-center space-y-md">
          <Lock className="mx-auto h-12 w-12 text-ink-muted" />
          <h2 className="font-display text-h2 text-ink-primary">Campaign Creation Locked</h2>
          <p className="text-body text-ink-muted max-w-md mx-auto">
            Campaign creation requires Panda Pro or Panda Elite membership.
            Hold at least 3 LPanda NFTs to unlock.
          </p>
          <Button variant="jungle" onClick={() => router.push('/dashboard/premium')}>
            View Membership Tiers
          </Button>
        </Card>
      </div>
    );
  }

  const totalEscrow = numQualifiers * ppPerQualifier;
  const availablePP = status?.available_points || 0;
  const canAfford = availablePP >= totalEscrow;

  const canUseMediaType = (type: string) => {
    if (['image', 'video', 'video_contest', 'bounty'].includes(type)) {
      return status?.permissions.can_use_media || false;
    }
    return true;
  };

  return (
    <div className="animate-page-in space-y-xl">
      <div className="flex items-center gap-md">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="font-display text-h1 text-ink-primary">Create Campaign</h1>
          <p className="text-body text-ink-muted">
            Set up a performance-based campaign with PP rewards.
          </p>
        </div>
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-md">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center gap-sm">
            <div className={cn(
              'flex h-8 w-8 items-center justify-center rounded-full text-body font-medium',
              step >= s ? 'bg-brand-cobalt text-white' : 'bg-bg-elevated text-ink-muted',
            )}>
              {step > s ? <Check className="h-4 w-4" /> : s}
            </div>
            <span className={cn('text-body', step >= s ? 'text-ink-primary' : 'text-ink-muted')}>
              {s === 1 ? 'Details' : s === 2 ? 'Configuration' : 'Review & Fund'}
            </span>
            {s < 3 && <div className="h-px w-8 bg-line" />}
          </div>
        ))}
      </div>

      {/* Step 1: Details */}
      {step === 1 && (
        <Card className="p-lg space-y-lg">
          <h2 className="font-display text-h2 text-ink-primary">Campaign Details</h2>

          <div className="space-y-sm">
            <label className="text-label text-ink-muted">Campaign Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter campaign title"
              className="w-full rounded-card border border-line bg-bg-primary px-md py-sm text-body text-ink-primary placeholder:text-ink-muted focus:border-brand-cobalt focus:outline-none"
            />
          </div>

          <div className="space-y-sm">
            <label className="text-label text-ink-muted">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe your campaign..."
              rows={4}
              className="w-full rounded-card border border-line bg-bg-primary px-md py-sm text-body text-ink-primary placeholder:text-ink-muted focus:border-brand-cobalt focus:outline-none resize-none"
            />
          </div>

          <div className="space-y-sm">
            <label className="text-label text-ink-muted">Campaign Type</label>
            <div className="grid grid-cols-2 gap-sm sm:grid-cols-3">
              {CAMPAIGN_TYPES.map((ct) => {
                const locked = !canUseMediaType(ct.key);
                return (
                  <button
                    key={ct.key}
                    onClick={() => !locked && setCampaignType(ct.key)}
                    disabled={locked}
                    className={cn(
                      'flex flex-col items-center gap-sm rounded-card border p-md transition-all',
                      campaignType === ct.key
                        ? 'border-brand-cobalt bg-brand-ice'
                        : locked
                        ? 'border-line bg-bg-elevated opacity-50 cursor-not-allowed'
                        : 'border-line hover:border-brand-cobalt/50',
                    )}
                  >
                    <ct.icon className={cn(
                      'h-5 w-5',
                      campaignType === ct.key ? 'text-brand-cobalt' : 'text-ink-muted',
                    )} />
                    <span className="text-body text-ink-primary">{ct.label}</span>
                    {locked && (
                      <Badge tone="neutral" className="text-caption">
                        <Lock className="h-3 w-3" /> Elite
                      </Badge>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="flex justify-end">
            <Button
              variant="jungle"
              onClick={() => setStep(2)}
              disabled={!title.trim()}
            >
              Next <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </Card>
      )}

      {/* Step 2: Configuration */}
      {step === 2 && (
        <Card className="p-lg space-y-lg">
          <h2 className="font-display text-h2 text-ink-primary">Reward Configuration</h2>

          <div className="grid gap-lg sm:grid-cols-2">
            <div className="space-y-sm">
              <label className="text-label text-ink-muted">Number of Qualifiers</label>
              <input
                type="number"
                value={numQualifiers}
                onChange={(e) => setNumQualifiers(Math.max(1, parseInt(e.target.value) || 1))}
                min={1}
                max={1000}
                className="w-full rounded-card border border-line bg-bg-primary px-md py-sm text-body text-ink-primary focus:border-brand-cobalt focus:outline-none"
              />
            </div>

            <div className="space-y-sm">
              <label className="text-label text-ink-muted">PP Per Qualifier</label>
              <input
                type="number"
                value={ppPerQualifier}
                onChange={(e) => setPpPerQualifier(Math.max(1, parseInt(e.target.value) || 1))}
                min={1}
                className="w-full rounded-card border border-line bg-bg-primary px-md py-sm text-body text-ink-primary focus:border-brand-cobalt focus:outline-none"
              />
            </div>

            <div className="space-y-sm">
              <label className="text-label text-ink-muted">Start Date (optional)</label>
              <input
                type="datetime-local"
                value={startsAt}
                onChange={(e) => setStartsAt(e.target.value)}
                className="w-full rounded-card border border-line bg-bg-primary px-md py-sm text-body text-ink-primary focus:border-brand-cobalt focus:outline-none"
              />
            </div>

            <div className="space-y-sm">
              <label className="text-label text-ink-muted">End Date (optional)</label>
              <input
                type="datetime-local"
                value={endsAt}
                onChange={(e) => setEndsAt(e.target.value)}
                className="w-full rounded-card border border-line bg-bg-primary px-md py-sm text-body text-ink-primary focus:border-brand-cobalt focus:outline-none"
              />
            </div>
          </div>

          {/* Escrow preview */}
          <div className="rounded-card bg-bg-elevated p-md space-y-sm">
            <div className="flex justify-between text-body">
              <span className="text-ink-muted">Total Escrow Required</span>
              <span className="font-display text-h3 text-ink-primary">
                {totalEscrow.toLocaleString()} PP
              </span>
            </div>
            <div className="flex justify-between text-body">
              <span className="text-ink-muted">Your Available PP</span>
              <span className={cn(
                'font-medium',
                canAfford ? 'text-reward-jungle' : 'text-danger',
              )}>
                {availablePP.toLocaleString()} PP
              </span>
            </div>
            {!canAfford && (
              <p className="text-caption text-danger">
                Insufficient PP. You need {(totalEscrow - availablePP).toLocaleString()} more PP.
              </p>
            )}
          </div>

          <div className="flex justify-between">
            <Button variant="ghost" onClick={() => setStep(1)}>
              <ArrowLeft className="h-4 w-4" /> Back
            </Button>
            <Button
              variant="jungle"
              onClick={() => setStep(3)}
              disabled={!canAfford}
            >
              Review <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </Card>
      )}

      {/* Step 3: Review & Fund */}
      {step === 3 && (
        <Card className="p-lg space-y-lg">
          <h2 className="font-display text-h2 text-ink-primary">Review & Launch</h2>

          <div className="space-y-md rounded-card bg-bg-elevated p-md">
            <div className="flex justify-between">
              <span className="text-ink-muted">Title</span>
              <span className="text-ink-primary font-medium">{title}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-ink-muted">Type</span>
              <span className="text-ink-primary">{campaignType}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-ink-muted">Qualifiers</span>
              <span className="text-ink-primary">{numQualifiers}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-ink-muted">PP Per Qualifier</span>
              <span className="text-ink-primary">{ppPerQualifier} PP</span>
            </div>
            <div className="border-t border-line pt-sm flex justify-between">
              <span className="text-ink-muted font-medium">Total Escrow</span>
              <span className="text-h3 font-display text-ink-primary">
                {totalEscrow.toLocaleString()} PP
              </span>
            </div>
          </div>

          <div className="flex justify-between">
            <Button variant="ghost" onClick={() => setStep(2)}>
              <ArrowLeft className="h-4 w-4" /> Back
            </Button>
            <Button
              variant="jungle"
              onClick={() => createMutation.mutate()}
              disabled={createMutation.isLoading}
            >
              {createMutation.isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Megaphone className="h-4 w-4" />
              )}
              <span>{createMutation.isLoading ? 'Creating...' : 'Create Campaign'}</span>
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
