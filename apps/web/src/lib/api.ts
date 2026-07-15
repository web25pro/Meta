import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';
import { APIError } from '@/types';

/**
 * API client — talks to the Next.js API proxy at /api/*.
 * The backend URL is a server-side secret (BACKEND_URL env var in route.ts).
 * Never expose the backend origin to the browser.
 */
const API_URL = '/api';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// ── Helpers ──────────────────────────────────────────────────────────────

function generateIdempotencyKey(): string {
  // Use crypto.randomUUID when available, fallback to random hex
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return Array.from({ length: 32 }, () =>
    Math.floor(Math.random() * 16).toString(16),
  ).join('');
}

function getCsrfToken(): string {
  if (typeof document === 'undefined') return '';
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : '';
}

// ── Request interceptor — auth token + idempotency key + CSRF token ─────

apiClient.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Attach idempotency key to mutating requests
    const method = (config.method || '').toUpperCase();
    if (['POST', 'PUT', 'PATCH'].includes(method)) {
      config.headers['X-Idempotency-Key'] = generateIdempotencyKey();
    }

    // Attach CSRF token for mutating requests
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
      const csrf = getCsrfToken();
      if (csrf) {
        config.headers['X-CSRF-Token'] = csrf;
      }
    }

    return config;
  },
  (error) => Promise.reject(error),
);

// ── Response interceptor — token refresh on 401 ─────────────────────────

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<APIError>) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

    // If 401 or 403 (expired/missing token) and not already retried, try to refresh.
    // FastAPI's HTTPBearer returns 403 "Not authenticated" for missing/expired tokens,
    // while standard auth returns 401 — handle both.
    const status = error.response?.status;
    const detail = (error.response?.data as any)?.detail;
    const isAuthError = status === 401 || (status === 403 && detail === 'Not authenticated');
    if (isAuthError && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = getRefreshToken();
        if (refreshToken) {
          const response = await axios.post(`${API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token: newRefreshToken } = response.data;
          setTokens(access_token, newRefreshToken);

          // Retry original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
          }
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        clearTokens();
        if (typeof window !== 'undefined') {
          window.location.href = '/auth/login';
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);

// ── Token management ────────────────────────────────────────────────────

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('refresh_token');
}

export function setTokens(accessToken: string, refreshToken: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem('access_token', accessToken);
  localStorage.setItem('refresh_token', refreshToken);

  // Also set cookie for Next.js middleware
  // max-age=86400 is 1 day (matches access token expiry or general session length)
  document.cookie = `access_token=${accessToken}; path=/; max-age=86400; SameSite=Lax`;
}

export function clearTokens(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');

  // Clear cookie for Next.js middleware
  document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

// Export API client
export default apiClient;

// Helper function to handle API errors
export function handleAPIError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const apiError = error.response?.data as APIError;
    if (apiError?.error?.message) {
      return apiError.error.message;
    }
    return error.message || 'An unexpected error occurred';
  }
  return 'An unexpected error occurred';
}
