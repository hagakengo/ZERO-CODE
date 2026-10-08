# Secure dashboard proxy (single operator, experimental)

This branch builds on the **unmerged** write-API authentication PR #5.
The browser never receives `ZERO_CODE_WRITE_TOKEN`: Next.js route handlers
forward only three allowlisted operations to FastAPI using server-side secrets.

## Required server-side environment variables (frontend)

- `ZERO_CODE_ADMIN_USER`: operator login name.
- `ZERO_CODE_ADMIN_PASSWORD`: long, random operator password.
- `ZERO_CODE_WRITE_TOKEN`: a distinct random token, matching the FastAPI
  backend's server-only `ZERO_CODE_WRITE_TOKEN`.
- `ZERO_CODE_BACKEND_URL`: HTTPS backend origin ending in `/`, for example
  `https://example.invalid/`. Local `http://localhost:8000/` is allowed.

**Never use `NEXT_PUBLIC_` for these secrets.** Set variables in the
frontend's server environment only. Do not commit their values.

The browser receives a Basic-auth challenge on the dashboard. Use **HTTPS
only** for any non-local deployment. Basic authentication is an interim
single-operator solution; it is not user accounts, MFA or fine-grained RBAC.
Browsers may cache Basic credentials until closed.

## Remaining release blockers

- Do not merge or deploy until PR #5 is reviewed and backend/frontend
  authentication is integration-tested together.
- Dashboard reads now require a server-side bearer token at FastAPI too;
  the Next.js proxy forwards ZERO_CODE_WRITE_TOKEN for these reads. Keep the
  backend token configured and secret, and test both deployments together.
- Ensure the backend cannot be used to bypass authorization. All write
  endpoints must require `ZERO_CODE_WRITE_TOKEN`.
- Add rate limiting, audit logging, safe secret rotation and stronger
  sessions/MFA before exposing to multiple users.
- Buffer posting is an external side effect: use dry runs first.
- No production DB, external post, deployment or paid resource is authorized
  by this document.

## Read endpoint access

FastAPI `/api/status`, `/api/metrics/latest`, `/api/metrics/history`,
`/api/missions`, `/api/integrations/youtube/status`,
`/api/integrations/buffer/status`, and `/api/progression` now reject requests
without a valid bearer token. Either `ZERO_CODE_WRITE_TOKEN` or the distinct
`ZERO_CODE_READ_TOKEN` can read. Only the write token authorizes mutations.
`/health` remains public. `/api/public/status` retains its dedicated
read-token-only contract.

**Compatibility:** clients that previously fetched these endpoints without
credentials must be updated before deploying. Verify all third-party agents
and integrations; CI does not cover live authentication, rate limits or hosting.
