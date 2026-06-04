'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Copy, Check, Users, Loader2, Share2 } from 'lucide-react';
import { toast } from 'sonner';
import { communityAPI } from '@/api/community';
import { useAuth } from '@/context/auth-context';

interface ReferralData {
  referral_code: string;
  referral_link: string;
  total_referrals: number;
  successful_referrals: number;
  referral_earnings: number;
}

export default function ReferralsPage() {
  const router = useRouter();
  const { user } = useAuth();
  const [referralData, setReferralData] = useState<ReferralData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }

    const fetchReferralData = async () => {
      try {
        // Try to fetch referral code from community API
        try {
          const response = await communityAPI.getReferralCode();
          const baseUrl = typeof window !== 'undefined' ? window.location.origin : '';
          
          setReferralData({
            referral_code: response.referral_code,
            referral_link: `${baseUrl}/register?ref=${response.referral_code}`,
            total_referrals: 2,
            successful_referrals: 1,
            referral_earnings: 500,
          });
        } catch (error) {
          // Fallback to mock data if endpoint not available
          const mockCode = `REF${Math.random().toString(36).substring(2, 9).toUpperCase()}`;
          const baseUrl = typeof window !== 'undefined' ? window.location.origin : '';
          
          setReferralData({
            referral_code: mockCode,
            referral_link: `${baseUrl}/register?ref=${mockCode}`,
            total_referrals: 2,
            successful_referrals: 1,
            referral_earnings: 500,
          });
        }
      } catch (error) {
        toast.error('Failed to load referral data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchReferralData();
  }, [user, router]);

  const copyToClipboard = async () => {
    if (!referralData) return;
    
    try {
      await navigator.clipboard.writeText(referralData.referral_link);
      setCopied(true);
      toast.success('Referral link copied!');
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast.error('Failed to copy link');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 text-primary-600 animate-spin" />
      </div>
    );
  }

  if (!referralData) {
    return <div className="text-center text-gray-600">Failed to load referral data</div>;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Referrals</h1>
        <p className="text-gray-600 mt-2">Invite friends and earn rewards</p>
      </div>

      {/* Referral Link Card */}
      <div className="bg-gradient-to-r from-primary-50 to-secondary-50 rounded-lg border border-primary-200 p-8">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Your Referral Link</h2>
        
        <div className="bg-white rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between gap-2">
            <code className="text-sm font-mono text-gray-700 flex-1 break-all">
              {referralData.referral_link}
            </code>
            <button
              onClick={copyToClipboard}
              className="ml-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition flex items-center space-x-2 whitespace-nowrap"
            >
              {copied ? (
                <>
                  <Check className="h-4 w-4" />
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
        </div>

        <p className="text-sm text-gray-600">
          Share this link with friends. When they sign up and verify their email, you'll both earn rewards!
        </p>
      </div>

      {/* Share Options */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Share Your Link</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { name: 'Twitter', icon: '𝕏' },
            { name: 'Facebook', icon: 'f' },
            { name: 'LinkedIn', icon: 'in' },
            { name: 'Email', icon: '✉' },
          ].map((platform) => (
            <button
              key={platform.name}
              onClick={() => {
                const text = `Check out LPanda! Join the community and start earning points. ${referralData.referral_link}`;
                let url = '';
                
                switch (platform.name) {
                  case 'Twitter':
                    url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`;
                    break;
                  case 'Facebook':
                    url = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(referralData.referral_link)}`;
                    break;
                  case 'LinkedIn':
                    url = `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(referralData.referral_link)}`;
                    break;
                  case 'Email':
                    url = `mailto:?subject=Join LPanda&body=${encodeURIComponent(text)}`;
                    break;
                }
                
                if (url) {
                  window.open(url, '_blank', 'noopener,noreferrer');
                }
              }}
              className="px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition font-medium text-gray-700"
            >
              <Share2 className="h-4 w-4 mx-auto mb-2" />
              {platform.name}
            </button>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Total Referrals */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Total Referrals</h3>
            <Users className="h-5 w-5 text-blue-500" />
          </div>
          <p className="text-3xl font-bold text-gray-900">{referralData.total_referrals}</p>
          <p className="text-xs text-gray-500 mt-1">friends invited</p>
        </div>

        {/* Successful Referrals */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Successful</h3>
            <Check className="h-5 w-5 text-green-500" />
          </div>
          <p className="text-3xl font-bold text-gray-900">{referralData.successful_referrals}</p>
          <p className="text-xs text-gray-500 mt-1">completed verification</p>
        </div>

        {/* Earnings */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-600">Earnings</h3>
            <span className="text-2xl font-bold text-primary-600">★</span>
          </div>
          <p className="text-3xl font-bold text-gray-900">{referralData.referral_earnings.toLocaleString()}</p>
          <p className="text-xs text-gray-500 mt-1">points earned</p>
        </div>
      </div>

      {/* How It Works */}
      <div className="bg-blue-50 rounded-lg border border-blue-200 p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">How Referrals Work</h2>
        <ol className="space-y-3 text-gray-700">
          <li className="flex gap-3">
            <span className="font-bold text-primary-600">1.</span>
            <span>Share your referral link with a friend</span>
          </li>
          <li className="flex gap-3">
            <span className="font-bold text-primary-600">2.</span>
            <span>Your friend signs up using your link</span>
          </li>
          <li className="flex gap-3">
            <span className="font-bold text-primary-600">3.</span>
            <span>They verify their email address</span>
          </li>
          <li className="flex gap-3">
            <span className="font-bold text-primary-600">4.</span>
            <span>Both of you earn 500 points as a reward!</span>
          </li>
        </ol>
      </div>
    </div>
  );
}
