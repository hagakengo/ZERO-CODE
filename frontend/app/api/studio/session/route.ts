import { NextRequest, NextResponse } from 'next/server';
import { COOKIE, MAX_AGE, issueSession, validCredentials } from '../../../../lib/studio-auth';
export const dynamic = 'force-dynamic';
// Single-process pilot limiter. Shared rate limiting is required before public deployment.
const attempts = new Map<string, { count: number; until: number }>();
function sameOrigin(request: NextRequest) {
  return request.headers.get('origin') === request.nextUrl.origin;
}
export async function POST(request: NextRequest) {
  if (!sameOrigin(request)) return new NextResponse(null, { status: 403 });
  if (request.nextUrl.protocol !== 'https:' && !['localhost', '127.0.0.1', '[::1]'].includes(request.nextUrl.hostname)) return new NextResponse(null, { status: 403 });
  if (Number(request.headers.get('content-length') || 0) > 4096) return new NextResponse(null, { status: 413 });
  if (!process.env.STUDIO_VIEWER_USER || !process.env.STUDIO_VIEWER_PASSWORD || (process.env.STUDIO_SESSION_SECRET || '').length < 32)
    return NextResponse.json({ detail: '閲覧用ログインが未設定です' }, { status: 503 });
  // Global bucket avoids trusting spoofable X-Forwarded-For in a local pilot.
  const key = 'viewer', now = Date.now();
  const entry = attempts.get(key);
  if (entry && entry.until > now && entry.count >= 10) return NextResponse.json({ detail: 'しばらく待って再試行してください' }, { status: 429 });
  let form: FormData;
  try { form = await request.formData(); } catch { return new NextResponse(null, { status: 400 }); }
  const user = String(form.get('username') || ''), pass = String(form.get('password') || '');
  if (user.length > 128 || pass.length > 512 || !await validCredentials(user, pass)) {
    const bucket = entry && entry.until > now ? entry : { count: 0, until: now + 60_000 };
    bucket.count++; attempts.set(key, bucket);
    return NextResponse.redirect(new URL('/production/login?error=1', request.url), 303);
  }
  attempts.delete(key);
  const response = NextResponse.redirect(new URL('/production', request.url), 303);
  response.cookies.set(COOKIE, await issueSession(), { httpOnly: true, sameSite: 'strict', secure: request.nextUrl.protocol === 'https:', path: '/', maxAge: MAX_AGE });
  response.headers.set('Cache-Control', 'no-store');
  return response;
}
export async function DELETE(request: NextRequest) {
  if (!sameOrigin(request)) return new NextResponse(null, { status: 403 });
  const response = NextResponse.json({ ok: true });
  response.cookies.set(COOKIE, '', { httpOnly: true, sameSite: 'strict', path: '/', maxAge: 0 });
  response.headers.set('Cache-Control', 'no-store');
  return response;
}
