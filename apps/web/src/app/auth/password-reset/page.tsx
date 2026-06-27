'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { KeyRound, Loader2, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import { Input, Button } from '@meta-jungle/ui';
import { communityAPI } from '@/api/community';
import { AuthShell } from '@/components/auth-shell';

const resetSchema = z.object({ email: z.string().email('Invalid email address') });
type ResetFormData = z.infer<typeof resetSchema>;

export default function PasswordResetPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [submittedEmail, setSubmittedEmail] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetFormData>({ resolver: zodResolver(resetSchema) });

  const onSubmit = async (data: ResetFormData) => {
    setIsLoading(true);
    try {
      await communityAPI.requestPasswordReset(data.email);
      setSubmittedEmail(data.email);
      setSubmitted(true);
      toast.success('Password reset email sent! Check your inbox.');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || error.message || 'Failed to send reset email');
    } finally {
      setIsLoading(false);
    }
  };

  if (submitted) {
    return (
      <AuthShell title="Email sent" subtitle="Reset your password">
        <div className="space-y-lg text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-success/15">
            <CheckCircle className="h-8 w-8 text-success" />
          </div>
          <p className="text-body text-ink-muted">
            We sent a reset link to{' '}
            <strong className="text-ink-primary">{submittedEmail}</strong>
          </p>
          <p className="text-label text-ink-muted">
            The link expires in 1 hour. Check your spam folder if you don&apos;t see it.
          </p>
          <div className="space-y-sm">
            <Link href="/auth/login" className="block">
              <Button className="w-full">Back to Login</Button>
            </Link>
            <Button variant="ghost" className="w-full" onClick={() => setSubmitted(false)}>
              Try another email
            </Button>
          </div>
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell
      title="Reset your password"
      subtitle="We'll email you a reset link"
      footer={
        <Link href="/auth/login" className="font-semibold text-ice underline">
          Back to login
        </Link>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-lg">
        <Input label="Email Address" type="email" placeholder="you@example.com" {...register('email')} error={errors.email?.message} />
        <Button type="submit" className="w-full" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" /> Sending…
            </>
          ) : (
            <>
              <KeyRound className="h-5 w-5" /> Send Reset Link
            </>
          )}
        </Button>
      </form>
    </AuthShell>
  );
}
