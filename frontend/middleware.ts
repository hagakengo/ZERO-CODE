import { NextRequest, NextResponse } from 'next/server';
import { COOKIE, validSession, localPilotEnabled } from './lib/studio-auth';
export async function middleware(request: NextRequest) {
  if (!localPilotEnabled() || !['localhost', '127.0.0.1', '[::1]'].includes(request.nextUrl.hostname))
    return NextResponse.json({ detail: 'ローカル検証専用です。外部公開用認証は未実装です' }, { status: 503, headers: { 'Cache-Control': 'no-store' } });
  const path = request.nextUrl.pathname;
  if (path === '/production/login' || path === '/api/studio/session') return NextResponse.next();
  if (!await validSession(request.cookies.get(COOKIE)?.value)) {
    if (path.startsWith('/api/')) return NextResponse.json({ detail: '認証が必要です' }, { status: 401, headers: { 'Cache-Control': 'no-store' } });
    return NextResponse.redirect(new URL('/production/login', request.url));
  }
  const response = NextResponse.next();
  response.headers.set('Cache-Control', 'private, no-store');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('Referrer-Policy', 'same-origin');
  return response;
}
export const config = { matcher: ['/production/:path*', '/api/studio/:path*'] };
