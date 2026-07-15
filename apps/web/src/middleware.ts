import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/** Check if a JWT is expired by decoding its payload (no signature check needed). */
function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    // exp is in seconds; add 30s buffer for clock skew
    return typeof payload.exp !== 'number' || payload.exp < Date.now() / 1000 - 30;
  } catch {
    // Malformed token — treat as expired
    return true;
  }
}

/** Build a redirect to /auth/login, clearing the stale cookie in the process. */
function redirectToLogin(request: NextRequest, nextPath?: string): NextResponse {
  const loginUrl = new URL('/auth/login', request.url);
  if (nextPath) loginUrl.searchParams.set('next', nextPath);
  const response = NextResponse.redirect(loginUrl);
  response.cookies.delete('access_token');
  return response;
}

export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')?.value;
  const { pathname } = request.nextUrl;

  // Public routes that don't require authentication
  const publicRoutes = ['/', '/auth/login', '/auth/register', '/privacy', '/terms', '/support'];
  const isPublicRoute =
    publicRoutes.includes(pathname) ||
    pathname.startsWith('/auth') ||
    pathname.startsWith('/_next');

  // Protected routes that need a valid token
  const isProtectedRoute = pathname.startsWith('/dashboard') || pathname.startsWith('/admin');

  if (isProtectedRoute) {
    // No token at all → go to login
    if (!token) {
      return redirectToLogin(request, pathname);
    }
    // Token exists but is expired → clear it and go to login
    if (isTokenExpired(token)) {
      return redirectToLogin(request, pathname);
    }
  }

  // If logged in with a valid token and trying to access auth pages, redirect to dashboard
  if (token && !isTokenExpired(token) && (pathname === '/auth/login' || pathname === '/auth/register')) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
