'use client';

export const dynamic = 'force-dynamic';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { CheckCircle, XCircle, Loader2, Trophy } from 'lucide-react';
import { toast } from 'sonner';
import { communityAPI } from '@/api/community';

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const verifyEmail = async () => {
      if (!token) {
        setStatus('error');
        setMessage('No verification token provided');
        return;
      }

      try {
        const response = await communityAPI.verifyEmail(token);
        setStatus('success');
        setMessage(response.message || 'Email verified successfully!');
        toast.success('Email verified!');

        // Redirect to login after 2 seconds
        setTimeout(() => {
          router.push('/login');
        }, 2000);
      } catch (error: any) {
        setStatus('error');
        const errorMessage =
          error.response?.data?.detail || error.message || 'Email verification failed';
        setMessage(errorMessage);
        toast.error(errorMessage);
      }
    };

    verifyEmail();
  }, [token, router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-900 via-primary-800 to-jungle-900 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Jungle Background */}
      <div className="absolute top-0 right-0 text-9xl opacity-10">✅</div>
      <div className="absolute bottom-0 left-0 text-9xl opacity-10">📬</div>

      <div className="w-full max-w-md relative z-10">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-white rounded-full shadow-lg mb-4">
            <span className="text-3xl">🐼</span>
          </div>
          <span className="text-3xl font-bold text-white block">LPanda</span>
          <p className="text-primary-200 mt-2">Email Verification</p>
        </div>

        {/* Verification Status */}
        <div className="bg-primary-800 bg-opacity-80 backdrop-blur border border-primary-700 rounded-2xl shadow-2xl p-8 text-center">
          {status === 'loading' && (
            <div className="space-y-4">
              <Loader2 className="h-16 w-16 text-secondary-400 animate-spin mx-auto" />
              <p className="text-white font-medium">Verifying your jungle ID...</p>
              <p className="text-sm text-primary-200">Please wait while we verify your email address.</p>
            </div>
          )}

          {status === 'success' && (
            <div className="space-y-4">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-green-600 rounded-full">
                <CheckCircle className="h-8 w-8 text-white" />
              </div>
              <p className="text-white font-bold text-lg">Email Verified!</p>
              <p className="text-sm text-primary-200">{message}</p>
              <p className="text-xs text-primary-300 mt-4">Redirecting to login...</p>
              <Link
                href="/auth/login"
                className="inline-block mt-6 px-6 py-3 bg-secondary-600 text-white font-medium rounded-lg hover:bg-secondary-700 transition"
              >
                Go to Login
              </Link>
            </div>
          )}

          {status === 'error' && (
            <div className="space-y-4">
              <XCircle className="h-16 w-16 text-red-500 mx-auto" />
              <p className="text-gray-900 font-bold text-lg">Verification Failed</p>
              <p className="text-sm text-gray-600">{message}</p>
              <div className="space-y-3 mt-6">
                <p className="text-sm text-gray-600">
                  Try requesting a new verification email:
                </p>
                <Link
                  href="/auth/resend-verification"
                  className="inline-block px-6 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition"
                >
                  Resend Verification Email
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* Help Text */}
        <p className="text-center text-sm text-gray-600 mt-6">
          {status === 'error' && (
            <>
              Need help?{' '}
              <Link href="/support" className="text-primary-600 hover:underline">
                Contact support
              </Link>
            </>
          )}
        </p>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Loading...</div>}>
      <VerifyEmailContent />
    </Suspense>
  );
}
