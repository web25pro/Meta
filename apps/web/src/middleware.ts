import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')?.value;
  const { pathname } = request.nextUrl;

  // Public routes that don't require authentication
  // Include the auth group paths so /auth/register and /auth/login are public
  const publicRoutes = ['/', '/auth/login', '/auth/register', '/privacy', '/terms', '/support'];
  const isPublicRoute =
    publicRoutes.includes(pathname) ||
    pathname.startsWith('/auth') ||
    pathname.startsWith('/_next');

  // If trying to access a protected route without a token, redirect to login.
  // Preserve the original destination in a `next` query param so the login
  // page can redirect back after authentication.
  // (Admin pages additionally enforce the Overall_Admin role client-side.)
  if (!isPublicRoute && !token && (pathname.startsWith('/dashboard') || pathname.startsWith('/admin'))) {
    const loginUrl = new URL('/auth/login', request.url);
    loginUrl.searchParams.set('next', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // If logged in and trying to access auth pages, redirect to dashboard
  if (token && (pathname === '/auth/login' || pathname === '/auth/register')) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
