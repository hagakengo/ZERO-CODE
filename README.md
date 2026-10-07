# ZERO CODE

AI Agent Studio / Original Cinematic IP Production Repository.

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

## ZERO CODE OS Phase 4 — History & Progression Engine

Dashboard now reads `/api/metrics/history?limit=30` and `/api/progression` on load
and after a successful manual save or YouTube sync. HISTORY displays the latest
30 recorded dates, all five primary cumulative counters, observation dates and
previous-calendar-day deltas. Unknown provenance shows **未取得**, measured zero
shows **0**, and carried values retain their last observation date. Deltas remain
null unless both consecutive calendar dates contain an observation for that field.
No missing-day rows or fabricated measurements are inserted.

### DAY and migration

- First successful manual measurement (including zero) or YouTube sync starts DAY 1.
  DAY advances by calendar dates in `METRICS_TIMEZONE`, even without new records.
  Until a start exists, DAY is 0. Dates before the start also return DAY 0.
- The additive `progression_settings` table stores one start date. On upgrade,
  `PROGRESSION_START_DATE=YYYY-MM-DD`, if provided, takes priority; otherwise the
  earliest positive legacy DAY restores `start = record date - (DAY - 1)`, then
  the earliest known observation is used. Initial seed rows alone do not start DAY.
- `PROGRESSION_START_DATE` is a first-initialization setting, not a recurring override.
  For an existing installation, deliberately edit `progression_settings.start_on`
  with the backend stopped to change the operational start date.
- Stored `daily_metrics.day` and `.level` are preserved for compatibility.
  `/api/status` returns today's computed DAY and effective LEVEL;
  history/latest keep legacy snapshots and add `computed_day` for each record date.
  Read `/api/progression.metrics_date` to distinguish latest evidence from today's DAY.

### LEVEL v0.4 rules

`backend/app/main.py:LEVEL_RULES` is the explicit, replaceable declarative rule list.
Each rule has a level and a map of metric thresholds; **all** its conditions must
be met by observed counters. Initial rules are:

- LEVEL 0: no qualifying rule.
- LEVEL 1: observed total revenue ≥ ¥1.
- LEVEL 2: observed total revenue ≥ ¥100, TikTok followers ≥ 100,
  and YouTube lifetime views ≥ 1,000 (all three required).

These are configurable prototype thresholds, not claims of achieved milestones.
No API measurement is created by progression. Unknown-provenance legacy counters
cannot satisfy a rule. Carried observations are accepted as last-known evidence;
HISTORY exposes their dates. Corrections can lower the calculated level.
Effective LEVEL is `max(legacy stored level, calculated level)` to retain prior
progression. The API exposes both components rather than implying the legacy level
was verified. New cumulative metrics can be used by replacing/adding requirements;
YouTube Analytics fields retain their distinct period definitions.

### Missions and API

Only explicitly seeded/stored `missions` rows are shown; startup continues to seed
**MISSION 01 only**, without inventing new missions. To add a mission, explicitly
insert its unique code, title, metric_type, positive target_value and status into
SQLite with the app stopped, or edit the seed configuration in source. No mission
creation or unlocking API is introduced. Locked stays locked; other mission progress
and completed/active state follow the existing Phase 2 rules, including downward
corrections. Unknown YouTube measurements/invalid targets show unavailable progress.

`GET /api/progression` returns `day`, `start_on`, `as_of`, `level`,
`calculated_level`, `legacy_level`, `rules_version`, `level_rules`, `metrics_date`,
`current_mission` (first active mission or null), all `missions`, and
`history_summary` (record count and first/last saved dates). `achievements` is an
explicit disabled placeholder with an empty items array; no awards are generated.
The PROGRESSION section renders all active/completed/locked missions in the existing
black/charcoal and cyan HUD style.

### Phase 4 verification and remaining work

```bash
cd backend
python -m unittest discover -v
cd ../frontend
npm ci
npm run build
```

New isolated tests cover Tokyo midnight, calendar gaps, explicit/future start dates,
legacy Phase 3 migration and repeat startup, measured-zero initialization, rule
thresholds and correction, unknown provenance, mission states and disabled achievements.
Phase 2 manual-input and Phase 3 mocked OAuth/sync regressions remain in the suite.
Actual OAuth consent and first live sync still require owner configuration. Additional
missions and revised thresholds require explicit configuration. Achievements, TikTok
API, automatic posting and periodic synchronization remain unimplemented.
