'use client';

import { AdminShell } from '@meta-jungle/admin-ui';

/**
 * Chrome for the admin console.
 *
 * `basePath=""` because this app is mounted at the domain root — nav hrefs are
 * `/users`, `/quests`, … (in apps/web the same shell mounts under `/admin`).
 * `backHref={null}` hides "Back to app": this deployment has no user-facing app.
 */
export default function PanelLayout({ children }: { children: React.ReactNode }) {
  return (
    <AdminShell basePath="" backHref={null}>
      {children}
    </AdminShell>
  );
}
