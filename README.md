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
path (see `backend/.env.example`); `.env` is not loaded automatically.

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
- YouTube stays unconnected. Existing/zero counters are preserved and labeled;
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
Automatic integrations, historical backfill editing, history charts and DAY/LEVEL
progression rules remain future work.

If default ports are occupied, set `NEXT_PUBLIC_API_URL` before building/starting
the frontend and `CORS_ORIGINS` (comma-separated frontend origins) before starting
the backend. Defaults allow localhost and 127.0.0.1 on frontend port 3000.
