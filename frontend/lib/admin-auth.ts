/** Small single-operator gate. Replace with user sessions before multi-user access. */
export async function isAdminAuthorized(header: string | null): Promise<boolean> {
  const user = process.env.ZERO_CODE_ADMIN_USER;
  const pass = process.env.ZERO_CODE_ADMIN_PASSWORD;
  if (!user || !pass || !header?.startsWith("Basic ")) return false;
  let decoded: string;
  try {
    decoded = atob(header.slice(6));
  } catch {
    return false;
  }
  const colon = decoded.indexOf(":");
  if (colon < 0) return false;
  const suppliedUser = decoded.slice(0, colon);
  const suppliedPass = decoded.slice(colon + 1);
  const digest = async (value: string) =>
    new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value)));
  const [a, b] = await Promise.all([digest(suppliedUser + ":" + suppliedPass), digest(user + ":" + pass)]);
  let difference = 0;
  for (let i = 0; i < a.length; i++) difference |= a[i] ^ b[i];
  return difference === 0;
}

export function unauthorized(): Response {
  return new Response("Authentication required", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="ZERO CODE OS"', "Cache-Control": "no-store" },
  });
}
