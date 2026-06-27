'use client';

export const dynamic = 'force-dynamic';

import { Suspense, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, UserPlus, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { Input, Button } from '@meta-jungle/ui';
import { communityAPI } from '@/api/community';
import { AuthShell } from '@/components/auth-shell';

const registerSchema = z
  .object({
    email: z.string().email('Invalid email address'),
    username: z
      .string()
      .min(3, 'Username must be at least 3 characters')
      .max(20, 'Username must be at most 20 characters')
      .regex(/^[a-zA-Z0-9_]+$/, 'Letters, numbers, and underscores only'),
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Must contain an uppercase letter')
      .regex(/[a-z]/, 'Must contain a lowercase letter')
      .regex(/[0-9]/, 'Must contain a digit'),
    confirmPassword: z.string(),
    referralCode: z.string().optional(),
    agreeToTerms: z.boolean().refine((val) => val === true, {
      message: 'You must agree to the terms and conditions',
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

type RegisterFormData = z.infer<typeof registerSchema>;

function RegisterContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const referralCodeParam = searchParams.get('ref') || '';

  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: { referralCode: referralCodeParam },
  });

  const onSubmit = async (data: RegisterFormData) => {
    setIsLoading(true);
    try {
      await communityAPI.register({
        email: data.email,
        username: data.username,
        password: data.password,
        referral_code: data.referralCode || undefined,
      });
      toast.success('Account created! Check your email to verify your address.');
      setTimeout(
        () => router.push('/auth/check-email?email=' + encodeURIComponent(data.email)),
        1500,
      );
    } catch (error: any) {
      toast.error(
        error.response?.data?.error?.message ||
          error.response?.data?.detail ||
          error.message ||
          'Registration failed',
      );
    } finally {
      setIsLoading(false);
    }
  };

  const eye = (shown: boolean, toggle: () => void) => (
    <button type="button" onClick={toggle} className="hover:text-ink-primary">
      {shown ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
    </button>
  );

  return (
    <AuthShell
      title="Create your account"
      subtitle="Earn everywhere. Own everything."
      wide
      footer={
        <>
          Already have an account?{' '}
          <Link href="/auth/login" className="font-semibold text-ice underline">
            Sign in here
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-md">
        <div className="grid gap-md sm:grid-cols-2">
          <Input label="Email Address" type="email" placeholder="you@example.com" {...register('email')} error={errors.email?.message} />
          <Input label="Username" placeholder="your_username" {...register('username')} error={errors.username?.message} hint="3–20 chars, letters, numbers, underscores" />
        </div>
        <div className="grid gap-md sm:grid-cols-2">
          <Input
            label="Password"
            type={showPassword ? 'text' : 'password'}
            placeholder="••••••••"
            trailing={eye(showPassword, () => setShowPassword(!showPassword))}
            {...register('password')}
            error={errors.password?.message}
          />
          <Input
            label="Confirm Password"
            type={showConfirm ? 'text' : 'password'}
            placeholder="••••••••"
            trailing={eye(showConfirm, () => setShowConfirm(!showConfirm))}
            {...register('confirmPassword')}
            error={errors.confirmPassword?.message}
          />
        </div>
        <Input label="Referral Code (optional)" placeholder="Enter a referral code" {...register('referralCode')} error={errors.referralCode?.message} />

        <label className="flex items-start gap-sm text-label text-ink-muted">
          <input type="checkbox" {...register('agreeToTerms')} className="mt-1 h-4 w-4 accent-brand-cobalt" />
          <span>
            I agree to the{' '}
            <Link href="/terms" className="font-medium text-brand-cobalt">Terms of Service</Link> and{' '}
            <Link href="/privacy" className="font-medium text-brand-cobalt">Privacy Policy</Link>
          </span>
        </label>
        {errors.agreeToTerms && <p className="text-label text-danger">{errors.agreeToTerms.message}</p>}

        <Button type="submit" className="w-full" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" /> Joining the jungle…
            </>
          ) : (
            <>
              <UserPlus className="h-5 w-5" /> Start Your Quest
            </>
          )}
        </Button>
      </form>
    </AuthShell>
  );
}

export default function RegisterPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center bg-bg-dark text-ink-inverse">Loading…</div>}>
      <RegisterContent />
    </Suspense>
  );
}
