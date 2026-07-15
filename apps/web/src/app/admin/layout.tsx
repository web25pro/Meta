'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { useQuery } from 'react-query';
import {
  LayoutDashboard,
  Users,
  Target,
  Megaphone,
  ClipboardCheck,
  ArrowLeft,
  ShieldAlert,
  Menu,
  X,
} from 'lucide-react';
import { PandaMascot, Button, cn } from '@meta-jungle/ui';
import apiClient, { isAuthenticated } from '@/lib/api';

const nav = [
  { name: 'Overview', href: '/admin', icon: LayoutDashboard },
  { name: 'Users', href: '/admin/users', icon: Users },
  { name: 'Quests', href: '/admin/quests', icon: Target },
  { name: 'Campaigns', href: '/admin/campaigns', icon: Megaphone },
  { name: 'Reviews', href: '/admin/reviews', icon: ClipboardCheck },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const redirectingRef = useRef(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      redirectingRef.current = true;
      router.push('/auth/login');
    } else {
      setAuthChecked(true);
    }
  }, [router]);

  const { data: me, isLoading, isError } = useQuery(
    'adminMe',
    async () => (await apiClient.get('/users/me')).data,
    {
      retry: false,
      enabled: authChecked,
      onError: (err: any) => {
        // If the API returned 401 or 403 (auth failure), the interceptor
        // already redirected — don't flash the "access denied" screen.
        const s = err?.response?.status;
        const d = (err?.response?.data as any)?.detail;
        if (s === 401 || (s === 403 && d === 'Not authenticated')) {
          redirectingRef.current = true;
        }
      },
    },
  );

  const role = me?.role;
  const allowed = role === 'Overall_Admin';

  if (!authChecked || isLoading || redirectingRef.current) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg-dark">
        <PandaMascot size={96} />
      </div>
    );
  }

  if (isError || !allowed) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-md bg-bg-dark px-md text-center text-ink-inverse">
        <ShieldAlert className="h-12 w-12 text-reward-amber" />
        <h1 className="font-display text-h1">Admin access required</h1>
        <p className="max-w-sm text-brand-ice">
          This area is restricted to Overall Admins. Your account doesn&apos;t have access.
        </p>
        <Link href="/dashboard">
          <Button variant="jungle">Back to dashboard</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-surface">
      {open && (
        <div className="fixed inset-0 z-20 bg-bg-dark/50 lg:hidden" onClick={() => setOpen(false)} />
      )}

      {/* Control-room sidebar (navy to distinguish from the user app) */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-30 flex w-60 flex-col bg-bg-dark text-ink-inverse',
          'transition-transform duration-300 lg:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="flex h-16 items-center justify-between border-b border-white/10 px-lg">
          <Link href="/admin" className="flex items-center gap-sm">
            <span className="text-xl">🐼</span>
            <span className="font-display text-lg font-bold">Admin</span>
          </Link>
          <button onClick={() => setOpen(false)} className="text-brand-ice lg:hidden">
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-md py-lg">
          {nav.map((item) => {
            const active = item.href === '/admin' ? pathname === item.href : pathname.startsWith(item.href);
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => setOpen(false)}
                className={cn(
                  'flex items-center gap-md rounded-card px-md py-2.5 text-body font-medium transition-colors',
                  active ? 'bg-white/10 text-ink-inverse' : 'text-brand-ice hover:bg-white/5',
                )}
              >
                <item.icon className="h-5 w-5" />
                {item.name}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-white/10 p-md">
          <Link
            href="/dashboard"
            className="flex items-center gap-md rounded-card px-md py-2.5 text-body font-medium text-brand-ice transition-colors hover:bg-white/5"
          >
            <ArrowLeft className="h-5 w-5" /> Back to app
          </Link>
        </div>
      </aside>

      <div className="lg:pl-60">
        <header className="flex h-16 items-center gap-md border-b border-line bg-bg-primary px-lg lg:hidden">
          <button onClick={() => setOpen(true)} className="text-ink-muted">
            <Menu className="h-6 w-6" />
          </button>
          <span className="font-display font-bold text-ink-primary">Meta-Jungle Admin</span>
        </header>
        <main className="mx-auto max-w-6xl p-lg lg:p-xl">{children}</main>
      </div>
    </div>
  );
}
