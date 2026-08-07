/**
 * Re-export shim for backward compatibility.
 * The admin API client moved to @meta-jungle/admin-ui so it can be shared
 * between apps/web and the standalone apps/admin deployment.
 */
export { adminAPI } from '@meta-jungle/admin-ui';
export type {
  AdminOverview,
  AdminUser,
  AdminQuest,
  AdminCampaign,
  AdminPartner,
} from '@meta-jungle/admin-ui';
