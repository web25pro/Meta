/**
 * Re-export shim for backward compatibility.
 * The actual implementation moved to @meta-jungle/api-client so it can be
 * shared between apps/web and apps/admin without duplication.
 */
export {
  default,
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
  isAuthenticated,
  handleAPIError,
  configureApiClient,
} from '@meta-jungle/api-client';
export type { APIError } from '@meta-jungle/api-client';
