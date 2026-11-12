import { NextRequest } from "next/server";
import { configuration, isSameOriginRead, reply, sessionAccess, unavailable } from "../../access";

async function write(request: NextRequest, context: { params: Promise<{ operation: string }> }) {
  const { operation } = await context.params;
  const manual = operation === "manual";
  const sync = operation === "youtube" && request.method === "POST";
  if (!manual && !sync) return reply({ detail: "Not found" }, 404);

  const config = configuration();
  const token = process.env.ZERO_CODE_METRICS_WRITE_TOKEN?.trim();
  if (!config || !token || token === config.serviceToken || token === config.key) return unavailable();
  if (request.headers.get("origin") !== config.origin || !isSameOriginRead(request, config)) {
    return reply({ detail: "Forbidden" }, 403);
  }
  const access = await sessionAccess(request, config);
  if (access.denial) return access.denial;
  if (!access.canWrite) return reply({ detail: "Forbidden" }, 403);

  const headers: Record<string, string> = { "X-ZCS-Metrics-Write-Token": token, Origin: config.origin };
  let body: string | undefined;
  if (manual) {
    if (request.headers.get("content-type")?.split(";")[0] !== "application/json") {
      return reply({ detail: "Expected application/json" }, 415);
    }
    const reader = request.body?.getReader();
    if (!reader) return reply({ detail: "Missing body" }, 400);
    const chunks: Uint8Array[] = [];
    let length = 0;
    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        length += value.byteLength;
        if (length > 4096) {
          void reader.cancel().catch(() => {});
          return reply({ detail: "Request too large" }, 413);
        }
        chunks.push(value);
      }
      body = Buffer.concat(chunks).toString("utf8");
    } catch {
      return reply({ detail: "Invalid body" }, 400);
    }
    headers["Content-Type"] = "application/json";
  }

  const path = manual ? "/api/metrics/manual" : "/api/integrations/youtube/sync";
  try {
    const response = await fetch(config.backend + path, {
      method: request.method, headers, body, redirect: "error", cache: "no-store",
      signal: AbortSignal.timeout(25000),
    });
    if (!response.ok) {
      if ([409, 422].includes(response.status)) return reply({ detail: "更新条件を確認してください。" }, response.status);
      return reply({ detail: "更新結果を確認できません。" }, 502);
    }
    return reply(await response.json(), response.status);
  } catch {
    return reply({ detail: "更新結果を確認できません。" }, 502);
  }
}

export { write as POST, write as PATCH };
