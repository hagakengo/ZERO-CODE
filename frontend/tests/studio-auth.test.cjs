const { test, beforeEach } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const ts = require('typescript');
const { createHmac } = require('node:crypto');
const source = fs.readFileSync(path.join(__dirname, '../lib/studio-auth.ts'), 'utf8');
const js = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText;
const out = {}; new Function('exports', js)(out);
beforeEach(() => { process.env.STUDIO_SESSION_SECRET = 'test-only-key-that-is-long-enough-for-hmac'; process.env.STUDIO_VIEWER_USER = 'test-user'; process.env.STUDIO_VIEWER_PASSWORD = 'test-only-password'; });
test('issued session validates', async () => assert.equal(await out.validSession(await out.issueSession()), true));
test('missing and malformed sessions rejected', async () => { for (const v of [undefined,'', 'v1.1.bad.bad','Bearer anything']) assert.equal(await out.validSession(v), false); });
test('tampering rejected', async () => { const v = await out.issueSession(); assert.equal(await out.validSession(v.slice(0,-1) + (v.endsWith('0') ? '1' : '0')), false); });
function signed(exp) { const payload = `v1.${exp}.12345678-1234-1234-1234-123456789abc`; return payload + '.' + createHmac('sha256', process.env.STUDIO_SESSION_SECRET).update(payload).digest('hex'); }
test('expired session rejected', async () => assert.equal(await out.validSession(signed(Math.floor(Date.now()/1000)-1)), false));
test('overlong future session rejected', async () => assert.equal(await out.validSession(signed(Math.floor(Date.now()/1000)+out.MAX_AGE+300)), false));
test('secret rotation invalidates old session', async () => { const v = await out.issueSession(); process.env.STUDIO_SESSION_SECRET = 'another-test-only-key-at-least-32-characters'; assert.equal(await out.validSession(v), false); });
test('unconfigured secret fails closed', async () => { const v = await out.issueSession(); delete process.env.STUDIO_SESSION_SECRET; assert.equal(await out.validSession(v), false); });
test('credentials compare both fields and fail closed', async () => { assert.equal(await out.validCredentials('test-user','test-only-password'), true); assert.equal(await out.validCredentials('test-user','wrong'), false); assert.equal(await out.validCredentials('wrong','test-only-password'), false); delete process.env.STUDIO_VIEWER_PASSWORD; assert.equal(await out.validCredentials('test-user','test-only-password'), false); });
