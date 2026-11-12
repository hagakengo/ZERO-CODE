import { createHmac, timingSafeEqual } from "node:crypto";
import { NextRequest, NextResponse } from "next/server";

const headers = { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" };

export function reply(body: object, status = 200) {
  return NextResponse.json(body, { status, headers });
}

function httpOrigin(value: string | undefined) {
  try {
    const url = new URL(value || "");
    const loopback = ["127.0.0.1", "localhost", "[::1]"].includes(url.hostname);
    if (url.origin === value && (url.protocol === "https:" || (loopback && url.protocol === "http:"))) {
      return url.origin;
    }
  } catch { /* Missing or malformed configuration. */ }
}

export function configuration() {
  const origin = httpOrigin(process.env.ZCS_DASHBOARD_ORIGIN);
  const backend = httpOrigin(process.env.ZCS_DASHBOARD_API_ORIGIN);
  const key = process.env.ZCS_DASHBOARD_SESSION_KEY;
  const serviceToken = process.env.ZCS_DASHBOARD_SESSION_SERVICE_TOKEN;
  if (!origin || !backend || origin === backend ||
      !key || !/^[0-9a-f]{64}$/.test(key) || !serviceToken || !/^[0-9a-f]{64}$/.test(serviceToken) ||
      serviceToken === key) return;
  const secure = origin.startsWith("https:");
  return { origin, backend, key, serviceToken, secure, cookie: secure ? "__Host-zcs-dashboard" : "zcs-dashboard-local" };
}

type Configuration = NonNullable<ReturnType<typeof configuration>>;

function sign(config: Configuration, expires: number, nonce: string) {
  return createHmac("sha256", Buffer.from(config.key, "hex"))
    .update(JSON.stringify(["dashboard-session-v2", config.origin, expires, nonce]))
    .digest("hex");
}

export function signedSession(request: NextRequest, config: Configuration) {
  const match = /^(\d{1,12})\.([0-9a-f]{32})\.([0-9a-f]{64})$/.exec(request.cookies.get(config.cookie)?.value || "");
  if (!match) return;
  const expires = Number(match[1]);
  if (expires <= 0) return;
  if (timingSafeEqual(Buffer.from(match[3], "hex"), Buffer.from(sign(config, expires, match[2]), "hex"))) {
    return { expires, nonce: match[2] };
  }
}

export function sessionResponse(config: Configuration, session?: { expires: number; nonce: string }) {
  const response = reply(session ? { expiresAt: session.expires * 1000 } : {});
  const value = session ? `${session.expires}.${session.nonce}.${sign(config, session.expires, session.nonce)}` : "";
  response.cookies.set(config.cookie, value, {
    httpOnly: true, secure: config.secure, sameSite: "strict", path: "/",
    maxAge: session ? Math.max(0, session.expires - Math.floor(Date.now() / 1000)) : 0,
  });
  return response;
}

export async function sessionService(config: Configuration, operation: "login" | "check" | "revoke", body: object) {
  return fetch(`${config.backend}/api/internal/dashboard-session/${operation}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${config.serviceToken}`, "Content-Type": "application/json" },
    body: JSON.stringify(body), cache: "no-store", redirect: "error", signal: AbortSignal.timeout(5000),
  });
}

export async function sessionAccess(request: NextRequest, config: Configuration) {
  const session = signedSession(request, config);
  if (!session || session.expires <= Math.floor(Date.now() / 1000)) return { denial: unauthorized() };
  try {
    const response = await sessionService(config, "check", session);
    if (response.ok) {
      const { active, canWrite } = await response.json();
      if (active === true) return { expiresAt: session.expires * 1000, canWrite: canWrite === true };
      if (active === false) return { denial: unauthorized() };
    }
  } catch { /* Storage and transport errors deny access. */ }
  return { denial: unavailable() };
}

export function isSameOriginRead(request: NextRequest, config: Configuration) {
  const origin = request.headers.get("origin");
  const site = request.headers.get("sec-fetch-site");
  return (!origin || origin === config.origin) && (!site || site === "same-origin");
}

export const unavailable = () => reply({ detail: "Dashboard unavailable" }, 503);
export const unauthorized = () => reply({ detail: "Unauthorized" }, 401);
