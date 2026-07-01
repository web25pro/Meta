'use client';

export const dynamic = 'force-dynamic';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@meta-jungle/ui';
import { communityAPI } from '@/api/community';
import { AuthShell } from '@/components/auth-shell';

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
        setTimeout(() => router.push('/auth/login'), 2000);
      } catch (error: any) {
        setStatus('error');
        const msg = error.response?.data?.detail || error.message || 'Email verification failed';
        setMessage(msg);
        toast.error(msg);
      }
    };
    verifyEmail();
  }, [token, router]);

  return (
    <AuthShell title="Email verification" subtitle="Verifying your jungle ID">
      <div className="space-y-lg text-center">
        {status === 'loading' && (
          <>
            <Loader2 className="mx-auto h-14 w-14 animate-spin text-brand-cobalt" />
            <p className="text-body text-ink-primary">Verifying your email address…</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-success/15">
              <CheckCircle className="h-8 w-8 text-success" />
            </div>
            <p className="font-display text-h2 text-ink-primary">Email verified!</p>
            <p className="text-body text-ink-muted">{message}</p>
            <p className="text-label text-ink-muted">Redirecting to login…</p>
            <Link href="/auth/login" className="block">
              <Button className="w-full">Go to Login</Button>
            </Link>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-danger/15">
              <XCircle className="h-8 w-8 text-danger" />
            </div>
            <p className="font-display text-h2 text-ink-primary">Verification failed</p>
            <p className="text-body text-ink-muted">{message}</p>
            <Link href="/auth/resend-verification" className="block">
              <Button className="w-full">Resend verification email</Button>
            </Link>
          </>
        )}
      </div>
    </AuthShell>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center bg-bg-dark text-ink-inverse">Loading…</div>}>
      <VerifyEmailContent />
    </Suspense>
  );
}
