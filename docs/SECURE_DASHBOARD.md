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
- Dashboard read requests now go through the authenticated Next.js proxy,
  but the FastAPI read endpoints themselves remain directly accessible at the
  backend origin. Protect the backend origin or add backend read authorization
  before treating any metrics as private.
- Ensure the backend cannot be used to bypass authorization. All write
  endpoints must require `ZERO_CODE_WRITE_TOKEN`.
- Add rate limiting, audit logging, safe secret rotation and stronger
  sessions/MFA before exposing to multiple users.
- Buffer posting is an external side effect: use dry runs first.
- No production DB, external post, deployment or paid resource is authorized
  by this document.
