'use client';

import { ReactNode } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Trophy, User, Settings, Users, LogOut } from 'lucide-react';
import { useAuth } from '@/context/auth-context';

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { logout } = useAuth();

  const isActive = (path: string) => pathname === path;

  const handleLogout = () => {
    logout();
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className="w-64 bg-white shadow-lg">
        <div className="p-6">
          <div className="flex items-center space-x-2 mb-8">
            <Trophy className="h-8 w-8 text-primary-600" />
            <span className="text-2xl font-bold text-gray-900">LPanda</span>
          </div>

          <nav className="space-y-2">
            <Link
              href="/dashboard"
              className={`block px-4 py-2 rounded-lg transition ${
                isActive('/dashboard')
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <div className="flex items-center space-x-2">
                <Trophy className="h-5 w-5" />
                <span>Overview</span>
              </div>
            </Link>

            <Link
              href="/dashboard/community/profile"
              className={`block px-4 py-2 rounded-lg transition ${
                isActive('/dashboard/community/profile')
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <div className="flex items-center space-x-2">
                <User className="h-5 w-5" />
                <span>Profile</span>
              </div>
            </Link>

            <Link
              href="/dashboard/community/referrals"
              className={`block px-4 py-2 rounded-lg transition ${
                isActive('/dashboard/community/referrals')
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <div className="flex items-center space-x-2">
                <Users className="h-5 w-5" />
                <span>Referrals</span>
              </div>
            </Link>

            <Link
              href="/dashboard/community/settings"
              className={`block px-4 py-2 rounded-lg transition ${
                isActive('/dashboard/community/settings')
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              <div className="flex items-center space-x-2">
                <Settings className="h-5 w-5" />
                <span>Settings</span>
              </div>
            </Link>
          </nav>

          <button
            onClick={handleLogout}
            className="mt-8 w-full px-4 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition flex items-center space-x-2"
          >
            <LogOut className="h-5 w-5" />
            <span>Logout</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1">
        <main className="p-8">{children}</main>
      </div>
    </div>
  );
}
