import { NextRequest, NextResponse } from "next/server";
import { isAdminAuthorized, unauthorized } from "../../../../lib/admin-auth";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const actions: Record<string, { path: string; method: string }> = {
  manual: { path: "/api/metrics/manual", method: "PATCH" },
  youtube: { path: "/api/integrations/youtube/sync", method: "POST" },
  buffer: { path: "/api/integrations/buffer/schedule", method: "POST" },
};

async function proxy(request: NextRequest, action: string): Promise<Response> {
  if (!(await isAdminAuthorized(request.headers.get("authorization")))) return unauthorized();
  const target = actions[action];
  if (!target || request.method !== target.method) return NextResponse.json({ detail: "Not found" }, { status: 404 });
  const api = process.env.ZERO_CODE_BACKEND_URL;
  const token = process.env.ZERO_CODE_WRITE_TOKEN;
  if (!api || !token) return NextResponse.json({ detail: "Write API is not configured" }, { status: 503 });
  let base: URL;
  try {
    base = new URL(api);
    if (base.protocol !== "https:" && !(base.protocol === "http:" && ["localhost", "127.0.0.1"].includes(base.hostname))) throw new Error("Unsafe API protocol");
    if (base.username || base.password || base.search || base.hash || base.pathname !== "/") throw new Error("Invalid API base");
  } catch {
    return NextResponse.json({ detail: "Backend URL is invalid" }, { status: 503 });
  }
  try {
    const body = action === "youtube" ? undefined : await request.text();
    if (body && body.length > 8192) return NextResponse.json({ detail: "Payload too large" }, { status: 413 });
    const upstream = await fetch(new URL(target.path, base), {
      method: target.method,
      headers: { Authorization: `Bearer ${token}`, ...(body === undefined ? {} : { "Content-Type": "application/json" }) },
      body,
      cache: "no-store",
      signal: AbortSignal.timeout(20000),
    });
    const responseBody = await upstream.text();
    return new Response(responseBody, {
      status: upstream.status,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    });
  } catch {
    return NextResponse.json({ detail: "Backend unavailable" }, { status: 502 });
  }
}

type RouteContext = { params: Promise<{ action: string }> };
export async function POST(request: NextRequest, context: RouteContext) {
  return proxy(request, (await context.params).action);
}
export async function PATCH(request: NextRequest, context: RouteContext) {
  return proxy(request, (await context.params).action);
}
