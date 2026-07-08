'use client';

import { useEffect } from 'react';
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
} from 'lucide-react';
import {
  StatCard,
  Card,
  Button,
  Skeleton,
  QuestCard,
  PandaMascot,
  Foliage,
} from '@meta-jungle/ui';
import apiClient, { isAuthenticated } from '@/lib/api';
import { User, DashboardStats } from '@/types';

export default function DashboardPage() {
  const router = useRouter();

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

  return (
    <div className="animate-page-in space-y-xl">
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
            <Link href="/dashboard/tasks" className="mt-lg inline-block">
              <Button variant="jungle">
                Continue Earning <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
          <div className="hidden shrink-0 sm:block">
            <PandaMascot size={120} />
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

      <div className="grid gap-lg lg:grid-cols-3">
        {/* Active quests */}
        <div className="space-y-md lg:col-span-2">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-h2 text-ink-primary">Continue Earning</h2>
            <Link href="/dashboard/tasks" className="text-label font-medium text-brand-cobalt">
              View all quests →
            </Link>
          </div>
          <QuestCard
            title="Follow @LPanda on X"
            description="Connect your X account and follow to earn your first reward."
            ppReward={50}
            status="available"
          />
          <QuestCard
            title="Daily check-in"
            description="Log in every day to grow your streak bonus."
            ppReward={10}
            progress={70}
            status="in-progress"
          />
          <QuestCard
            title="Refer a friend"
            description="Invite a friend who completes 3 tasks in 7 days."
            ppReward={300}
            status="available"
          />
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
