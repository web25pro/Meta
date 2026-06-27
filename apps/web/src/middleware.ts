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

  // If trying to access protected route without token, redirect to login
  if (!isPublicRoute && !token && pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/auth/login', request.url));
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
