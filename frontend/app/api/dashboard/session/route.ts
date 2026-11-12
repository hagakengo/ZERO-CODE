import { createHash } from "node:crypto";
import { NextRequest } from "next/server";
import {
  configuration, isSameOriginRead, reply, sessionAccess, sessionResponse, sessionService,
  signedSession, unavailable, unauthorized,
} from "../access";

export async function GET(request: NextRequest) {
  const config = configuration();
  if (!config) return unavailable();
  if (!isSameOriginRead(request, config)) return reply({ detail: "Forbidden" }, 403);
  const access = await sessionAccess(request, config);
  return access.denial ?? reply({ expiresAt: access.expiresAt, canWrite: access.canWrite });
}

async function loginBody(request: NextRequest) {
  const reader = request.body?.getReader();
  if (!reader) return;
  const chunks = [];
  let size = 0;
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > 2048) {
        void reader.cancel().catch(() => {});
        return;
      }
      chunks.push(value);
    }
    return JSON.parse(Buffer.concat(chunks).toString("utf-8"))?.credential;
  } catch { /* Invalid request body. */ }
}

export async function POST(request: NextRequest) {
  const config = configuration();
  if (!config) return unavailable();
  if (request.headers.get("origin") !== config.origin || !isSameOriginRead(request, config)) {
    return reply({ detail: "Forbidden" }, 403);
  }
  if (request.headers.get("content-type") !== "application/json") return reply({ detail: "Invalid request" }, 415);
  const credential = await loginBody(request);
  if (typeof credential !== "string" || !credential.length || credential.length > 256) return unauthorized();
  try {
    const response = await sessionService(config, "login", {
      digest: createHash("sha256").update(credential).digest("hex"),
      nonce: signedSession(request, config)?.nonce,
    });
    if (response.status === 403) return unauthorized();
    if (response.status === 429) {
      const limited = reply({ detail: "Too many attempts" }, 429);
      limited.headers.set("Retry-After", "300");
      return limited;
    }
    if (response.ok) {
      const { nonce, expires } = await response.json();
      const now = Math.floor(Date.now() / 1000);
      if (typeof nonce === "string" && /^[a-f0-9]{32}$/.test(nonce) &&
          Number.isSafeInteger(expires) && expires > now && expires <= now + 910) {
        return sessionResponse(config, { nonce, expires });
      }
    }
  } catch { /* Storage and transport errors deny access. */ }
  return unavailable();
}

export async function DELETE(request: NextRequest) {
  const config = configuration();
  if (!config) return unavailable();
  if (request.headers.get("origin") !== config.origin || !isSameOriginRead(request, config)) {
    return reply({ detail: "Forbidden" }, 403);
  }
  const session = signedSession(request, config);
  if (!session) return sessionResponse(config);
  try {
    if ((await sessionService(config, "revoke", session)).ok) return sessionResponse(config);
  } catch { /* Retain the cookie so revocation can be retried. */ }
  return unavailable();
}
