'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from 'react-query';
import { CheckCircle, Mail, Loader2, Target, Flame, Users, Award } from 'lucide-react';
import { toast } from 'sonner';
import {
  ReputationRings,
  StatCard,
  RoleBadge,
  Skeleton,
  Foliage,
  cn,
  type Role,
} from '@meta-jungle/ui';
import { metajungleAPI } from '@/api/metajungle';
import { useAuth } from '@/context/auth-context';
import apiClient from '@/lib/api';

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
  const { user, isLoading: authLoading } = useAuth();
  const [stats, setStats] = useState<CommunityUserStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const { data: rep } = useQuery('mjReputation', metajungleAPI.getReputation, {
    retry: false,
    enabled: !!user,
  });

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.push('/auth/login');
      return;
    }
    const fetchStats = async () => {
      try {
        // Fetch real user stats from the API
        const { data } = await apiClient.get('/users/me/stats');
        setStats({
          user_id: user.id,
          username: user.username || 'User',
          email: user.email,
          email_verified: user.email_verified || false,
          points: data.points ?? 0,
          xp: data.xp ?? 0,
          level: data.level ?? 1,
          current_streak: data.current_streak ?? 0,
          best_streak: data.best_streak ?? 0,
          total_submissions: data.total_submissions ?? 0,
          total_tasks_completed: data.total_tasks_completed ?? 0,
          referrals_count: data.referrals_count ?? 0,
          created_at: data.created_at ?? new Date().toISOString(),
        });
      } catch {
        toast.error('Failed to load profile');
      } finally {
        setIsLoading(false);
      }
    };
    fetchStats();
  }, [user, authLoading, router]);

  if (isLoading) {
    return (
      <div className="space-y-xl">
        <Skeleton className="h-48 w-full" />
        <div className="grid grid-cols-2 gap-lg lg:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    );
  }

  if (!stats) {
    return <div className="text-center text-ink-muted">Failed to load profile</div>;
  }

  // Reputation data from API (or zeros if not available)
  const r = rep ?? { activity_score: 0, reputation_score: 0, influence_score: 0, role: 'Explorer' };

  return (
    <div className="animate-page-in space-y-xl">
      {/* Navy header */}
      <div className="relative overflow-hidden rounded-card bg-hero-gradient p-xl text-center text-ink-inverse">
        <div className="bamboo-texture pointer-events-none absolute inset-0 opacity-40" />
        <Foliage />
        <div className="relative flex flex-col items-center">
          <ReputationRings
            activity={r.activity_score}
            reputation={r.reputation_score}
            influence={r.influence_score}
            size={108}
          />
          <h1 className="mt-md font-display text-h1 text-ink-inverse">{stats.username}</h1>
          <div className="mt-sm flex items-center gap-sm">
            <RoleBadge role={r.role as Role} />
            {stats.email_verified ? (
              <span className="flex items-center gap-1 rounded-pill bg-success/15 px-sm py-[2px] text-label text-success">
                <CheckCircle className="h-4 w-4" /> Verified
              </span>
            ) : (
              <span className="flex items-center gap-1 rounded-pill bg-reward-amber/15 px-sm py-[2px] text-label text-reward-amber">
                <Mail className="h-4 w-4" /> Unverified
              </span>
            )}
          </div>
          <p className="mt-sm text-label text-brand-ice">{stats.email}</p>
        </div>
      </div>

      {/* Score legend */}
      <div className="flex flex-wrap gap-lg text-label">
        <Legend color="bg-brand-sky" label="Activity" value={r.activity_score} />
        <Legend color="bg-brand-cobalt" label="Reputation" value={r.reputation_score} />
        <Legend color="bg-reward-gold" label="Influence" value={r.influence_score} />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-lg lg:grid-cols-4">
        <StatCard icon={<Award className="h-6 w-6" />} label="PP Earned" value={stats.points} isPP />
        <StatCard icon={<Target className="h-6 w-6" />} label="Quests Done" value={stats.total_tasks_completed} />
        <StatCard icon={<Flame className="h-6 w-6" />} label="Best Streak" value={stats.best_streak} />
        <StatCard icon={<Users className="h-6 w-6" />} label="Referrals" value={stats.referrals_count} />
      </div>
    </div>
  );
}

function Legend({ color, label, value }: { color: string; label: string; value: number }) {
  return (
    <span className="flex items-center gap-sm text-ink-muted">
      <span className={cn('h-3 w-3 rounded-full', color)} />
      {label} <span className="font-display text-ink-primary">{value}</span>
    </span>
  );
}
