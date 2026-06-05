'use client';

export const dynamic = 'force-dynamic';

import { Suspense, useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, KeyRound, Trophy, Loader2, CheckCircle, XCircle } from 'lucide-react';
import { toast } from 'sonner';
import { communityAPI } from '@/api/community';

const resetConfirmSchema = z
  .object({
    new_password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
      .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
      .regex(/[0-9]/, 'Password must contain at least one digit'),
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
  } = useForm<ResetConfirmFormData>({
    resolver: zodResolver(resetConfirmSchema),
  });

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
      await communityAPI.confirmPasswordReset({
        token,
        new_password: data.new_password,
      });

      setStatus('success');
      toast.success('Password reset successfully!');

      // Redirect to login after 2 seconds
      setTimeout(() => {
        router.push('/login');
      }, 2000);
    } catch (error: any) {
      setStatus('error');
      const errorMsg =
        error.response?.data?.detail || error.message || 'Failed to reset password';
      setErrorMessage(errorMsg);
      toast.error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  if (status === 'success') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-900 via-primary-800 to-jungle-900 flex items-center justify-center p-4 relative overflow-hidden">
        {/* Jungle Background */}
        <div className="absolute top-0 right-0 text-9xl opacity-10">🔐</div>
        <div className="absolute bottom-0 left-0 text-9xl opacity-10">✅</div>

        <div className="w-full max-w-md relative z-10">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 bg-white rounded-full shadow-lg mb-4">
              <span className="text-3xl">🐼</span>
            </div>
            <span className="text-3xl font-bold text-white block">LPanda</span>
            <p className="text-primary-200 mt-2">Password Reset Successful</p>
          </div>

          {/* Success Message */}
          <div className="bg-primary-800 bg-opacity-80 backdrop-blur border border-primary-700 rounded-2xl shadow-2xl p-8 text-center space-y-4">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-600 rounded-full">
              <CheckCircle className="h-8 w-8 text-white" />
            </div>
            <p className="text-white font-bold text-lg">Password Updated!</p>
            <p className="text-sm text-primary-200">
              Your password has been reset successfully. You can now login with your new jungle credentials.
            </p>
            <p className="text-xs text-primary-300 mt-4">Redirecting to login...</p>
            <Link
              href="/auth/login"
              className="inline-block mt-6 px-6 py-3 bg-secondary-600 text-white font-medium rounded-lg hover:bg-secondary-700 transition"
            >
              Go to Login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-900 via-primary-800 to-jungle-900 flex items-center justify-center p-4 relative overflow-hidden">
        {/* Jungle Background */}
        <div className="absolute top-0 left-0 text-9xl opacity-10">⚠️</div>
        <div className="absolute bottom-0 right-0 text-9xl opacity-10">🔓</div>

        <div className="w-full max-w-md relative z-10">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 bg-white rounded-full shadow-lg mb-4">
              <span className="text-3xl">🐼</span>
            </div>
            <span className="text-3xl font-bold text-white block">LPanda</span>
            <p className="text-primary-200 mt-2">Reset Failed</p>
          </div>

          {/* Error Message */}
          <div className="bg-primary-800 bg-opacity-80 backdrop-blur border border-primary-700 rounded-2xl shadow-2xl p-8 text-center space-y-4">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-red-600 rounded-full">
              <XCircle className="h-8 w-8 text-white" />
            </div>
            <p className="text-white font-bold text-lg">Password Reset Failed</p>
            <p className="text-sm text-primary-200">{errorMessage}</p>
            <div className="space-y-3 mt-6">
              <Link
                href="/auth/password-reset"
                className="inline-block w-full px-6 py-3 bg-secondary-600 text-white font-medium rounded-lg hover:bg-secondary-700 transition"
              >
                Try Again
              </Link>
              <Link
                href="/auth/login"
                className="inline-block w-full px-6 py-3 border border-primary-600 text-secondary-400 font-medium rounded-lg hover:border-primary-500 transition"
              >
                Back to Login
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-900 via-primary-800 to-jungle-900 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Jungle Background */}
      <div className="absolute top-0 left-0 text-9xl opacity-10">🔐</div>
      <div className="absolute bottom-0 right-0 text-9xl opacity-10">🔑</div>

      <div className="w-full max-w-md relative z-10">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-white rounded-full shadow-lg mb-4">
            <span className="text-3xl">🐼</span>
          </div>
          <span className="text-3xl font-bold text-white block">LPanda</span>
          <p className="text-primary-200 mt-2">Set Your New Password</p>
        </div>

        {/* Reset Form */}
        <div className="bg-primary-800 bg-opacity-80 backdrop-blur border border-primary-700 rounded-2xl shadow-2xl p-8">
          <p className="text-sm text-primary-200 mb-6">Create a strong password to secure your jungle account</p>
          
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* New Password */}
            <div>
              <label htmlFor="new_password" className="block text-sm font-medium text-primary-100 mb-2">
                New Password
              </label>
              <div className="relative">
                <input
                  {...register('new_password')}
                  type={showPassword ? 'text' : 'password'}
                  id="new_password"
                  className="w-full px-4 py-3 bg-primary-700 border border-primary-600 rounded-lg text-white placeholder-primary-400 focus:ring-2 focus:ring-secondary-500 focus:border-transparent transition pr-10"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3 text-primary-400 hover:text-primary-200"
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
              {errors.new_password && (
                <p className="mt-1 text-sm text-red-400">{errors.new_password.message}</p>
              )}
              <p className="mt-2 text-xs text-primary-300">
                Must contain uppercase, lowercase, and numbers
              </p>
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirm_password" className="block text-sm font-medium text-primary-100 mb-2">
                Confirm Password
              </label>
              <div className="relative">
                <input
                  {...register('confirm_password')}
                  type={showConfirm ? 'text' : 'password'}
                  id="confirm_password"
                  className="w-full px-4 py-3 bg-primary-700 border border-primary-600 rounded-lg text-white placeholder-primary-400 focus:ring-2 focus:ring-secondary-500 focus:border-transparent transition pr-10"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute right-3 top-3 text-primary-400 hover:text-primary-200"
                >
                  {showConfirm ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
              {errors.confirm_password && (
                <p className="mt-1 text-sm text-red-400">{errors.confirm_password.message}</p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full px-6 py-3 bg-gradient-to-r from-secondary-600 to-secondary-700 text-white font-medium rounded-lg hover:from-secondary-700 hover:to-secondary-800 transition-all flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>Resetting...</span>
                </>
              ) : (
                <>
                  <KeyRound className="h-5 w-5" />
                  <span>Reset Password</span>
                </>
              )}
            </button>
          </form>

          {/* Back to Login */}
          <p className="text-center text-sm text-primary-300 mt-6">
            Remember your password?{' '}
            <Link href="/login" className="text-primary-600 hover:underline font-medium">
              Back to Login
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default function PasswordResetConfirmPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Loading...</div>}>
      <PasswordResetConfirmContent />
    </Suspense>
  );
}
