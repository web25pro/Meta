'use client';

import { useQuery, useMutation, useQueryClient } from 'react-query';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Plus,
  Megaphone,
  Users,
  Trophy,
  DollarSign,
  Loader2,
  CheckCircle2,
  Clock,
  AlertCircle,
} from 'lucide-react';
import { cn, Card, Button, Badge, Skeleton, EmptyState } from '@meta-jungle/ui';
import apiClient from '@/lib/api';
import { toast } from 'sonner';

interface UserCampaign {
  id: string;
  title: string;
  description: string;
  campaign_type: string;
  status: string;
  num_qualifiers: number;
  pp_per_qualifier: number;
  total_escrow: number;
  pp_distributed: number;
  pp_refunded: number;
  total_participants: number;
  starts_at: string | null;
  ends_at: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  draft: 'neutral',
  funding_required: 'amber',
  funded: 'cobalt',
  active: 'jungle',
  paused: 'amber',
  ended: 'neutral',
  completed: 'gold',
  rewards_distributed: 'jungle',
};

export default function MyCampaignsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery(
    'myCampaigns',
    async () => {
      const { data } = await apiClient.get('/campaigns/my-campaigns');
      return data as { campaigns: UserCampaign[]; total: number };
    },
    { staleTime: 30_000 },
  );

  const fundMutation = useMutation(
    async (campaignId: string) => {
      const { data } = await apiClient.post(`/campaigns/${campaignId}/fund`);
      return data;
    },
    {
      onSuccess: () => {
        toast.success('Campaign funded!');
        queryClient.invalidateQueries('myCampaigns');
        queryClient.invalidateQueries('membershipStatus');
      },
      onError: (err: any) => {
        toast.error(err?.response?.data?.detail || 'Failed to fund campaign');
      },
    },
  );

  const finalizeMutation = useMutation(
    async (campaignId: string) => {
      const { data } = await apiClient.post(`/campaigns/${campaignId}/finalize`);
      return data;
    },
    {
      onSuccess: () => {
        toast.success('Campaign finalized and rewards distributed!');
        queryClient.invalidateQueries('myCampaigns');
      },
      onError: (err: any) => {
        toast.error(err?.response?.data?.detail || 'Failed to finalize campaign');
      },
    },
  );

  return (
    <div className="animate-page-in space-y-xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-h1 text-ink-primary">My Campaigns</h1>
          <p className="text-body text-ink-muted">
            Manage your created campaigns, track participants, and distribute rewards.
          </p>
        </div>
        <Link href="/dashboard/campaigns/create">
          <Button variant="jungle">
            <Plus className="h-4 w-4" />
            <span>Create Campaign</span>
          </Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="space-y-md">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="p-lg">
              <Skeleton className="h-6 w-48 mb-sm" />
              <Skeleton className="h-4 w-full mb-sm" />
              <Skeleton className="h-4 w-3/4" />
            </Card>
          ))}
        </div>
      ) : data && data.campaigns.length > 0 ? (
        <div className="space-y-md">
          {data.campaigns.map((campaign) => (
            <Card key={campaign.id} className="p-lg">
              <div className="flex flex-col gap-md sm:flex-row sm:items-start sm:justify-between">
                <div className="space-y-sm flex-1">
                  <div className="flex items-center gap-sm">
                    <h3 className="font-display text-h3 text-ink-primary">
                      {campaign.title}
                    </h3>
                    <Badge tone={STATUS_COLORS[campaign.status] as any || 'neutral'}>
                      {campaign.status.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                  <p className="text-body text-ink-muted line-clamp-2">
                    {campaign.description}
                  </p>
                  <div className="flex flex-wrap gap-lg text-body">
                    <span className="flex items-center gap-sm text-ink-muted">
                      <Users className="h-4 w-4" />
                      {campaign.total_participants} participants
                    </span>
                    <span className="flex items-center gap-sm text-ink-muted">
                      <Trophy className="h-4 w-4" />
                      {campaign.num_qualifiers} qualifiers
                    </span>
                    <span className="flex items-center gap-sm text-ink-muted">
                      <DollarSign className="h-4 w-4" />
                      {campaign.total_escrow.toLocaleString()} PP escrow
                    </span>
                  </div>
                </div>

                <div className="flex gap-sm">
                  {campaign.status === 'funding_required' && (
                    <Button
                      variant="gold"
                      size="sm"
                      onClick={() => fundMutation.mutate(campaign.id)}
                      disabled={fundMutation.isLoading}
                    >
                      {fundMutation.isLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <DollarSign className="h-4 w-4" />
                      )}
                      Fund
                    </Button>
                  )}
                  {(campaign.status === 'active' || campaign.status === 'ended') && (
                    <Button
                      variant="jungle"
                      size="sm"
                      onClick={() => finalizeMutation.mutate(campaign.id)}
                      disabled={finalizeMutation.isLoading}
                    >
                      {finalizeMutation.isLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <CheckCircle2 className="h-4 w-4" />
                      )}
                      Finalize
                    </Button>
                  )}
                  <Link href={`/dashboard/campaigns/${campaign.id}/leaderboard`}>
                    <Button variant="ghost" size="sm">
                      <Trophy className="h-4 w-4" />
                      Leaderboard
                    </Button>
                  </Link>
                </div>
              </div>

              {/* Stats bar */}
              {campaign.pp_distributed > 0 && (
                <div className="mt-md flex gap-lg rounded-card bg-bg-elevated p-md text-body">
                  <span className="text-ink-muted">
                    Distributed: <span className="font-medium text-reward-jungle">{campaign.pp_distributed.toLocaleString()} PP</span>
                  </span>
                  {campaign.pp_refunded > 0 && (
                    <span className="text-ink-muted">
                      Refunded: <span className="font-medium text-ink-primary">{campaign.pp_refunded.toLocaleString()} PP</span>
                    </span>
                  )}
                </div>
              )}
            </Card>
          ))}
        </div>
      ) : (
        <Card className="p-xl">
          <EmptyState
            title="No campaigns yet"
            description="Create your first campaign to start rewarding top contributors."
          />
          <div className="mt-md text-center">
            <Link href="/dashboard/campaigns/create">
              <Button variant="jungle">
                <Plus className="h-4 w-4" />
                <span>Create Your First Campaign</span>
              </Button>
            </Link>
          </div>
        </Card>
      )}
    </div>
  );
}
