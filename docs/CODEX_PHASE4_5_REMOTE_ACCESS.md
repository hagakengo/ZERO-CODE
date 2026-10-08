# CODEX TASK — ZERO CODE OS Phase 4.5 Remote Access

## Objective
Make ZERO CODE OS usable from iPhone and make current statistics retrievable remotely.

## Priority
This is the highest-priority task before HUD/video automation.

## Target repository
`hagakengo/ZERO-CODE`

## Goals
1. Move production persistence from SQLite to PostgreSQL.
2. Deploy the app publicly with Vercel where practical.
3. Preserve all existing Phase 1–4 behavior.
4. Expose a safe read-only status endpoint that can later be queried by ChatGPT/agents.
5. Keep secrets private and never expose raw credentials.

## Recommended architecture
- Frontend: Next.js on Vercel
- Backend: FastAPI
- Database: PostgreSQL
- Provider: prefer Supabase Postgres or Neon; choose the lowest-friction option for the current codebase.
- Keep local SQLite support for development/tests if practical, but production should use PostgreSQL through `DATABASE_URL`.

## Required work

### 1. PostgreSQL compatibility
- Audit current SQLAlchemy models and migrations.
- Make all production DB logic PostgreSQL-compatible.
- Avoid SQLite-specific production assumptions.
- Preserve existing schema/data concepts:
  - daily_metrics
  - missions
  - progression / XP
  - YouTube integration metadata
  - mission completion history
- Provide a safe migration path from the current SQLite DB.
- Do not fabricate historical data.

### 2. Production configuration
- Production `DATABASE_URL` via environment variable only.
- No secrets committed.
- Update `.env.example` with placeholders only.
- Document required production env vars.

### 3. Remote read-only API
Add a safe endpoint, e.g.:
`GET /api/public/status`

It should return only non-sensitive operational data needed for analytics:
- current date/day
- level
- XP / XP to next level
- YouTube subscribers/views and observation timestamps
- TikTok followers/views and observation timestamps
- total revenue
- active mission
- mission progress/status
- latest deltas
- last updated timestamp

Do NOT return:
- OAuth tokens
- API keys
- channel secrets
- raw internal errors
- any personal identifiers

Protect this endpoint with a simple read token, e.g.:
`ZERO_CODE_READ_TOKEN`

Supported auth:
`Authorization: Bearer <token>`

Return 401 without a valid token.

### 4. Vercel/public deployment
- Deploy the Next.js frontend.
- Deploy FastAPI in a Vercel-compatible way if robust.
- If FastAPI on Vercel is awkward for persistent/long-running integration flows, use a minimal alternative hosting approach and document why.
- Ensure frontend can call backend from production.
- Configure CORS safely.
- Confirm iPhone access over HTTPS.

### 5. Existing integrations
Do not break:
- YouTube OAuth/sync
- Buffer integration
- manual TikTok/revenue input
- history
- XP/DAY/LEVEL
- mission completion

For OAuth callback constraints in production, document any required Google Cloud redirect URI changes.

### 6. Validation
Add/update tests for:
- PostgreSQL-compatible models/queries
- public status endpoint auth
- public status response shape
- no secret leakage
- existing APIs remain functional

Run:
- backend tests
- frontend build
- git diff --check

### 7. Documentation
Update README with:
- PostgreSQL setup
- chosen provider setup
- production env vars
- Vercel deployment steps
- Google OAuth production callback setup
- how to verify the public status endpoint safely
- iPhone access URL

## Definition of done
- Production data persists in PostgreSQL.
- Public HTTPS dashboard works from iPhone.
- Existing ZERO CODE OS dashboard loads real stored data.
- `GET /api/public/status` is reachable remotely with Bearer auth.
- Invalid/missing token returns 401.
- No secrets are exposed.
- Existing tests pass.
- Changes committed and pushed to `main`.

## Important rule
Reality is the database.
Never create synthetic success metrics, fake progression, or historical backfill that did not occur.
