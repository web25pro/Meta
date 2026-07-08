'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Copy, Check, Users, Loader2, Gift, UserCheck } from 'lucide-react';
import { toast } from 'sonner';
import { Card, StatCard, Button, Skeleton } from '@meta-jungle/ui';
import { communityAPI } from '@/api/community';
import { useAuth } from '@/context/auth-context';
import apiClient from '@/lib/api';

interface ReferralData {
  referral_code: string;
  referral_link: string;
  total_referrals: number;
  successful_referrals: number;
  referral_earnings: number;
}

export default function ReferralsPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const [referralData, setReferralData] = useState<ReferralData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.push('/auth/login');
      return;
    }
    const fetchReferralData = async () => {
      const baseUrl = typeof window !== 'undefined' ? window.location.origin : '';
      try {
        const [codeRes, statsRes] = await Promise.all([
          communityAPI.getReferralCode(),
          apiClient.get('/community/referral-stats').catch(() => ({ data: {} })),
        ]);
        setReferralData({
          referral_code: codeRes.referral_code,
          referral_link: `${baseUrl}/auth/register?ref=${codeRes.referral_code}`,
          total_referrals: statsRes.data.total_referrals ?? 0,
          successful_referrals: statsRes.data.successful_referrals ?? 0,
          referral_earnings: statsRes.data.referral_earnings ?? 0,
        });
      } catch {
        toast.error('Failed to load referral data');
      } finally {
        setIsLoading(false);
      }
    };
    fetchReferralData();
  }, [user, authLoading, router]);

  const copyToClipboard = async () => {
    if (!referralData) return;
    try {
      await navigator.clipboard.writeText(referralData.referral_link);
      setCopied(true);
      toast.success('Referral link copied!');
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Failed to copy link');
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-xl">
        <Skeleton className="h-40 w-full" />
        <div className="grid grid-cols-1 gap-lg sm:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    );
  }

  if (!referralData) {
    return <div className="text-center text-ink-muted">Failed to load referral data</div>;
  }

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Referrals</h1>
        <p className="mt-1 text-body text-ink-muted">
          Invite friends to the jungle — you both earn when they get active.
        </p>
      </div>

      {/* Referral link card — navy + bamboo */}
      <div className="relative overflow-hidden rounded-card bg-bg-dark p-xl text-ink-inverse">
        <div className="bamboo-texture pointer-events-none absolute inset-0" />
        <div className="relative">
          <h2 className="font-display text-h2 text-ink-inverse">Your referral link</h2>
          <div className="mt-md flex items-center gap-sm rounded-card bg-white/10 p-sm">
            <code className="flex-1 break-all px-sm font-mono text-label text-brand-ice">
              {referralData.referral_link}
            </code>
            <Button size="sm" variant="gold" onClick={copyToClipboard}>
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              {copied ? 'Copied' : 'Copy'}
            </Button>
          </div>
          <p className="mt-md text-label text-brand-ice">
            Referral reward: 300 PP when your friend completes 3 quests in 7 days.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-lg sm:grid-cols-3">
        <StatCard icon={<Users className="h-6 w-6" />} label="Total Referrals" value={referralData.total_referrals} />
        <StatCard icon={<UserCheck className="h-6 w-6" />} label="Successful" value={referralData.successful_referrals} />
        <StatCard icon={<Gift className="h-6 w-6" />} label="PP Earned" value={referralData.referral_earnings} isPP />
      </div>
    </div>
  );
}
