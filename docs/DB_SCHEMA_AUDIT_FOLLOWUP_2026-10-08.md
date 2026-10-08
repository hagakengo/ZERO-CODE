# Supabase schema audit follow-up — 2026-10-08

This is a read-only verification of the existing `public` schema in project `vqzrundafhfgpgsvpzwj`. No DDL or DML was executed.

## Findings
- `to_regclass('public.alembic_version')` returned `NULL`: there is no existing Alembic version table in `public`.
- `missions`: `missions_pkey` (PRIMARY KEY), `missions_code_key` (UNIQUE), and separate `ix_missions_code` index exist.
- `daily_metrics`: `daily_metrics_pkey` (PRIMARY KEY), `daily_metrics_date_key` (UNIQUE) exist.
- `youtube_integration`: `youtube_integration_pkey` (PRIMARY KEY) exists.
- PostgreSQL also reported system-generated NOT NULL checks. Their names must not be used as portable migration identifiers.

## Migration implications
- The absence of `alembic_version` means **do not run `alembic upgrade head` on the existing database** before a reviewed baseline strategy.
- Database-side defaults differ from ORM Python-side defaults. Do not assume autogenerate output is safe to apply.
- `missions.code` has both a unique constraint and an independent nonunique index. Preserve both until a deliberate index review.
- Next implementation work should happen in a **separate draft PR**, against disposable SQLite/Postgres test databases only.
- Production baseline stamping or schema modifications require explicit human approval, backups, and a rollback plan.

## Verification still required
- Detailed nullability and varchar length parity.
- Test migration environment without importing application startup seed side effects.
- CI check that Alembic can render offline SQL without production credentials.
