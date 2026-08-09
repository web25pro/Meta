'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Mail, Trash2 } from 'lucide-react';
import { Card } from '@meta-jungle/ui';
import { useAuth } from '@/context/auth-context';

export default function CommunitySettingsPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();

  useEffect(() => {
    if (!authLoading && !user) router.push('/auth/login');
  }, [user, authLoading, router]);

  return (
    <div className="animate-page-in space-y-xl">
      <div>
        <h1 className="font-display text-h1 text-ink-primary">Account Settings</h1>
        <p className="mt-1 text-body text-ink-muted">Manage your account and security.</p>
      </div>

      <Card className="space-y-md">
        <h2 className="font-display text-h2 text-ink-primary">Account Information</h2>
        <div>
          <label className="mb-2 block text-label font-medium text-ink-primary">Email Address</label>
          <div className="flex items-center gap-sm rounded-card border border-line bg-bg-surface px-md py-3">
            <Mail className="h-5 w-5 text-brand-cobalt" />
            <span className="text-body text-ink-primary">{user?.email}</span>
          </div>
        </div>
      </Card>

      {/*
        Change Password and Delete Account previously reported success without
        calling anything. The controls stay visible but disabled until
        POST /auth/change-password and DELETE /users/me exist.
      */}
      <Card className="space-y-sm">
        <h2 className="font-display text-h2 text-ink-primary">Change Password</h2>
        <p className="text-body text-ink-muted">
          Changing your password from this page isn&apos;t available yet. Use the{' '}
          <Link href="/auth/password-reset" className="text-brand-cobalt underline">
            password reset
          </Link>{' '}
          flow instead.
        </p>
      </Card>

      <Card className="border-danger/30 space-y-sm">
        <h2 className="font-display text-h2 text-danger">Danger Zone</h2>
        <p className="text-body text-ink-muted">
          Account deletion isn&apos;t available yet. Contact support if you need your
          account removed.
        </p>
        <button
          disabled
          title="Account deletion is not available yet"
          className="mt-md inline-flex cursor-not-allowed items-center gap-sm rounded-pill border border-line px-md py-sm text-label font-medium text-ink-muted opacity-60"
        >
          <Trash2 className="h-4 w-4" /> Delete Account
        </button>
      </Card>
    </div>
  );
}
