'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { LogIn, Leaf, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import apiClient, { setTokens } from '@/lib/api';
import { LoginRequest, TokenResponse } from '@/types';

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    try {
      const response = await apiClient.post<TokenResponse>('/auth/login', data);
      const { access_token, refresh_token } = response.data;
      
      setTokens(access_token, refresh_token);
      toast.success('Welcome back to the jungle!');
      
      // Small delay to ensure token is set
      setTimeout(() => {
        router.push('/dashboard');
      }, 100);
    } catch (error: any) {
      const message = error.response?.data?.error?.message || 'Login failed';
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-jungle-900 via-blue-900 to-primary-900 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Jungle Background Elements */}
      <div className="absolute top-0 right-0 text-9xl opacity-5">🌿</div>
      <div className="absolute bottom-0 left-0 text-9xl opacity-5">🎋</div>
      <div className="absolute top-1/3 right-10 text-8xl opacity-5">🐼</div>

      <div className="w-full max-w-md relative z-10">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-gradient-to-br from-blue-400 to-blue-300 rounded-full shadow-lg shadow-blue-400/50 mb-4">
            <span className="text-3xl">🐼</span>
          </div>
          <span className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-panda-white bg-clip-text text-transparent block">LPanda</span>
          <p className="text-blue-200 mt-2">Return to the Jungle</p>
        </div>

        {/* Login Form */}
        <div className="bg-gradient-to-br from-blue-800 to-jungle-800 bg-opacity-80 backdrop-blur border border-blue-600 rounded-2xl shadow-2xl shadow-blue-900/50 p-8">
          <h1 className="text-2xl font-bold text-panda-white mb-6">Welcome Back</h1>
          
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-blue-100 mb-2">
                Email Address
              </label>
              <input
                {...register('email')}
                type="email"
                id="email"
                className="w-full px-4 py-3 bg-blue-700 border border-blue-600 rounded-lg text-panda-white placeholder-blue-300 focus:ring-2 focus:ring-blue-400 focus:border-transparent transition"
                placeholder="you@example.com"
              />
              {errors.email && (
                <p className="mt-1 text-sm text-red-400">{errors.email.message}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-blue-100 mb-2">
                Password
              </label>
              <input
                {...register('password')}
                type="password"
                id="password"
                className="w-full px-4 py-3 bg-blue-700 border border-blue-600 rounded-lg text-panda-white placeholder-blue-300 focus:ring-2 focus:ring-blue-400 focus:border-transparent transition"
                placeholder="••••••••"
              />
              {errors.password && (
                <p className="mt-1 text-sm text-red-400">{errors.password.message}</p>
              )}
            </div>

            {/* Forgot Password */}
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <input
                  id="remember"
                  type="checkbox"
                  className="h-4 w-4 bg-blue-700 border-blue-600 rounded accent-blue-400"
                />
                <label htmlFor="remember" className="ml-2 block text-sm text-blue-200">
                  Remember me
                </label>
              </div>
              <Link
                href="/password-reset"
                className="text-sm text-blue-300 hover:text-blue-200 font-medium"
              >
                Forgot password?
              </Link>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-panda-white py-3 rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed font-semibold shadow-lg shadow-blue-600/50"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>Entering Jungle...</span>
                </>
              ) : (
                <>
                  <LogIn className="h-5 w-5" />
                  <span>Sign In</span>
                </>
              )}
            </button>
          </form>

          {/* Register Link */}
          <div className="mt-6 text-center">
            <p className="text-sm text-blue-300">
              New to the jungle?{' '}
              <Link href="/register" className="text-blue-300 hover:text-blue-200 font-semibold">
                Start your quest
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
