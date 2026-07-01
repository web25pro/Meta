'use client';

export const dynamic = 'force-dynamic';

import { Suspense, useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, KeyRound, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { toast } from 'sonner';
import { Input, Button } from '@meta-jungle/ui';
import { communityAPI } from '@/api/community';
import { AuthShell } from '@/components/auth-shell';

const resetConfirmSchema = z
  .object({
    new_password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Must contain an uppercase letter')
      .regex(/[a-z]/, 'Must contain a lowercase letter')
      .regex(/[0-9]/, 'Must contain a digit'),
    confirm_password: z.string(),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords don't match",
    path: ['confirm_password'],
  });

type ResetConfirmFormData = z.infer<typeof resetConfirmSchema>;

function PasswordResetConfirmContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetConfirmFormData>({ resolver: zodResolver(resetConfirmSchema) });

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setErrorMessage('No reset token provided. Please use the link from your email.');
    }
  }, [token]);

  const onSubmit = async (data: ResetConfirmFormData) => {
    if (!token) {
      toast.error('No reset token available');
      return;
    }
    setIsLoading(true);
    try {
      await communityAPI.confirmPasswordReset({ token, new_password: data.new_password });
      setStatus('success');
      toast.success('Password reset successfully!');
      setTimeout(() => router.push('/auth/login'), 2000);
    } catch (error: any) {
      setStatus('error');
      const msg = error.response?.data?.detail || error.message || 'Failed to reset password';
      setErrorMessage(msg);
      toast.error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const eye = (shown: boolean, toggle: () => void) => (
    <button type="button" onClick={toggle} className="hover:text-ink-primary">
      {shown ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
    </button>
  );

  if (status === 'success') {
    return (
      <AuthShell title="Password updated" subtitle="Reset successful">
        <div className="space-y-lg text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-success/15">
            <CheckCircle className="h-8 w-8 text-success" />
          </div>
          <p className="text-body text-ink-muted">
            Your password has been reset. You can now sign in with your new credentials.
          </p>
          <Link href="/auth/login" className="block">
            <Button className="w-full">Go to Login</Button>
          </Link>
        </div>
      </AuthShell>
    );
  }

  if (status === 'error') {
    return (
      <AuthShell title="Reset failed" subtitle="Something went wrong">
        <div className="space-y-lg text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-danger/15">
            <XCircle className="h-8 w-8 text-danger" />
          </div>
          <p className="text-body text-ink-muted">{errorMessage}</p>
          <div className="space-y-sm">
            <Link href="/auth/password-reset" className="block">
              <Button className="w-full">Try again</Button>
            </Link>
            <Link href="/auth/login" className="block">
              <Button variant="ghost" className="w-full">Back to Login</Button>
            </Link>
          </div>
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell title="Set a new password" subtitle="Secure your jungle account">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-lg">
        <Input
          label="New Password"
          type={showPassword ? 'text' : 'password'}
          placeholder="••••••••"
          trailing={eye(showPassword, () => setShowPassword(!showPassword))}
          {...register('new_password')}
          error={errors.new_password?.message}
          hint="Must contain uppercase, lowercase, and numbers"
        />
        <Input
          label="Confirm Password"
          type={showConfirm ? 'text' : 'password'}
          placeholder="••••••••"
          trailing={eye(showConfirm, () => setShowConfirm(!showConfirm))}
          {...register('confirm_password')}
          error={errors.confirm_password?.message}
        />
        <Button type="submit" className="w-full" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" /> Resetting…
            </>
          ) : (
            <>
              <KeyRound className="h-5 w-5" /> Reset Password
            </>
          )}
        </Button>
      </form>
    </AuthShell>
  );
}

export default function PasswordResetConfirmPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center bg-bg-dark text-ink-inverse">Loading…</div>}>
      <PasswordResetConfirmContent />
    </Suspense>
  );
}
