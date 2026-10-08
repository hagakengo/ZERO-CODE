# ZERO CODE

AI Agent Studio / Original Cinematic IP Production Repository.

## 理念とAI社員の共通指針

- [理念・行動指針](docs/ZERO_CODE_PHILOSOPHY.md)：社訓、事業・開発原則、証拠と安全の基準。
- [AGENTS.md](AGENTS.md)：AI社員・エージェントの作業開始時の必読指示。
- [制作ルール](ZERO_CODE_RULES.md) / [プロジェクト背景](PROJECT_CONTEXT.md)：正史・資産の制約と背景。

理念は判断基準です。未検証の接続・本番稼働・収益を達成実績として記載しません。

## ZERO CODE OS Phase 1

Phase 1 adds a local FastAPI + Next.js + SQLite foundation. It seeds one mission and keeps all initial metrics at zero.

## Local startup

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. API health is available at http://localhost:8000/health. YouTube and TikTok integrations are intentionally not included in Phase 1.

`GET /api/status` returns the latest saved `daily_metrics` row and the initial mission.
The dashboard reads this endpoint for DAY, LEVEL, both platform counters, revenue,
and mission progress. All counters, including DAY and LEVEL, start at zero.
Startup seeds metrics only when the table is empty; restarting preserves saved data.
DAY and LEVEL remain stored values until progression rules are defined.
MISSION 01 progress is calculated from revenue and capped at 100%.

Optional configuration: copy `frontend/.env.example` to `frontend/.env.local`.
For the backend, export `DATABASE_URL` in the shell to override the default SQLite
path (see `backend/.env.example`); `backend/.env` is loaded automatically in Phase 3.

Run isolated health/status tests without modifying the development database:

```bash
cd backend
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m unittest -v test_api
```

## ZERO CODE OS Phase 2 — daily manual updates

Open the dashboard and use **UPDATE MANUAL → SAVE TODAY** to enter TikTok
followers, TikTok views, and total revenue in whole yen. Enter **cumulative totals**,
not increments. Blank fields are unchanged; an explicit `0` records a measured zero.
Only nonnegative integers up to JavaScript's safe integer maximum are accepted.
Saving updates the dashboard and mission immediately; errors retain your input for retry.

- The backend determines today's date in `METRICS_TIMEZONE` (default `Asia/Tokyo`).
  Set this IANA timezone before startup and keep it consistent for the database.
- Saving again on the same date updates that row. The first save on a new date
  creates a row carrying the last saved counters, DAY and LEVEL. No automatic
  progression or synthetic rows are generated on days without input.
- Each manually supplied field records its observation date. Omitted/carried
  fields retain their original observation date. Initial and migrated Phase 1
  values have unknown provenance, displayed as 未入力・未取得（初期値／既存値）.
- Deltas compare the latest record with the **previous calendar date**, not the
  previous available row. Both fields must have been observed on their row dates;
  missing observations or dates yield JSON `null` / dashboard `—`. Negative
  changes are allowed. The dashboard shows the record date and last observation.
- In Phase 2, YouTube stays unconnected. Existing/zero counters are preserved and labeled;
  manual requests cannot write YouTube values. No YouTube/TikTok API calls occur.
- `MISSION 01` uses `metric_type=revenue`, `target_value=1`. Progress is clamped
  to 0–100 from current value / target. Status becomes completed at the target
  and returns to active if totals are corrected downward. Locked missions stay
  locked. `/api/missions` and `/api/status` use the same derived calculation.
  `followers`/`views` mean TikTok; explicit column names are also supported.
  Unknown metric types or nonpositive targets return unavailable progress (`null`).

### Phase 2 API

- `GET /api/status`: dashboard state, date/timezone, observation dates, deltas, mission.
- `GET /api/metrics/latest`: latest persisted daily row.
- `GET /api/metrics/history?limit=30`: newest-first rows; limit 1–366.
- `POST /api/metrics/manual` or `PATCH /api/metrics/manual`: partial cumulative
  totals for today; returns the refreshed status. Empty objects, nulls, unknown
  fields, negative/fractional values and numeric strings are rejected (422).

Example for an **isolated test database only** (these are test inputs, not real results):

```bash
curl -X PATCH http://localhost:8000/api/metrics/manual \
  -H 'Content-Type: application/json' \
  -d '{"tiktok_followers": 10, "tiktok_views": 100, "total_revenue_yen": 1}'
curl http://localhost:8000/api/metrics/history
```

Startup automatically adds Phase 2 columns to the existing SQLite database;
existing rows and counters are preserved. Back up `backend/zero_code.db` before
upgrading. Migrations are idempotent; SQLite manual writes are serialized to
protect same-day and concurrent rollover updates. This is a local, single-user
app without authentication; run it on localhost.

### Validation

```bash
cd backend
source .venv/bin/activate
python -m unittest -v test_api
cd ../frontend
npm run build
```

Backend tests use a temporary database, including a reconstructed Phase 1 schema,
validation, partial updates, explicit zero, rollover, missing days, negative deltas,
YouTube observation rules, mission calculation and concurrent writes.
For a local smoke test without touching real data, launch the backend with
`DATABASE_URL=sqlite:////tmp/zero-code-phase2-smoke.db` and use the dashboard form.
Scheduled sync, historical backfill editing, history charts and DAY/LEVEL
progression rules remain future work.

If default ports are occupied, set `NEXT_PUBLIC_API_URL` before building/starting
the frontend and `CORS_ORIGINS` (comma-separated frontend origins) before starting
the backend. Defaults allow localhost and 127.0.0.1 on frontend port 3000.


## ZERO CODE OS Phase 3 — YouTube sync

Requires Python **3.11 or 3.12** and Node.js 20+. Install updated backend dependencies.
This remains a **localhost, single-user app**: bind Uvicorn to `127.0.0.1`, use one
worker, and do not expose these unauthenticated endpoints on a public network.
The backend allows localhost hosts and rejects foreign browser origins on sync.

### Google Cloud / OAuth setup

1. Create/select a project in [Google Cloud Console](https://console.cloud.google.com/).
   Enable **YouTube Data API v3** and **YouTube Analytics API** in APIs & Services.
2. Configure Google Auth Platform branding and audience (OAuth consent screen).
   For External / Testing, add your channel-owning Google account as a test user.
   Request only `https://www.googleapis.com/auth/youtube.readonly` and
   `https://www.googleapis.com/auth/yt-analytics.readonly` under Data Access.
3. Create an OAuth client with application type **Desktop app**. Copy its client ID
   and client secret into `backend/.env` using the example below. Do not commit a
   downloaded client JSON. Service accounts are not used for this channel-owner flow.
4. Find your channel ID (`UC...`) in YouTube Settings → Advanced settings. Put it in
   `YOUTUBE_CHANNEL_ID`. OAuth must authorize that same channel; for a Brand Account,
   choose the correct channel during consent. A mismatch fails without changing metrics.
5. Run the helper locally; it opens Google's consent page, uses state validation and
   PKCE, and listens on a random `127.0.0.1` port for at most 180 seconds. A Desktop
   client supports this loopback redirect; no web callback endpoint is exposed.

```bash
cd backend
cp .env.example .env  # first setup only; do not overwrite an existing .env
chmod 600 .env
# Edit .env: YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_CHANNEL_ID
source .venv/bin/activate
pip install -r requirements.txt
python youtube_authorize.py
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The helper writes the refresh token to **backend/.env only**, with owner-only
permissions. Access tokens remain in memory; neither token nor client secret is
stored in SQLite, browser storage, API responses or Git. Credentials are read from
this file, not frontend variables or shell exports. `.env` and `.env.*` are ignored,
except placeholder `.env.example` files. Do not paste credentials into chat or logs.

External apps in Testing may receive refresh tokens that expire after seven days.
If access expires/revokes, rerun `python youtube_authorize.py`; for longer-term use,
review Google's publishing/verification requirements. Removing the refresh token
from `.env` disconnects future sync; revoke access in your Google account to invalidate it.

### Dashboard and API

Click **SYNC YOUTUBE**. After first successful sync, the panel shows 接続済み,
last successful sync and observed date; credentials alone do not claim a verified connection.
The button fetches real data; no scheduler or background periodic sync is installed.

- `POST /api/integrations/youtube/sync`: refreshes OAuth access, reads the authorized
  channel's `statistics.subscriberCount` and `statistics.viewCount`, and overwrites
  today's cumulative counters. Returns `{status, integration}`. Same-day retries do
  not add counts. The observation date uses `METRICS_TIMEZONE` at save time.
- `GET /api/integrations/youtube/status`: returns `state` (`disconnected`, `connected`,
  `error`), `configured`, safe `error`/`warning`, `last_synced_at` (UTC), and
  `last_observed_on`. It makes no Google requests; connected means last sync succeeded,
  not that remote authorization has just been revalidated.
- Missing configuration / overlapping sync returns 409. Google authentication,
  quota, timeout, hidden subscriber count, channel mismatch or malformed required
  data returns 502; no metrics rows, counters or observation dates change.
- Optional Analytics requests `estimatedMinutesWatched`, `likes`, `comments` over
  `YOUTUBE_ANALYTICS_START_DATE` (default 2005-01-01) through yesterday. These are
  **period totals**, not today's activity or the Data API lifetime view count.
  Google may return data only through its latest available reporting date; the stored
  end date is the **requested** end, not a freshness guarantee. Analytics uses Pacific
  reporting dates and can lag behind the dashboard's local day.
- Analytics values and requested dates are available in `/api/metrics/latest` and
  `/api/metrics/history`, with separate `observed_on.youtube_analytics`. No rows or
  failed Analytics calls retain all previous Analytics values and dates, returning a
  warning while saving valid Data API counters. Set `YOUTUBE_ANALYTICS_ENABLED=false`
  to skip these optional reports. Unobserved Analytics is not treated as a mission result.
- Unobserved YouTube dashboard counters show **未取得**; observed zero shows **0**.
  For compatibility, raw history counters retain Phase 1/2 numeric defaults; consumers
  must use observation dates to distinguish unobserved values. YouTube missions return
  null progress until their corresponding observation exists.
- Subscriber totals may be rounded by YouTube. Data API counts and Studio Analytics
  can differ in timing and definition; the app does not invent precision.

Startup adds nullable Analytics date columns and a non-secret integration status
record table, preserving Phase 1/2 history. Back up the SQLite database before upgrade.
Manual TikTok/revenue saves, daily carry-forward, deltas and revenue missions retain
Phase 2 behavior. API errors keep the last good metrics and last successful timestamp.

### Isolated verification

```bash
cd backend
python -m unittest -v test_api test_youtube
cd ../frontend
npm ci
npm run build
```

Tests use a temporary SQLite database and mocked HTTP transport (no Google account,
real credentials or development database required). Coverage includes real zeros,
auth/quota/server errors, timeout, missing/hidden statistics, channel mismatch,
Analytics failure, migrations, repeated sync, rollover, mission updates and concurrent
manual/sync saves. Actual Google consent and live sync require the owner's setup above.
TikTok API, automatic posting and scheduled polling remain outside Phase 3.

References: [Desktop OAuth](https://developers.google.com/identity/protocols/oauth2/native-app),
[Channel statistics](https://developers.google.com/youtube/v3/docs/channels),
[Analytics reports](https://developers.google.com/youtube/analytics/reference/reports/query).

## ZERO CODE OS Phase 4 — real history progression

Phase 4 supersedes the earlier stored DAY/LEVEL placeholders and reversible
mission status. No historical counters, observations, or blank days are invented.

- **DAY** is the number of distinct saved dates with at least one observation
  dated that same day. First actual record is DAY 1; no records means DAY 0.
  Initial/unknown-provenance rows and carried values alone do not count.
  Missing calendar days neither advance DAY nor create rows.
- **XP** = recorded dates × **10** + evidenced completed missions × **100**.
  Same-day overwrites, reads, restarts and failed syncs give no extra XP. Explicit
  observed zero is a real record; unknown zero is not. XP is derived from evidence,
  with no arbitrary XP award endpoint. Rules are the constants `DAILY_RECORD_XP`,
  `MISSION_COMPLETION_XP`, `XP_PER_LEVEL` in `backend/app/main.py`.
- **LEVEL** is 0 before any record, otherwise `1 + floor(XP / 100)`.
  **NEXT LEVEL** displays remaining XP (`100 - XP % 100`). Stored row snapshots
  (`day`, `level`, `xp`) are rebuilt on startup and successful writes.
- Missions support the existing metric types and targets. An unlocked mission
  completes only with observed evidence meeting its positive target. Its first
  `completed_at` (UTC) and `completed_recorded_on` persist. Later lower totals do
  not erase that achievement or award it again. There is no mission editor or
  automatic next mission; MISSION 01 remains visible as **MISSION COMPLETE**.
- On migration, only saved same-day observation evidence can establish historical
  completion. The earliest qualifying row's saved `updated_at` is used as the
  evidence timestamp; the app cannot recover an earlier overwritten intraday
  achievement. Unknown-provenance Phase 1 counters do not award XP.
- `GET /api/status` adds `progression`: `day`, `level`, `xp`, `xp_to_next_level`,
  `first_recorded_on`, `last_recorded_on`, evidence counts and rule values.
  Legacy numeric counters remain compatible; use observation dates for provenance.
- `GET /api/progression` retains the progression, mission list and history summary
  endpoint, using the same XP rules as `/api/status`. Existing history `delta`
  fields remain available; `computed_day` now follows recorded-day progression.
- `/api/metrics/history` adds `recorded`, `xp`, and `measured`. Each `measured`
  field is `null` when not observed on that row's date (including carried values).
  The dashboard shows a newest-first, horizontally scrollable time series table
  for the latest 30 rows, and labels missing values `—` versus measured `0`.
  TikTok/revenue panels also distinguish unobserved counters from measured zero.
- Migration only adds nullable mission completion columns and an XP column.
  Metric counters, dates and timestamps remain intact. Existing DAY/LEVEL values
  are recalculated as derived snapshots, never used as evidence. No new metric
  rows are created except the existing empty-install placeholder and real saves.
  YouTube OAuth/service behavior is retained; TikTok API remains out of scope.

### Local verification

Back up your SQLite database before upgrading. Use Python 3.11/3.12 and Node 20+.

```bash
cd backend
source .venv/bin/activate
python -m unittest -v test_api test_youtube test_progression
DATABASE_URL=sqlite:////tmp/zero-code-phase4-isolated.db uvicorn app.main:app --host 127.0.0.1 --port 8000
# In another terminal:
cd frontend
npm ci
npm run build
npm run dev
```

In that **isolated** database, check the empty dashboard (DAY/LEVEL/XP 0 and
unobserved values). Save an actual-zero test input: DAY 1, LEVEL 1, XP 10.
Repeat the same-day save: unchanged XP. Enter test revenue 1: MISSION COMPLETE,
XP 110, LEVEL 2, NEXT LEVEL 90. Correct test revenue to 0: the achievement timestamp
and XP remain. Never enter these sample numbers in the real metrics database.
Tests simulate missing dates, level boundaries, migrations, zero/unknown values,
mission completion and duplicate saves; YouTube tests use mocked HTTP and no
real credentials. Live Google OAuth and first sync still require account setup.


## Buffer / X minimal integration

Uses the current [Buffer GraphQL API](https://developers.buffer.com/guides/getting-started.html)
at `https://api.buffer.com` and [custom scheduled posts](https://developers.buffer.com/guides/your-first-post.html).
Set `BUFFER_API_KEY` in ignored `backend/.env`; never put real values in `.env.example`.
Optional `BUFFER_X_CHANNEL_ID` selects an existing Twitter channel. One X channel is
selected automatically; multiple X channels require this setting. Other services are rejected.
No metrics, history, progression, or YouTube records are changed by this integration.

Restart the backend after configuring it. Read-only connectivity check:

```sh
curl --fail http://localhost:8000/api/integrations/buffer/status
```

Validation/channel resolution only (no Buffer writes):

```sh
curl --fail http://localhost:8000/api/integrations/buffer/schedule \
  -H 'Content-Type: application/json' \
  -d '{"text":"ZERO CODE test","scheduled_at":"2099-01-01T12:00:00+09:00","dry_run":true}'
```

Replace the example date with your intended future time, including a timezone.
Only an explicit JSON `"dry_run":false` creates a reservation. The default is true.
Text must fit one tweet (conservative 280 weighted-character limit; URLs counted
in full and emoji sequences conservatively counted). Text is never split into a thread.
Scheduling uses `automatic` + `customScheduled` and UTC `dueAt`, never immediate sharing.
Success returns a post ID; verify the reservation in the Buffer planner.
Errors return fixed safe messages, never upstream response bodies or credentials.
Requests time out after 15 seconds per query. Do not blindly retry a failed write:
Buffer may already have accepted it. Check the planner first; no automatic retry or
local deduplication is provided in this minimal version.
This follows the existing localhost backend trust model; keep it local.

For a later seven-day batch, prepare seven approved texts and future timezone-aware
posting times, select the intended X channel, and add persistent reservation IDs /
idempotency handling before automatic retries or bulk scheduling.

Run checks:

```sh
cd backend
python -m unittest discover -v
cd ../frontend
npm run build
cd ..
git diff --check
```

Implementation verification (2026-10-08): a read-only status probe with the locally
located `backend/.env` returned `Buffer authentication failed`; a valid-key
connection and live reservation are not yet verified. Run the status command
above after configuring the intended new key. No live post was created.
If a real key was ever committed in an example file, revoke it and issue a new
one: removing its value from the current file does not remove Git history.

## ZERO CODE OS Phase 4.5 — remote dashboard + PostgreSQL

Phase 4.5 makes the dashboard deployable and adds a protected read-only endpoint for trusted remote clients such as ChatGPT/agents.

### Production architecture

Recommended low-cost setup:

- **Frontend:** Vercel project with Root Directory `frontend`
- **Backend:** Vercel project with Root Directory `backend`
- **Database:** managed PostgreSQL (Supabase or Neon)
- **Local development/tests:** SQLite remains supported

Set the backend production environment variables:

```env
DATABASE_URL=postgresql://...
METRICS_TIMEZONE=Asia/Tokyo
ZERO_CODE_READ_TOKEN=<long-random-secret>
CORS_ORIGINS=https://<frontend-project>.vercel.app
ALLOWED_HOSTS=<backend-project>.vercel.app,*.vercel.app

YOUTUBE_CLIENT_ID=
YOUTUBE_CLIENT_SECRET=
YOUTUBE_REFRESH_TOKEN=
YOUTUBE_CHANNEL_ID=
YOUTUBE_ANALYTICS_ENABLED=true
YOUTUBE_ANALYTICS_START_DATE=2005-01-01

BUFFER_API_KEY=
BUFFER_X_CHANNEL_ID=
```

Do not commit real values. The backend accepts both `postgres://` and
`postgresql://` URLs and uses the psycopg driver in production.

Set the frontend production variable:

```env
NEXT_PUBLIC_API_URL=https://<backend-project>.vercel.app
```

The backend has a Vercel entrypoint at `backend/api/index.py` and rewrite config
at `backend/vercel.json`.

### Protected remote status

`GET /api/public/status` returns only non-sensitive data needed for remote analysis:

- DAY / LEVEL / XP / XP-to-next-level
- YouTube subscribers/views + observation date
- TikTok followers/views + observation dates
- revenue + observation date
- active/completed mission and progress
- latest deltas
- last database update time

Authentication:

```bash
curl https://<backend-project>.vercel.app/api/public/status \
  -H "Authorization: Bearer $ZERO_CODE_READ_TOKEN"
```

Missing/invalid tokens return `401`; if the server has no read token configured,
the endpoint is closed with `503`. API keys, OAuth credentials and internal
integration secrets are never included in the response.

### PostgreSQL migration path

Before moving production data, back up `backend/zero_code.db`. Create the managed
PostgreSQL database first and set its `DATABASE_URL` only in the production
environment. The application creates the current schema on first startup and its
additive migration logic supports both SQLite and PostgreSQL.

For the first hosted cutover, keep the local SQLite file as the source of truth
until the PostgreSQL instance and HTTPS dashboard are verified. Copy existing
records only once, then switch production writes to PostgreSQL. Do not create
synthetic missing days or backfill unknown observations. A dedicated one-time data
copy utility can be used for the cutover if existing local history must be retained.

### Deployment checklist

1. Create Supabase/Neon PostgreSQL and copy its connection string into the backend Vercel project.
2. Create the backend Vercel project from this repo with Root Directory `backend`.
3. Add backend environment variables above and deploy.
4. Verify `/health`.
5. Verify `/api/public/status` returns 401 without a token and data with the Bearer token.
6. Create the frontend Vercel project with Root Directory `frontend`.
7. Set `NEXT_PUBLIC_API_URL` to the backend URL and deploy.
8. Set backend `CORS_ORIGINS` to the exact frontend HTTPS origin and redeploy.
9. Open the frontend URL on iPhone and verify metrics/history/mission views.
10. If YouTube OAuth must be reauthorized for the hosted environment, update the Google Cloud OAuth configuration before the first production sync.

### Validation

```bash
cd backend
python -m unittest discover -v
cd ../frontend
npm run build
cd ..
git diff --check
```

The remote endpoint tests verify Bearer authentication and ensure common secret
names/token values do not appear in the response.
