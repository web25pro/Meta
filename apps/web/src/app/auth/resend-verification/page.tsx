'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Mail, Trophy, Loader2, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import { communityAPI } from '@/api/community';

const resendSchema = z.object({
  email: z.string().email('Invalid email address'),
});

type ResendFormData = z.infer<typeof resendSchema>;

export default function ResendVerificationPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [submittedEmail, setSubmittedEmail] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResendFormData>({
    resolver: zodResolver(resendSchema),
  });

  const onSubmit = async (data: ResendFormData) => {
    setIsLoading(true);
    try {
      await communityAPI.resendVerificationEmail(data.email);
      setSubmittedEmail(data.email);
      setSubmitted(true);
      toast.success('Verification email sent! Check your inbox.');
    } catch (error: any) {
      const message =
        error.response?.data?.detail || error.message || 'Failed to resend verification email';
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-900 via-primary-800 to-jungle-900 flex items-center justify-center p-4 relative overflow-hidden">
        {/* Jungle Background */}
        <div className="absolute top-0 right-0 text-9xl opacity-10">📧</div>
        <div className="absolute bottom-0 left-0 text-9xl opacity-10">✉️</div>

        <div className="w-full max-w-md relative z-10">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 bg-white rounded-full shadow-lg mb-4">
              <span className="text-3xl">🐼</span>
            </div>
            <span className="text-3xl font-bold text-white block">LPanda</span>
            <p className="text-primary-200 mt-2">Verification Email Sent</p>
          </div>

          {/* Success Message */}
          <div className="bg-primary-800 bg-opacity-80 backdrop-blur border border-primary-700 rounded-2xl shadow-2xl p-8 text-center space-y-4">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-600 rounded-full">
              <CheckCircle className="h-8 w-8 text-white" />
            </div>
            <p className="text-white font-bold text-lg">Check Your Email</p>
            <p className="text-sm text-primary-200">
              We&apos;ve sent a verification link to <strong className="text-secondary-400">{submittedEmail}</strong>
            </p>
            <div className="bg-primary-700 border border-primary-600 rounded-lg p-4 text-left">
              <p className="text-sm text-primary-100">
                <strong className="text-secondary-400">🎋 Tips:</strong>
              </p>
              <ul className="text-sm text-primary-200 mt-2 space-y-1">
                <li>• Check your spam or junk folder</li>
                <li>• The link expires in 24 hours</li>
                <li>• Click the link to verify your email</li>
              </ul>
            </div>

            <div className="space-y-3 pt-4">
              <Link
                href="/auth/login"
                className="inline-block w-full px-6 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition"
              >
                Back to Login
              </Link>
              <button
                onClick={() => setSubmitted(false)}
                className="w-full px-6 py-3 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition"
              >
                Resend to Another Email
              </button>
            </div>
          </div>

          {/* Help */}
          <p className="text-center text-xs text-gray-600 mt-6">
            Still haven&apos;t received it?{' '}
            <Link href="/support" className="text-primary-600 hover:underline">
              Contact support
            </Link>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-secondary-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <Trophy className="h-10 w-10 text-primary-600" />
            <span className="text-3xl font-bold text-gray-900">LPanda</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Resend Verification Email</h1>
          <p className="text-gray-600 mt-2">Enter your email to receive a new verification link</p>
        </div>

        {/* Resend Form */}
        <div className="bg-white rounded-xl shadow-lg p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <input
                {...register('email')}
                type="email"
                id="email"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                placeholder="you@example.com"
              />
              {errors.email && (
                <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full px-6 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:bg-gray-400 transition flex items-center justify-center space-x-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>Sending...</span>
                </>
              ) : (
                <>
                  <Mail className="h-5 w-5" />
                  <span>Resend Verification Email</span>
                </>
              )}
            </button>
          </form>

          {/* Back to Login */}
          <p className="text-center text-sm text-gray-600 mt-6">
            Already verified?{' '}
            <Link href="/auth/login" className="text-primary-600 hover:underline font-medium">
              Go to Login
            </Link>
          </p>
        </div>

        {/* Help Text */}
        <p className="text-center text-xs text-gray-600 mt-6">
          Don&apos;t have an account?{' '}
          <Link href="/auth/register" className="text-primary-600 hover:underline font-medium">
            Sign up here
          </Link>
        </p>
      </div>
    </div>
  );
}
