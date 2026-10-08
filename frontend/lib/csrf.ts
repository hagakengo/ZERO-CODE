import { NextRequest, NextResponse } from "next/server";

/** Basic auth is browser-managed ambient authority: every mutation needs Origin.
 * Use a configured public origin, never attacker-controlled forwarded headers.
 */
export function rejectUnsafeMutation(request: NextRequest): Response | null {
  if (["GET", "HEAD", "OPTIONS"].includes(request.method)) return null;
  const configured = process.env.ZERO_CODE_FRONTEND_ORIGIN;
  let trusted: URL;
  try {
    if (!configured) throw new Error("Missing origin");
    trusted = new URL(configured);
    const local = ["localhost", "127.0.0.1", "[::1]"].includes(trusted.hostname);
    if (trusted.origin !== configured || trusted.username || trusted.password ||
        (trusted.protocol !== "https:" && !(trusted.protocol === "http:" && local))) {
      throw new Error("Invalid origin");
    }
  } catch {
    return NextResponse.json({ detail: "Frontend origin is not configured" }, {
      status: 503, headers: { "Cache-Control": "no-store" },
    });
  }
  // Missing/null/multiple/malformed origins fail closed, including HTTP clients.
  // Forwarded Host/Proto are intentionally ignored; deployment must preserve Host.
  if (request.headers.get("origin") !== trusted.origin ||
      request.headers.get("host")?.toLowerCase() !== trusted.host.toLowerCase() ||
      request.headers.get("sec-fetch-site") === "cross-site") {
    return NextResponse.json({ detail: "Request origin is not allowed" }, {
      status: 403, headers: { "Cache-Control": "no-store" },
    });
  }
  return null;
}
