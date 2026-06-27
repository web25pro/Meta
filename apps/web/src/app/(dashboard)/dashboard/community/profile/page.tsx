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
      router.push('/auth/login');
      return;
    }

    // Fetch user stats from community API
    const fetchStats = async () => {
      try {
        // For now, we'll create mock stats since the endpoint might not exist yet
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
        <h1 className="text-3xl font-bold text-white">🐼 Your Profile</h1>
        <p className="text-primary-200 mt-2">Your jungle warrior statistics and account information</p>
      </div>

      {/* User Info Card */}
      <div className="bg-primary-700 bg-opacity-50 backdrop-blur border border-primary-600 rounded-lg p-6 space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white">{stats.username}</h2>
            <p className="text-primary-200">{stats.email}</p>
          </div>
          <div className="flex items-center space-x-2">
            {stats.email_verified ? (
              <div className="flex items-center space-x-1 text-green-400 bg-green-900 bg-opacity-30 px-3 py-1 rounded-full text-sm font-medium border border-green-700">
                <CheckCircle className="h-4 w-4" />
                <span>Verified</span>
              </div>
            ) : (
              <div className="flex items-center space-x-1 text-yellow-400 bg-yellow-900 bg-opacity-30 px-3 py-1 rounded-full text-sm font-medium border border-yellow-700">
                <Mail className="h-4 w-4" />
                <span>Unverified</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
