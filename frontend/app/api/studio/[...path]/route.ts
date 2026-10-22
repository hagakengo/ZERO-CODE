import { NextRequest, NextResponse } from 'next/server';
import { COOKIE, validSession } from '../../../../lib/studio-auth';
export const dynamic = 'force-dynamic';
async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  if (!await validSession(request.cookies.get(COOKIE)?.value)) return new NextResponse(null, { status: 401 });
  const { path } = await context.params;
  if (!(path.length === 1 && path[0] === 'index') && !(path.length === 2 && path[0] === 'media' && /^[a-zA-Z0-9_-]{1,120}$/.test(path[1]))) return new NextResponse(null, { status: 404 });
  const token = process.env.STUDIO_READER_TOKEN;
  if (!token || token.length < 32) return NextResponse.json({ detail: '制作データは未接続です' }, { status: 503 });
  const base = new URL(process.env.STUDIO_READER_URL || 'http://127.0.0.1:8135');
  if (base.protocol !== 'https:' && !(['127.0.0.1', 'localhost', '[::1]'].includes(base.hostname) && base.protocol === 'http:')) return new NextResponse(null, { status: 503 });
  const headers = new Headers({ Authorization: `Bearer ${token}` });
  const range = request.headers.get('range'); if (range) headers.set('Range', range);
  try {
    const upstream = await fetch(new URL(`/api/studio/${path.join('/')}`, base), { method: request.method, headers, cache: 'no-store', signal: AbortSignal.timeout(20_000), redirect: 'error' });
    const output = new Headers({ 'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff', 'Content-Security-Policy': "default-src 'none'; frame-ancestors 'self'" });
    for (const name of ['content-type', 'content-length', 'content-range', 'accept-ranges', 'x-asset-sha256']) {
      const value = upstream.headers.get(name); if (value) output.set(name, value);
    }
    return new NextResponse(upstream.body, { status: upstream.status, headers: output });
  } catch { return NextResponse.json({ detail: '制作データへ接続できません' }, { status: 503 }); }
}
export const GET = proxy;
export const HEAD = proxy;
