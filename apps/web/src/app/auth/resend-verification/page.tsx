'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Mail, Loader2, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import { Input, Button } from '@meta-jungle/ui';
import { communityAPI } from '@/api/community';
import { AuthShell } from '@/components/auth-shell';

const resendSchema = z.object({ email: z.string().email('Invalid email address') });
type ResendFormData = z.infer<typeof resendSchema>;

export default function ResendVerificationPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [submittedEmail, setSubmittedEmail] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResendFormData>({ resolver: zodResolver(resendSchema) });

  const onSubmit = async (data: ResendFormData) => {
    setIsLoading(true);
    try {
      await communityAPI.resendVerificationEmail(data.email);
      setSubmittedEmail(data.email);
      setSubmitted(true);
      toast.success('Verification email sent! Check your inbox.');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || error.message || 'Failed to resend email');
    } finally {
      setIsLoading(false);
    }
  };

  if (submitted) {
    return (
      <AuthShell title="Check your email" subtitle="Verification email sent">
        <div className="space-y-lg text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-success/15">
            <CheckCircle className="h-8 w-8 text-success" />
          </div>
          <p className="text-body text-ink-muted">
            We sent a verification link to{' '}
            <strong className="text-ink-primary">{submittedEmail}</strong>
          </p>
          <div className="rounded-card bg-bg-surface p-md text-left text-label text-ink-muted">
            <ul className="space-y-1">
              <li>• Check your spam or junk folder</li>
              <li>• The link expires in 24 hours</li>
              <li>• Click the link to verify your email</li>
            </ul>
          </div>
          <div className="space-y-sm">
            <Link href="/auth/login" className="block">
              <Button className="w-full">Back to Login</Button>
            </Link>
            <Button variant="ghost" className="w-full" onClick={() => setSubmitted(false)}>
              Resend to another email
            </Button>
          </div>
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell
      title="Resend verification"
      subtitle="Get a new verification link"
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
              <Mail className="h-5 w-5" /> Resend Verification Email
            </>
          )}
        </Button>
      </form>
    </AuthShell>
  );
}
