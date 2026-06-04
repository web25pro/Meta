'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { Trophy, Star, Users, Target } from 'lucide-react';
import { useAuth } from '@/context/auth-context';

export default function DashboardPage() {
  const router = useRouter();
  const { user } = useAuth();

  useEffect(() => {
    if (!user) {
      router.push('/login');
    }
  }, [user, router]);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-gray-900">Welcome back, {user?.username || 'User'}! 👋</h1>
        <p className="text-gray-600 mt-2">Here's your community dashboard</p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Points</h3>
            <Star className="h-5 w-5 text-yellow-500" />
          </div>
          <p className="text-3xl font-bold text-gray-900">1,250</p>
          <p className="text-xs text-gray-500 mt-1">+50 this week</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Level</h3>
            <Trophy className="h-5 w-5 text-purple-500" />
          </div>
          <p className="text-3xl font-bold text-gray-900">3</p>
          <p className="text-xs text-gray-500 mt-1">1,200 XP to Level 4</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Streak</h3>
            <Target className="h-5 w-5 text-orange-500" />
          </div>
          <p className="text-3xl font-bold text-gray-900">5</p>
          <p className="text-xs text-gray-500 mt-1">days in a row</p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Referrals</h3>
            <Users className="h-5 w-5 text-blue-500" />
          </div>
          <p className="text-3xl font-bold text-gray-900">2</p>
          <p className="text-xs text-gray-500 mt-1">+1,000 points earned</p>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link
          href="/dashboard/community/profile"
          className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition"
        >
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-lg font-bold text-gray-900">Your Profile</h3>
              <p className="text-sm text-gray-600 mt-1">View your stats and achievements</p>
            </div>
            <Trophy className="h-6 w-6 text-primary-600" />
          </div>
          <div className="text-primary-600 font-medium text-sm">View Profile →</div>
        </Link>

        <Link
          href="/dashboard/community/referrals"
          className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition"
        >
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-lg font-bold text-gray-900">Invite Friends</h3>
              <p className="text-sm text-gray-600 mt-1">Share your referral link and earn rewards</p>
            </div>
            <Users className="h-6 w-6 text-primary-600" />
          </div>
          <div className="text-primary-600 font-medium text-sm">Share Link →</div>
        </Link>

        <Link
          href="/dashboard/community/settings"
          className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition"
        >
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-lg font-bold text-gray-900">Account Settings</h3>
              <p className="text-sm text-gray-600 mt-1">Manage your preferences and security</p>
            </div>
            <Target className="h-6 w-6 text-primary-600" />
          </div>
          <div className="text-primary-600 font-medium text-sm">Go to Settings →</div>
        </Link>

        <Link
          href="/"
          className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition"
        >
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-lg font-bold text-gray-900">View Tasks</h3>
              <p className="text-sm text-gray-600 mt-1">Start completing tasks and earning points</p>
            </div>
            <Star className="h-6 w-6 text-primary-600" />
          </div>
          <div className="text-primary-600 font-medium text-sm">View Tasks →</div>
        </Link>
      </div>

      {/* Announcements */}
      <div className="bg-gradient-to-r from-primary-50 to-secondary-50 rounded-lg border border-primary-200 p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Latest Updates</h2>
        <div className="space-y-3">
          <div className="bg-white rounded-lg p-4">
            <p className="font-medium text-gray-900">🎉 New Feature: Daily Streak Rewards</p>
            <p className="text-sm text-gray-600 mt-1">Unlock bonus points for maintaining your streak!</p>
          </div>
          <div className="bg-white rounded-lg p-4">
            <p className="font-medium text-gray-900">🏆 Leaderboard Reset</p>
            <p className="text-sm text-gray-600 mt-1">Monthly leaderboard rewards are now available</p>
          </div>
        </div>
      </div>
    </div>
  );
}
