/**
 * Error envelope returned by the FastAPI backend.
 *
 * Structurally identical to the `APIError` in `apps/web/src/types` — kept here
 * so this package has no dependency on any app's local types.
 */
export interface APIError {
  success: false;
  error: {
    code: string;
    message: string;
    details: Record<string, any>;
  };
}
