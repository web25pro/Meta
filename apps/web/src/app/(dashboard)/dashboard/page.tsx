'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from 'react-query';
import {
  Trophy,
  Target,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';
import apiClient, { isAuthenticated } from '@/lib/api';
import { User, DashboardStats } from '@/types';

export default function DashboardPage() {
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/auth/login');
    }
  }, [router]);

  const { data: user, isLoading: userLoading } = useQuery<User>('currentUser', async () => {
    const response = await apiClient.get('/users/me');
    return response.data;
  });

  const { data: stats, isLoading: statsLoading } = useQuery<DashboardStats>(
    'dashboardStats',
    async () => {
      // Mock data for now - replace with actual API call when endpoint is ready
      return {
        total_tasks: 12,
        pending_submissions: 3,
        total_points: 450,
        current_rank: 5,
        tasks_completed: 8,
        tasks_pending: 4,
      };
    }
  );

  if (userLoading || statsLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-primary-600 to-secondary-600 rounded-xl p-8 text-white">
        <h1 className="text-3xl font-bold mb-2">Welcome back, {user?.name}!</h1>
        <p className="text-primary-100">Here&apos;s what&apos;s happening with your tasks today.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={<Target className="h-6 w-6" />}
          title="Total Tasks"
          value={stats?.total_tasks || 0}
          color="bg-blue-500"
        />
        <StatCard
          icon={<Clock className="h-6 w-6" />}
          title="Pending"
          value={stats?.tasks_pending || 0}
          color="bg-yellow-500"
        />
        <StatCard
          icon={<Trophy className="h-6 w-6" />}
          title="Total Points"
          value={stats?.total_points || 0}
          color="bg-primary-500"
        />
        <StatCard
          icon={<TrendingUp className="h-6 w-6" />}
          title="Rank"
          value={`#${stats?.current_rank || '-'}`}
          color="bg-secondary-500"
        />
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tasks Overview */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Tasks Overview</h2>
          <div className="space-y-4">
            <TaskStatusItem
              icon={<CheckCircle className="h-5 w-5 text-green-500" />}
              label="Completed"
              count={stats?.tasks_completed || 0}
            />
            <TaskStatusItem
              icon={<Clock className="h-5 w-5 text-yellow-500" />}
              label="In Progress"
              count={stats?.tasks_pending || 0}
            />
            <TaskStatusItem
              icon={<AlertCircle className="h-5 w-5 text-red-500" />}
              label="Pending Submissions"
              count={stats?.pending_submissions || 0}
            />
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <QuickActionButton
              href="/dashboard/tasks"
              label="View All Tasks"
              icon={<Target className="h-5 w-5" />}
            />
            <QuickActionButton
              href="/dashboard/leaderboard"
              label="Check Leaderboard"
              icon={<Trophy className="h-5 w-5" />}
            />
            <QuickActionButton
              href="/dashboard/points"
              label="Points History"
              icon={<TrendingUp className="h-5 w-5" />}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  icon,
  title,
  value,
  color,
}: {
  icon: React.ReactNode;
  title: string;
  value: number | string;
  color: string;
}) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <div className={`${color} p-3 rounded-lg text-white`}>{icon}</div>
      </div>
      <div className="text-3xl font-bold text-gray-900 mb-1">{value}</div>
      <div className="text-sm text-gray-600">{title}</div>
    </div>
  );
}

function TaskStatusItem({
  icon,
  label,
  count,
}: {
  icon: React.ReactNode;
  label: string;
  count: number;
}) {
  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
      <div className="flex items-center space-x-3">
        {icon}
        <span className="text-gray-700">{label}</span>
      </div>
      <span className="font-semibold text-gray-900">{count}</span>
    </div>
  );
}

function QuickActionButton({
  href,
  label,
  icon,
}: {
  href: string;
  label: string;
  icon: React.ReactNode;
}) {
  return (
    <a
      href={href}
      className="flex items-center space-x-3 p-3 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
    >
      {icon}
      <span className="text-gray-700 font-medium">{label}</span>
    </a>
  );
}
