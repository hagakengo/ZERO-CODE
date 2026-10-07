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
