'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { CheckCircle, Mail, Loader2, Target, Flame, Users, Award } from 'lucide-react';
import { toast } from 'sonner';
import {
  ReputationRings,
  StatCard,
  RoleBadge,
  Skeleton,
  cn,
} from '@meta-jungle/ui';
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
  const { user, isLoading: authLoading } = useAuth();
  const [stats, setStats] = useState<CommunityUserStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.push('/auth/login');
      return;
    }
    try {
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
    } catch {
      toast.error('Failed to load profile');
    } finally {
      setIsLoading(false);
    }
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

  return (
    <div className="animate-page-in space-y-xl">
      {/* Navy header */}
      <div className="relative overflow-hidden rounded-card bg-bg-dark p-xl text-center text-ink-inverse">
        <div className="bamboo-texture pointer-events-none absolute inset-0" />
        <div className="relative flex flex-col items-center">
          <ReputationRings activity={620} reputation={540} influence={310} size={108} />
          <h1 className="mt-md font-display text-h1 text-ink-inverse">{stats.username}</h1>
          <div className="mt-sm flex items-center gap-sm">
            <RoleBadge role="Hunter" />
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
        <Legend color="bg-brand-sky" label="Activity" value={620} />
        <Legend color="bg-brand-cobalt" label="Reputation" value={540} />
        <Legend color="bg-reward-gold" label="Influence" value={310} />
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
