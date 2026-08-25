/**
 * @meta-jungle/admin-ui — the admin panel, mounted by both
 * `apps/web` (under /admin) and the standalone `apps/admin` deployment.
 */

export { AdminShell, type AdminShellProps } from './shell/AdminShell';

export { OverviewPage } from './pages/OverviewPage';
export { UsersPage } from './pages/UsersPage';
export { QuestsPage } from './pages/QuestsPage';
export { CampaignsPage } from './pages/CampaignsPage';
export { ReviewsPage } from './pages/ReviewsPage';
export { ClearDataPage } from './pages/ClearDataPage';

export { adminAPI } from './api/admin';
export type {
  AdminOverview,
  AdminUser,
  AdminQuest,
  AdminCampaign,
  AdminPartner,
} from './api/admin';
