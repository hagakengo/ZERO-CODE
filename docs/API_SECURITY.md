# ZERO CODE OS — Write API security

All write operations require `Authorization: Bearer <token>` using the
server-only environment variable `ZERO_CODE_WRITE_TOKEN`.

Protected operations:
- `POST/PATCH /api/metrics/manual`
- `POST /api/integrations/youtube/sync`
- `POST /api/integrations/buffer/schedule` (including dry runs)

If `ZERO_CODE_WRITE_TOKEN` is missing or blank, all these endpoints return
HTTP 503 (fail closed). Missing, malformed or incorrect bearer tokens return
HTTP 401. This behavior applies to local development as well.

**Never expose this token to browser JavaScript, `NEXT_PUBLIC_*` variables,
Git, logs, or the user interface.** A frontend calling these endpoints directly
will need a separately designed, authenticated server-side proxy/session before
write features can be used safely from a public dashboard. Until then, the
browser's write buttons must not be considered production-ready.

For local CLI testing, configure a long random token in the backend process
environment and send it as a bearer header. Do not reuse the read-only
`ZERO_CODE_READ_TOKEN`. Rotate any token suspected of disclosure.

This PR does **not** provide user login, per-user roles, rate limits, CSRF
protection for future cookie sessions, or full read endpoint access control.
Review those before publishing sensitive metrics or opening the app publicly.

No production secrets, database mutations, or deployments are included.
