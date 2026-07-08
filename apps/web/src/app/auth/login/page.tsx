'use client';

import { Suspense, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { LogIn, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { Input, Button } from '@meta-jungle/ui';
import apiClient, { setTokens } from '@/lib/api';
import { TokenResponse } from '@/types';
import { AuthShell } from '@/components/auth-shell';

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  return (
    <Suspense fallback={<AuthShell title="Welcome back" subtitle="Loading…"><div /></AuthShell>}>
      <LoginForm />
    </Suspense>
  );
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const redirectTo = searchParams.get('next') || '/dashboard';

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({ resolver: zodResolver(loginSchema) });

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    try {
      const response = await apiClient.post<TokenResponse>('/auth/login', data);
      const { access_token, refresh_token } = response.data;
      setTokens(access_token, refresh_token);
      toast.success('Welcome back to the jungle!');
      setTimeout(() => router.push(redirectTo), 100);
    } catch (error: any) {
      toast.error(error.response?.data?.error?.message || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Your actions have value here."
      footer={
        <>
          New to the jungle?{' '}
          <Link href="/auth/register" className="font-semibold text-ice underline">
            Start your quest
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-lg">
        <Input
          label="Email Address"
          type="email"
          placeholder="you@example.com"
          {...register('email')}
          error={errors.email?.message}
        />
        <Input
          label="Password"
          type="password"
          placeholder="••••••••"
          {...register('password')}
          error={errors.password?.message}
        />
        <div className="flex items-center justify-between">
          <label className="flex items-center gap-sm text-label text-ink-muted">
            <input type="checkbox" className="h-4 w-4 accent-brand-cobalt" />
            Remember me
          </label>
          <Link href="/auth/password-reset" className="text-label font-medium text-brand-cobalt">
            Forgot password?
          </Link>
        </div>
        <Button type="submit" className="w-full" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" /> Entering jungle…
            </>
          ) : (
            <>
              <LogIn className="h-5 w-5" /> Sign In
            </>
          )}
        </Button>
      </form>
    </AuthShell>
  );
}
