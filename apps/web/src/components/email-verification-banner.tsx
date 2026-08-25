'use client';

import { useState } from 'react';
import { CheckCircle2, ExternalLink, Mail, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { Button, cn } from '@meta-jungle/ui';
import { communityAPI } from '@/api/community';
import { handleAPIError } from '@/lib/api';
import { useAuth } from '@/context/auth-context';

/**
 * Persistent dashboard affordance for users who reached the app before
 * verifying their email. The user can resend the link without restarting
 * registration, then refresh their account state after clicking it.
 */
export function EmailVerificationBanner() {
  const { user, refreshUser } = useAuth();
  const [isResending, setIsResending] = useState(false);
  const [isChecking, setIsChecking] = useState(false);

  if (!user || user.email_verified) return null;

  const isGmail = user.email.toLowerCase().endsWith('@gmail.com');

  const resendVerification = async () => {
    setIsResending(true);
    try {
      const response = await communityAPI.resendVerificationEmail(user.email);
      if (response.email_sent) {
        toast.success('Verification link sent. Check your inbox and spam folder.');
      } else {
        toast.error(response.message);
      }
    } catch (error: unknown) {
      toast.error(handleAPIError(error));
    } finally {
      setIsResending(false);
    }
  };

  const checkVerification = async () => {
    setIsChecking(true);
    try {
      const updatedUser = await refreshUser();
      if (updatedUser?.email_verified) {
        toast.success('Email verified. Quest submissions are now unlocked.');
      } else {
        toast.info('Your email is not verified yet. Click the link in your email first.');
      }
    } catch (error: unknown) {
      toast.error(handleAPIError(error));
    } finally {
      setIsChecking(false);
    }
  };

  return (
    <section
      aria-live="polite"
      className="mb-lg overflow-hidden rounded-card border border-reward-amber/35 bg-reward-amber/10"
    >
      <div className="flex flex-col gap-md p-md sm:flex-row sm:items-center sm:justify-between sm:px-lg">
        <div className="flex items-start gap-md">
          <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-reward-amber/20 text-reward-amber">
            <Mail className="h-5 w-5" aria-hidden="true" />
          </span>
          <div>
            <p className="text-body font-semibold text-ink-primary">Verify your email to unlock quest submissions</p>
            <p className="mt-1 text-label text-ink-muted">
              We&apos;ll send a link to <span className="font-medium text-ink-primary">{user.email}</span>.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-sm sm:justify-end">
          {isGmail && (
            <a
              href="https://mail.google.com/"
              target="_blank"
              rel="noreferrer"
              className="inline-flex h-9 items-center gap-1 rounded-pill border border-line-blue px-md text-label font-medium text-brand-cobalt transition-colors hover:bg-bg-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-cobalt focus-visible:ring-offset-2"
            >
              Open Gmail <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
            </a>
          )}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={resendVerification}
            disabled={isResending}
            className={cn('whitespace-nowrap', isResending && 'cursor-wait')}
          >
            <RefreshCw className={cn('h-4 w-4', isResending && 'animate-spin')} aria-hidden="true" />
            {isResending ? 'Sending…' : 'Resend link'}
          </Button>
          <Button type="button" size="sm" onClick={checkVerification} disabled={isChecking}>
            <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
            {isChecking ? 'Checking…' : 'I’ve verified'}
          </Button>
        </div>
      </div>
    </section>
  );
}
