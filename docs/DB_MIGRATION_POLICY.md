# ZERO CODE OS — DB migration policy

**State: proposal / PR. Not a production migration authorization.**

## Current verified facts (read-only, 2026-10-09)
- Supabase project `vqzrundafhfgpgsvpzwj` has three empty tables:
  `public.missions`, `public.daily_metrics`, `public.youtube_integration`.
- RLS is enabled on all three.
- SQLAlchemy defines the same three models in `backend/app/main.py`.
- Existing tables were created outside Alembic. They have **no Alembic baseline**.
- Models rely on Python-side defaults while Supabase schema also has SQL server defaults.
  Constraints/index naming and defaults require a separate parity review before stamping.

## Migration contract
- `alembic upgrade head` is for **fresh, isolated databases only** until a
  separate approval covers production baseline reconciliation.
- `alembic stamp head` on existing Supabase is a DB write. **Do not run**
  without explicit approval, a confirmed backup/restore procedure and schema
  parity review. Do not apply initial CREATE TABLE revision to existing tables.
- Every Alembic command requires an explicit `DATABASE_URL`. Never copy
  production credentials into GitHub Actions or run CI against production.
- Production schema changes must be reviewed separately from app deployment.
  No automatic migrations on serverless startup.
- App import/startup no longer performs DDL/seed/recalculation. Startup validates
  schema only; /ready and db_admin ready also validate required dashboard data.
- Fresh targets: explicit Alembic upgrade, then either explicit seed OR history
  copy into empty tables. Copy never seeds/rebuilds snapshots. db_admin migrate
  is legacy local setup and does not record Alembic history; never apply a fresh
  baseline to those existing tables without parity review.
- CI exercises a fresh temporary SQLite DB only. It does not prove PostgreSQL
  compatibility or Supabase RLS/permissions behavior.

## Local smoke test (isolated database)
```bash
cd backend
python -m pip install -r requirements-dev.txt
export DATABASE_URL="sqlite:////tmp/zero-code-migration-check.db"
python -m alembic upgrade head
python -m alembic current
```
Use a new, disposable path for each run. No production URLs.
