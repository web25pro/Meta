'use client';

import { AdminShell } from '@meta-jungle/admin-ui';

/**
 * Admin panel mounted inside the user app at /admin.
 *
 * The panel itself lives in @meta-jungle/admin-ui so this route and the
 * standalone apps/admin deployment render the exact same components.
 */
export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <AdminShell basePath="/admin" backHref="/dashboard">
      {children}
    </AdminShell>
  );
}
