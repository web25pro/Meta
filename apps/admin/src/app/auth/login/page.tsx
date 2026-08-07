'use client';

import { Suspense, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { LogIn, Loader2, ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';
import { Input, Button } from '@meta-jungle/ui';
import apiClient, { setTokens } from '@meta-jungle/api-client';

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormData = z.infer<typeof loginSchema>;

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export default function AdminLoginPage() {
  return (
    <Suspense fallback={<Shell><div /></Shell>}>
      <LoginForm />
    </Suspense>
  );
}

/**
 * Minimal auth shell. Deliberately self-contained — the admin console has no
 * registration or password-reset flow; both live in the user app.
 */
function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-bg-dark px-md">
      <div className="w-full max-w-sm">
        <div className="mb-xl text-center">
          <div className="mb-md inline-flex h-14 w-14 items-center justify-center rounded-card bg-white/10">
            <ShieldCheck className="h-7 w-7 text-brand-ice" />
          </div>
          <h1 className="font-display text-h1 text-ink-inverse">Admin Console</h1>
          <p className="mt-1 text-body text-brand-ice">Restricted to Overall Admins.</p>
        </div>
        <div className="rounded-card bg-bg-primary p-xl shadow-lg">{children}</div>
      </div>
    </div>
  );
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const redirectTo = searchParams.get('next') || '/';

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
      toast.success('Signed in');
      setTimeout(() => router.push(redirectTo), 100);
    } catch (error: any) {
      toast.error(error.response?.data?.error?.message || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Shell>
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
        <Button type="submit" className="w-full" disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" /> Signing in…
            </>
          ) : (
            <>
              <LogIn className="h-5 w-5" /> Sign In
            </>
          )}
        </Button>
      </form>
    </Shell>
  );
}
