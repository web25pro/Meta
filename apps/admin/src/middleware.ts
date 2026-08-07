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
  if (nextPath && nextPath !== '/') loginUrl.searchParams.set('next', nextPath);
  const response = NextResponse.redirect(loginUrl);
  response.cookies.delete('access_token');
  return response;
}

/**
 * Admin console middleware.
 *
 * Unlike the user app, EVERY route here is protected — the only public path is
 * /auth/login. This is a coarse gate on token presence and expiry only; the
 * authoritative Overall_Admin check happens in AdminShell (client) and, for
 * real enforcement, in the backend's require_admin dependency.
 */
export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')?.value;
  const { pathname } = request.nextUrl;

  const isAuthRoute = pathname.startsWith('/auth');
  const hasValidToken = !!token && !isTokenExpired(token);

  // Signed in and sitting on the login page → send to the console
  if (isAuthRoute) {
    if (hasValidToken) {
      return NextResponse.redirect(new URL('/', request.url));
    }
    return NextResponse.next();
  }

  // Everything else requires a valid token
  if (!hasValidToken) {
    return redirectToLogin(request, pathname);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
