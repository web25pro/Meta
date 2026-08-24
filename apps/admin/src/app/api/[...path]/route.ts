import { NextRequest, NextResponse } from 'next/server';

/**
 * Next.js API route proxy.
 *
 * All /api/* requests are forwarded to the backend URL defined in
 * BACKEND_URL (server-side only — never exposed to the browser).
 *
 * Keeping this proxy in the admin app means browser->backend traffic stays
 * same-origin, so the backend needs no CORS entry and no SameSite relaxation
 * on its CSRF cookie.
 */

const BACKEND_URL = (process.env.BACKEND_URL || 'https://meta-4bck.onrender.com/api/v1').replace(/\/+$/, '');

// Headers that should NOT be forwarded from the client to the backend
const HOP_BY_HOP_HEADERS = new Set([
  'connection',
  'keep-alive',
  'transfer-encoding',
  'te',
  'trailer',
  'upgrade',
  'proxy-authorization',
  'proxy-authenticate',
  'host',
]);

// Headers that should NOT be forwarded from the backend to the client.
// Node.js fetch() auto-decompresses gzip/br/deflate, so forwarding
// Content-Encoding causes ERR_CONTENT_DECODING_FAILED in the browser.
const BACKEND_STRIP_HEADERS = new Set([
  'content-encoding',
  'content-length',
  'transfer-encoding',
]);

function buildBackendUrl(path: string[], searchParams: string): string {
  const joined = path.join('/');
  const qs = searchParams ? `?${searchParams}` : '';
  return `${BACKEND_URL}/${joined}${qs}`;
}

function forwardHeaders(request: NextRequest): Record<string, string> {
  const headers: Record<string, string> = {};

  request.headers.forEach((value, key) => {
    if (!HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
      headers[key] = value;
    }
  });

  // Ensure the backend sees the original client IP
  const forwardedFor = request.headers.get('x-forwarded-for');
  if (!forwardedFor) {
    // In production behind a proxy, this is set automatically
    headers['x-forwarded-for'] = request.ip || '127.0.0.1';
  }

  return headers;
}

async function proxyRequest(
  request: NextRequest,
  params: { path: string[] },
  method: string,
): Promise<NextResponse> {
  const url = buildBackendUrl(params.path, request.nextUrl.searchParams.toString());
  const headers = forwardHeaders(request);

  let body: BodyInit | undefined;
  if (!['GET', 'HEAD'].includes(method)) {
    body = await request.arrayBuffer();
  }

  try {
    const backendResponse = await fetch(url, {
      method,
      headers,
      body,
    });

    // Build response, forwarding status + headers from backend.
    // Strip Content-Encoding/Content-Length because fetch() auto-decompresses
    // the body — forwarding those headers would cause ERR_CONTENT_DECODING_FAILED.
    const responseHeaders = new Headers();
    backendResponse.headers.forEach((value, key) => {
      if (!BACKEND_STRIP_HEADERS.has(key.toLowerCase())) {
        responseHeaders.set(key, value);
      }
    });

    // Forward Set-Cookie headers from the backend.
    // Node.js 18+ (undici) filters Set-Cookie out of headers.forEach() —
    // they are only accessible via getSetCookie(). Without this, cookies
    // set by the backend (e.g. csrf_token) never reach the browser, causing
    // every mutating request to fail CSRF validation.
    const setCookies =
      typeof backendResponse.headers.getSetCookie === 'function'
        ? backendResponse.headers.getSetCookie()
        : [];
    for (const cookie of setCookies) {
      responseHeaders.append('set-cookie', cookie);
    }

    return new NextResponse(backendResponse.body, {
      status: backendResponse.status,
      statusText: backendResponse.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error('[API Proxy] Error forwarding request:', error);
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'PROXY_ERROR',
          message: 'Failed to reach the backend service.',
          details: {},
        },
      },
      { status: 502 },
    );
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } },
) {
  return proxyRequest(request, await params, 'GET');
}

export async function POST(
  request: NextRequest,
  { params }: { params: { path: string[] } },
) {
  return proxyRequest(request, await params, 'POST');
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { path: string[] } },
) {
  return proxyRequest(request, await params, 'PUT');
}

export async function PATCH(
  request: NextRequest,
  { params }: { params: { path: string[] } },
) {
  return proxyRequest(request, await params, 'PATCH');
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { path: string[] } },
) {
  return proxyRequest(request, await params, 'DELETE');
}
