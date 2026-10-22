export const COOKIE = 'zcs_reader';
export const MAX_AGE = 6 * 60 * 60;
const enc = new TextEncoder();
const equal = (a: Uint8Array, b: Uint8Array) => {
  let diff = a.length ^ b.length;
  for (let i = 0; i < Math.max(a.length, b.length); i++) diff |= (a[i] || 0) ^ (b[i] || 0);
  return diff === 0;
};
async function signature(value: string) {
  const secret = process.env.STUDIO_SESSION_SECRET || '';
  if (secret.length < 32) throw Error('Session is not configured');
  const key = await crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  return new Uint8Array(await crypto.subtle.sign('HMAC', key, enc.encode(value)));
}
const hex = (v: Uint8Array) => Array.from(v, x => x.toString(16).padStart(2, '0')).join('');
export async function issueSession() {
  const value = `v1.${Math.floor(Date.now() / 1000) + MAX_AGE}.${crypto.randomUUID()}`;
  return `${value}.${hex(await signature(value))}`;
}
export async function validSession(token?: string) {
  if (!token) return false;
  const parts = token.split('.');
  if (parts.length !== 4 || parts[0] !== 'v1' || !/^\d+$/.test(parts[1]) || !/^[a-f0-9-]{36}$/.test(parts[2]) || !/^[a-f0-9]{64}$/.test(parts[3])) return false;
  const expiry = Number(parts[1]), now = Math.floor(Date.now() / 1000);
  if (expiry <= now || expiry > now + MAX_AGE) return false;
  try { return equal(enc.encode(parts[3]), enc.encode(hex(await signature(parts.slice(0, 3).join('.'))))); }
  catch { return false; }
}
export async function validCredentials(user: string, pass: string) {
  const expectedUser = process.env.STUDIO_VIEWER_USER || '';
  const expectedPass = process.env.STUDIO_VIEWER_PASSWORD || '';
  if (!expectedUser || !expectedPass) return false;
  const digest = async (s: string) => new Uint8Array(await crypto.subtle.digest('SHA-256', enc.encode(s)));
  return equal(await digest(`${user}\0${pass}`), await digest(`${expectedUser}\0${expectedPass}`));
}
