'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Star, Award, Zap, Flame, Mail, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { communityAPI } from '@/api/community';
import { useAuth } from '@/context/auth-context';

interface CommunityUserStats {
  user_id: string;
  username: string;
  email: string;
  email_verified: boolean;
  points: number;
  xp: number;
  level: number;
  current_streak: number;
  best_streak: number;
  total_submissions: number;
  total_tasks_completed: number;
  referrals_count: number;
  created_at: string;
}

export default function ProfilePage() {
  const router = useRouter();
  const { user } = useAuth();
  const [stats, setStats] = useState<CommunityUserStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }

    // Fetch user stats from community API
    const fetchStats = async () => {
      try {
        // For now, we'll create mock stats since the endpoint might not exist yet
        // In production, you'd call an API endpoint like:
        // const response = await communityAPI.getUserStats();
        
        // Mock data
        setStats({
          user_id: user.id,
          username: user.username || 'User',
          email: user.email,
          email_verified: user.email_verified || false,
          points: 1250,
          xp: 4560,
          level: 3,
          current_streak: 5,
          best_streak: 12,
          total_submissions: 8,
          total_tasks_completed: 15,
          referrals_count: 2,
          created_at: new Date().toISOString(),
        });
      } catch (error) {
        toast.error('Failed to load profile');
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, [user, router]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 text-primary-600 animate-spin" />
      </div>
    );
  }

  if (!stats) {
    return <div className="text-center text-gray-600">Failed to load profile</div>;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Profile</h1>
        <p className="text-gray-600 mt-2">Your community statistics and account information</p>
      </div>

      {/* User Info Card */}
      <div className="bg-white rounded-lg shadow p-6 space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{stats.username}</h2>
            <p className="text-gray-600">{stats.email}</p>
          </div>
          <div className="flex items-center space-x-2">
            {stats.email_verified ? (
              <div className="flex items-center space-x-1 text-green-600 bg-green-50 px-3 py-1 rounded-full text-sm font-medium">
                <CheckCircle className="h-4 w-4" />
                <span>Verified</span>
              </div>
            ) : (
              <div className="flex items-center space-x-1 text-yellow-600 bg-yellow-50 px-3 py-1 rounded-full text-sm font-medium">
                <Mail className="h-4 w-4" />
                <span>Unverified</span>
              </div>
            )}
          </div>
        </div>
        {!stats.email_verified && (
          <div className="bg-yellow-50 border border-yellow-200 rounded p-4 text-sm text-gray-700">
            <p className="font-semibold mb-2">Verify your email to unlock full features</p>
            <button
              onClick={() => router.push('/resend-verification')}
              className="text-yellow-600 font-medium hover:underline"
            >
              Resend verification email
            </button>
          </div>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Points */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Points</h3>
            <Star className="h-5 w-5 text-yellow-500" />
          </div>
          <p className="text-3xl font-bold text-gray-900">{stats.points.toLocaleString()}</p>
          <p className="text-xs text-gray-500 mt-1">Total earned</p>
        </div>

        {/* Level */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Level</h3>
            <Award className="h-5 w-5 text-purple-500" />
          </div>
          <p className="text-3xl font-bold text-gray-900">{stats.level}</p>
          <p className="text-xs text-gray-500 mt-1">Current rank</p>
        </div>

        {/* Current Streak */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Current Streak</h3>
            <Flame className="h-5 w-5 text-orange-500" />
          </div>
          <p className="text-3xl font-bold text-gray-900">{stats.current_streak}</p>
          <p className="text-xs text-gray-500 mt-1">days in a row</p>
        </div>

        {/* Best Streak */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Best Streak</h3>
            <Zap className="h-5 w-5 text-blue-500" />
          </div>
          <p className="text-3xl font-bold text-gray-900">{stats.best_streak}</p>
          <p className="text-xs text-gray-500 mt-1">max consecutive days</p>
        </div>
      </div>

      {/* Activity Stats */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-6">Activity</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <p className="text-sm text-gray-600 mb-2">Tasks Completed</p>
            <p className="text-2xl font-bold text-gray-900">{stats.total_tasks_completed}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-2">Submissions</p>
            <p className="text-2xl font-bold text-gray-900">{stats.total_submissions}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-2">Referrals</p>
            <p className="text-2xl font-bold text-gray-900">{stats.referrals_count}</p>
          </div>
        </div>
      </div>

      {/* Account Created */}
      <div className="text-center text-sm text-gray-600">
        <p>Account created {new Date(stats.created_at).toLocaleDateString()}</p>
      </div>
    </div>
  );
}
