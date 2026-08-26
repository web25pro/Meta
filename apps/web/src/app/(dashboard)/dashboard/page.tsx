'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useQuery } from 'react-query';
import {
  Trophy,
  Target,
  Wallet,
  Flame,
  ArrowRight,
  CheckCircle,
  Clock,
  AlertCircle,
  Crown,
} from 'lucide-react';
import {
  StatCard,
  Card,
  Button,
  Skeleton,
  QuestCard,
  PandaMascot,
  Foliage,
  ForestBackground,
  ForestParticles,
  getPandaTier,
} from '@meta-jungle/ui';
import apiClient, { isAuthenticated } from '@/lib/api';
import { User, DashboardStats } from '@/types';
import { metajungleAPI, type ApiQuest } from '@/api/metajungle';
import { MembershipStatusCard } from '@/components/membership-status';
import { ConnectWalletButton } from '@/components/connect-wallet-button';
import { UpgradeTierModal } from '@/components/upgrade-tier-modal';
import { premiumAPI, MembershipStatus } from '@/api/premium';

export default function DashboardPage() {
  const router = useRouter();
  const [upgradeModalOpen, setUpgradeModalOpen] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) router.push('/auth/login');
  }, [router]);

  const { data: user, isLoading: userLoading } = useQuery<User>(
    'currentUser',
    async () => (await apiClient.get('/users/me')).data,
  );

  const { data: stats, isLoading: statsLoading } = useQuery<DashboardStats>(
    'dashboardStats',
    async () => {
      const [statsRes, rankRes] = await Promise.all([
        apiClient.get('/users/me/stats'),
        apiClient.get('/leaderboard/user/me/rank').catch(() => ({ data: { rank: null } })),
      ]);
      return {
        total_tasks: statsRes.data.total_tasks ?? 0,
        pending_submissions: statsRes.data.pending_submissions ?? 0,
        total_points: statsRes.data.total_points ?? 0,
        current_rank: rankRes.data.rank ?? null,
        tasks_completed: statsRes.data.tasks_completed ?? 0,
        tasks_pending: statsRes.data.tasks_pending ?? 0,
      };
    },
  );

  const { data: quests } = useQuery<ApiQuest[]>(
    'mjQuests',
    metajungleAPI.listQuests,
    { retry: false },
  );

  const { data: membershipStatus } = useQuery<MembershipStatus>(
    'membershipStatus',
    () => premiumAPI.getStatus(),
    { staleTime: 60_000 },
  );

  if (userLoading || statsLoading) {
    return (
      <div className="space-y-lg">
        <Skeleton className="h-28 w-full" />
        <div className="grid grid-cols-2 gap-lg lg:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  const pandaTier = getPandaTier(stats?.total_points ?? 0);

  return (
    <div className="animate-page-in space-y-xl">
      {/* Forest ambient layers */}
      <ForestBackground />
      <ForestParticles />

      {/* Welcome hero — gradient + bamboo texture */}
      <div className="relative overflow-hidden rounded-card bg-hero-gradient p-xl text-ink-inverse">
        <div className="bamboo-texture pointer-events-none absolute inset-0 opacity-40" />
        <Foliage />
        <div className="relative flex items-center justify-between gap-lg">
          <div>
            <h1 className="font-display text-h1 text-ink-inverse">
              Welcome back, {user?.name || 'Panda'}
            </h1>
            <p className="mt-sm text-brand-ice">
              Your actions have value here. Keep your streak alive and climb the jungle.
            </p>
            <div className="mt-lg flex flex-col gap-sm sm:flex-row sm:flex-wrap">
              <Link href="/dashboard/tasks">
                <Button variant="jungle" className="w-full sm:w-auto">
                  Continue Earning <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <ConnectWalletButton variant="gold" className="w-full sm:w-auto" />
              <Button
                variant="gold"
                onClick={() => setUpgradeModalOpen(true)}
                className="w-full sm:w-auto"
              >
                <Crown className="h-4 w-4" /> Upgrade Tier
              </Button>
            </div>
          </div>
          <div className="hidden shrink-0 sm:block">
            <PandaMascot tier={pandaTier} />
          </div>
        </div>
      </div>

      {/* Hero stats row */}
      <div className="grid grid-cols-2 gap-lg lg:grid-cols-4">
        <StatCard
          icon={<Wallet className="h-6 w-6" />}
          label="PP Balance"
          value={stats?.total_points ?? 0}
          isPP
        />
        <StatCard
          icon={<Trophy className="h-6 w-6" />}
          label="Rank"
          value={`#${stats?.current_rank ?? '—'}`}
        />
        <StatCard
          icon={<Target className="h-6 w-6" />}
          label="Quests Done"
          value={stats?.tasks_completed ?? 0}
        />
        <StatCard
          icon={<Flame className="h-6 w-6" />}
          label="Streak Days"
          value={user?.current_streak ?? 0}
        />
      </div>

      {/* Membership status */}
      <MembershipStatusCard />

      <div className="grid gap-lg lg:grid-cols-3">
        {/* Active quests */}
        <div className="space-y-md lg:col-span-2">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-h2 text-ink-primary">Continue Earning</h2>
            <Link href="/dashboard/tasks" className="text-label font-medium text-brand-cobalt">
              View all quests →
            </Link>
          </div>
          {quests && quests.length > 0 ? (
            quests.slice(0, 3).map((q) => (
              <QuestCard
                key={q.id}
                title={q.title}
                description={q.description}
                ppReward={q.pp_reward}
                status="available"
              />
            ))
          ) : (
            <div className="rounded-card border border-line bg-bg-primary p-lg text-center text-ink-muted">
              No quests available right now. Check back soon!
            </div>
          )}
        </div>

        {/* Task overview */}
        <Card className="space-y-md">
          <h2 className="font-display text-h2 text-ink-primary">Quest Overview</h2>
          <OverviewItem
            icon={<CheckCircle className="h-5 w-5 text-success" />}
            label="Completed"
            count={stats?.tasks_completed ?? 0}
          />
          <OverviewItem
            icon={<Clock className="h-5 w-5 text-reward-amber" />}
            label="In Progress"
            count={stats?.tasks_pending ?? 0}
          />
          <OverviewItem
            icon={<AlertCircle className="h-5 w-5 text-brand-sky" />}
            label="Pending Review"
            count={stats?.pending_submissions ?? 0}
          />
          <Link href="/dashboard/leaderboard">
            <Button variant="ghost" className="w-full">
              Check Leaderboard
            </Button>
          </Link>
        </Card>
      </div>

      {/* Upgrade tier modal */}
      <UpgradeTierModal
        isOpen={upgradeModalOpen}
        onClose={() => setUpgradeModalOpen(false)}
        currentTier={membershipStatus?.tier || 'standard'}
        currentNftCount={membershipStatus?.nft_count || 0}
      />
    </div>
  );
}

function OverviewItem({
  icon,
  label,
  count,
}: {
  icon: React.ReactNode;
  label: string;
  count: number;
}) {
  return (
    <div className="flex items-center justify-between rounded-card bg-bg-surface px-md py-3">
      <div className="flex items-center gap-md">
        {icon}
        <span className="text-body text-ink-primary">{label}</span>
      </div>
      <span className="font-display text-body text-ink-primary">{count}</span>
    </div>
  );
}
