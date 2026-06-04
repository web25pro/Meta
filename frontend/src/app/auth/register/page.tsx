'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, UserPlus, Trophy, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { communityAPI } from '@/api/community';
import { setTokens } from '@/lib/api';

const registerSchema = z
  .object({
    email: z.string().email('Invalid email address'),
    username: z
      .string()
      .min(3, 'Username must be at least 3 characters')
      .max(20, 'Username must be at most 20 characters')
      .regex(/^[a-zA-Z0-9_]+$/, 'Username can only contain letters, numbers, and underscores'),
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
      .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
      .regex(/[0-9]/, 'Password must contain at least one digit'),
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

export default function RegisterPage() {
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
    defaultValues: {
      referralCode: referralCodeParam,
    },
  });

  const onSubmit = async (data: RegisterFormData) => {
    setIsLoading(true);
    try {
      // Register user with community API
      await communityAPI.register({
        email: data.email,
        username: data.username,
        password: data.password,
        referral_code: data.referralCode || undefined,
      });

      // Show success toast and redirect to email verification page
      toast.success('Account created! Check your email to verify your address.');
      
      // Redirect to a page asking user to check email
      setTimeout(() => {
        router.push('/auth/check-email?email=' + encodeURIComponent(data.email));
      }, 1500);
    } catch (error: any) {
      const message =
        error.response?.data?.detail || error.message || 'Registration failed';
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-jungle-900 via-blue-900 to-primary-900 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Jungle Background Elements */}
      <div className="absolute top-0 left-0 text-9xl opacity-5">🌿</div>
      <div className="absolute bottom-0 right-0 text-9xl opacity-5">🎋</div>
      <div className="absolute top-1/3 left-10 text-8xl opacity-5">🐼</div>

      <div className="w-full max-w-2xl relative z-10">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-gradient-to-br from-blue-400 to-blue-300 rounded-full shadow-lg shadow-blue-400/50 mb-4">
            <span className="text-3xl">🐼</span>
          </div>
          <span className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-panda-white bg-clip-text text-transparent block">LPanda</span>
          <p className="text-blue-200 mt-2">Join the Jungle Quest</p>
        </div>

        {/* Register Form */}
        <div className="bg-gradient-to-br from-blue-800 to-jungle-800 bg-opacity-80 backdrop-blur border border-blue-600 rounded-2xl shadow-2xl shadow-blue-900/50 p-8">
          <h1 className="text-2xl font-bold text-panda-white mb-6">Create Your Account</h1>
          
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
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

            {/* Username */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-blue-100 mb-2">
                Username
              </label>
              <input
                {...register('username')}
                type="text"
                id="username"
                className="w-full px-4 py-3 bg-blue-700 border border-blue-600 rounded-lg text-panda-white placeholder-blue-300 focus:ring-2 focus:ring-blue-400 focus:border-transparent transition"
                placeholder="your_username"
              />
              {errors.username && (
                <p className="mt-1 text-sm text-red-400">{errors.username.message}</p>
              )}
              <p className="mt-1 text-xs text-blue-200">3-20 characters, letters, numbers, and underscores only</p>
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-blue-100 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  {...register('password')}
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  className="w-full px-4 py-3 bg-blue-700 border border-blue-600 rounded-lg text-panda-white placeholder-blue-300 focus:ring-2 focus:ring-blue-400 focus:border-transparent transition pr-10"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3 text-blue-300 hover:text-blue-100"
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-sm text-red-400">{errors.password.message}</p>
              )}
              <p className="mt-1 text-xs text-blue-200">At least 8 characters, with uppercase, lowercase, and numbers</p>
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-blue-100 mb-2">
                Confirm Password
              </label>
              <div className="relative">
                <input
                  {...register('confirmPassword')}
                  type={showConfirm ? 'text' : 'password'}
                  id="confirmPassword"
                  className="w-full px-4 py-3 bg-blue-700 border border-blue-600 rounded-lg text-panda-white placeholder-blue-300 focus:ring-2 focus:ring-blue-400 focus:border-transparent transition pr-10"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(!showConfirm)}
                  className="absolute right-3 top-3 text-blue-300 hover:text-blue-100"
                >
                  {showConfirm ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
              {errors.confirmPassword && (
                <p className="mt-1 text-sm text-red-400">{errors.confirmPassword.message}</p>
              )}
            </div>

            {/* Referral Code (Optional) */}
            <div>
              <label htmlFor="referralCode" className="block text-sm font-medium text-blue-100 mb-2">
                Referral Code (Optional)
              </label>
              <input
                {...register('referralCode')}
                type="text"
                id="referralCode"
                className="w-full px-4 py-3 bg-blue-700 border border-blue-600 rounded-lg text-panda-white placeholder-blue-300 focus:ring-2 focus:ring-blue-400 focus:border-transparent transition"
                placeholder="Enter referral code if you have one"
              />
              {errors.referralCode && (
                <p className="mt-1 text-sm text-red-400">{errors.referralCode.message}</p>
              )}
            </div>

            {/* Terms */}
            <div className="flex items-start mt-4">
              <input
                id="terms"
                type="checkbox"
                {...register('agreeToTerms')}
                className="h-4 w-4 mt-1 bg-blue-700 border-blue-600 rounded accent-blue-400"
              />
              <label htmlFor="terms" className="ml-2 block text-sm text-blue-200">
                I agree to the{' '}
                <Link href="/terms" className="text-blue-300 hover:text-blue-200 font-medium">
                  Terms of Service
                </Link>{' '}
                and{' '}
                <Link href="/privacy" className="text-blue-300 hover:text-blue-200 font-medium">
                  Privacy Policy
                </Link>
              </label>
            </div>
            {errors.agreeToTerms && (
              <p className="mt-1 text-sm text-red-400">{errors.agreeToTerms.message}</p>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-panda-white py-3 rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed font-semibold shadow-lg shadow-blue-600/50 mt-6"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>Joining the Jungle...</span>
                </>
              ) : (
                <>
                  <UserPlus className="h-5 w-5" />
                  <span>Start Your Quest</span>
                </>
              )}
            </button>
          </form>

          {/* Login Link */}
          <div className="mt-6 text-center">
            <p className="text-sm text-blue-300">
              Already have an account?{' '}
              <Link href="/login" className="text-blue-300 hover:text-blue-200 font-semibold">
                Sign in here
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
