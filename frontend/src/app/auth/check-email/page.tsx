'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Mail, CheckCircle, ArrowLeft } from 'lucide-react';

export default function CheckEmailPage() {
  const searchParams = useSearchParams();
  const email = searchParams.get('email') || 'your email';

  return (
    <div className="min-h-screen bg-gradient-to-br from-jungle-900 via-blue-900 to-primary-900 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Jungle Background */}
      <div className="absolute top-0 right-0 text-9xl opacity-5">🌿</div>
      <div className="absolute bottom-0 left-0 text-9xl opacity-5">📬</div>
      <div className="absolute top-1/3 left-10 text-8xl opacity-5">🐼</div>

      <div className="w-full max-w-md relative z-10">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-gradient-to-br from-blue-400 to-blue-300 rounded-full shadow-lg shadow-blue-400/50 mb-4">
            <span className="text-3xl">🐼</span>
          </div>
          <span className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-panda-white bg-clip-text text-transparent block">LPanda</span>
          <p className="text-blue-200 mt-2">Jungle Quest Started!</p>
        </div>

        {/* Check Email Message */}
        <div className="bg-gradient-to-br from-blue-800 to-jungle-800 bg-opacity-80 backdrop-blur border border-blue-600 rounded-2xl shadow-2xl shadow-blue-900/50 p-8 text-center space-y-6">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-600 to-blue-700 rounded-full shadow-lg shadow-blue-600/50">
            <Mail className="h-8 w-8 text-panda-white" />
          </div>
          
          <div>
            <h2 className="text-lg font-bold text-panda-white mb-2">Check Your Email</h2>
            <p className="text-sm text-blue-100">
              We've sent a verification link to <strong className="text-blue-300">{email}</strong>
            </p>
          </div>

          <div className="bg-blue-700 border border-blue-600 rounded-lg p-4 text-left space-y-2">
            <p className="text-sm font-semibold text-blue-200">🎋 Next Steps:</p>
            <ol className="text-sm text-blue-100 space-y-2 list-decimal list-inside">
              <li>Check your email inbox</li>
              <li>Look for "Verify your LPanda account" email</li>
              <li>Click the verification link</li>
              <li>Start earning bamboo rewards!</li>
            </ol>
          </div>

          <div className="bg-blue-600 bg-opacity-50 border border-blue-500 rounded-lg p-4 text-sm text-blue-100">
            <strong className="text-blue-200">💡 Tip:</strong> If you don't see the email, check your spam or junk folder. The link expires in 24 hours.
          </div>

          <div className="space-y-3 pt-4">
            <p className="text-xs text-primary-300">Didn't receive the email?</p>
            <Link
              href="/auth/resend-verification"
              className="inline-block px-6 py-2 bg-primary-600 text-panda-white font-medium rounded-lg hover:bg-primary-700 transition text-sm"
            >
              Resend Verification Email
            </Link>
          </div>

          <div className="border-t border-primary-600 pt-6">
            <p className="text-sm text-primary-200 mb-3">Already verified?</p>
            <Link
              href="/auth/login"
              className="inline-block w-full px-6 py-3 bg-primary-600 text-panda-white font-medium rounded-lg hover:bg-primary-700 transition"
            >
              Go to Login
            </Link>
          </div>
        </div>

        {/* Back Link */}
        <div className="text-center mt-6">
          <Link
            href="/auth/login"
            className="inline-flex items-center space-x-2 text-primary-300 hover:text-panda-white transition"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Login</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
