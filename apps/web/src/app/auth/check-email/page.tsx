'use client';

export const dynamic = 'force-dynamic';

import { Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Mail } from 'lucide-react';
import { Button } from '@meta-jungle/ui';
import { AuthShell } from '@/components/auth-shell';

function CheckEmailContent() {
  const searchParams = useSearchParams();
  const email = searchParams.get('email') || 'your email';

  return (
    <AuthShell
      title="Check your email"
      subtitle="Jungle quest started!"
      footer={
        <Link href="/auth/login" className="font-semibold text-ice underline">
          Back to login
        </Link>
      }
    >
      <div className="space-y-lg text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-brand-ice">
          <Mail className="h-8 w-8 text-brand-cobalt" />
        </div>
        <p className="text-body text-ink-muted">
          We sent a verification link to{' '}
          <strong className="text-ink-primary">{email}</strong>
        </p>

        <div className="rounded-card bg-bg-surface p-md text-left">
          <p className="text-label font-medium text-ink-primary">Next steps</p>
          <ol className="mt-sm list-inside list-decimal space-y-1 text-label text-ink-muted">
            <li>Check your email inbox</li>
            <li>Open the verification email</li>
            <li>Click the verification link</li>
            <li>Start earning Panda Points</li>
          </ol>
        </div>

        <p className="text-label text-ink-muted">
          Tip: if you don&apos;t see it, check your spam folder. The link expires in 24 hours.
        </p>

        <div className="space-y-sm">
          <Link href="/auth/login" className="block">
            <Button className="w-full">Go to Login</Button>
          </Link>
          <Link href="/auth/resend-verification" className="block">
            <Button variant="ghost" className="w-full">Resend verification email</Button>
          </Link>
        </div>
      </div>
    </AuthShell>
  );
}

export default function CheckEmailPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center bg-bg-dark text-ink-inverse">Loading…</div>}>
      <CheckEmailContent />
    </Suspense>
  );
}
