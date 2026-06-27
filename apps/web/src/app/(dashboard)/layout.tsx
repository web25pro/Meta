'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import {
  Home,
  Target,
  Trophy,
  Wallet,
  ShoppingBag,
  Calendar,
  Bell,
  User,
  Users,
  LogOut,
  Menu,
  X,
  Flame,
  Megaphone,
  GraduationCap,
  ArrowLeftRight,
  Lock,
  Image as ImageIcon,
} from 'lucide-react';
import { cn } from '@meta-jungle/ui';
import { isAuthenticated, clearTokens } from '@/lib/api';

const navSections: {
  title?: string;
  items: { name: string; href: string; icon: typeof Home }[];
}[] = [
  { items: [{ name: 'Dashboard', href: '/dashboard', icon: Home }] },
  {
    title: 'Earn',
    items: [
      { name: 'Quests', href: '/dashboard/tasks', icon: Target },
      { name: 'Campaigns', href: '/dashboard/campaigns', icon: Megaphone },
      { name: 'Learn', href: '/dashboard/learn', icon: GraduationCap },
    ],
  },
  {
    title: 'Wallet',
    items: [
      { name: 'Panda Wallet', href: '/dashboard/points', icon: Wallet },
      { name: 'Marketplace', href: '/dashboard/marketplace', icon: ShoppingBag },
      { name: 'P2P Trade', href: '/dashboard/p2p', icon: ArrowLeftRight },
      { name: 'Staking', href: '/dashboard/staking', icon: Lock },
      { name: 'NFT Vault', href: '/dashboard/nft-vault', icon: ImageIcon },
    ],
  },
  {
    title: 'Community',
    items: [
      { name: 'Leaderboard', href: '/dashboard/leaderboard', icon: Trophy },
      { name: 'Profile', href: '/dashboard/community/profile', icon: User },
      { name: 'Referrals', href: '/dashboard/community/referrals', icon: Users },
    ],
  },
  {
    title: 'Updates',
    items: [
      { name: 'Schedule', href: '/dashboard/schedule', icon: Calendar },
      { name: 'Announcements', href: '/dashboard/announcements', icon: Bell },
    ],
  },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) router.push('/auth/login');
  }, [router]);

  const handleLogout = () => {
    clearTokens();
    router.push('/auth/login');
  };

  return (
    <div className="min-h-screen bg-bg-surface">
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-bg-dark/40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar — 240px, off-white blue-tint surface */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-30 flex w-60 flex-col bg-bg-surface',
          'border-r border-line transition-transform duration-300 lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        {/* Wordmark */}
        <div className="flex h-16 items-center justify-between border-b border-line px-lg">
          <Link href="/dashboard" className="flex items-center gap-sm">
            <span className="text-xl">🐼</span>
            <span className="font-display text-lg font-bold text-ink-primary">
              Meta-Jungle
            </span>
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="text-ink-muted hover:text-ink-primary lg:hidden"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-lg overflow-y-auto px-md py-lg">
          {navSections.map((section, si) => (
            <div key={si} className="space-y-1">
              {section.title && (
                <p className="px-md pb-1 text-[10px] font-semibold uppercase tracking-wider text-ink-muted">
                  {section.title}
                </p>
              )}
              {section.items.map((item) => {
                const isActive =
                  item.href === '/dashboard'
                    ? pathname === item.href
                    : pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={() => setSidebarOpen(false)}
                    className={cn(
                      'relative flex items-center gap-md rounded-card px-md py-2.5 text-body font-medium transition-colors',
                      isActive
                        ? 'bg-brand-ice text-brand-cobalt'
                        : 'text-ink-muted hover:bg-bg-elevated hover:text-ink-primary',
                    )}
                  >
                    {isActive && (
                      <span className="absolute left-0 top-1/2 h-6 w-[4px] -translate-y-1/2 rounded-r bg-brand-cobalt" />
                    )}
                    <item.icon className="h-5 w-5" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>

        {/* Footer — streak + role + logout */}
        <div className="space-y-sm border-t border-line p-md">
          <div className="flex items-center justify-between rounded-card bg-bg-elevated px-md py-sm">
            <span className="flex items-center gap-sm text-label text-ink-muted">
              <Flame className="h-4 w-4 text-reward-amber" /> Streak
            </span>
            <span className="font-display text-body text-reward-amber">5 days</span>
          </div>
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-md rounded-card px-md py-3 text-body font-medium text-ink-muted transition-colors hover:bg-bg-elevated hover:text-danger"
          >
            <LogOut className="h-5 w-5" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="lg:pl-60">
        {/* Mobile top bar */}
        <header className="flex h-16 items-center border-b border-line bg-bg-primary px-lg lg:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="mr-md text-ink-muted hover:text-ink-primary"
          >
            <Menu className="h-6 w-6" />
          </button>
          <span className="flex items-center gap-sm font-display font-bold text-ink-primary">
            <span>🐼</span> Meta-Jungle
          </span>
        </header>

        <main className="mx-auto max-w-6xl p-lg lg:p-xl">{children}</main>
      </div>
    </div>
  );
}
