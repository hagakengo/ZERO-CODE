# Supabase schema audit — 2026-10-08

## Scope
Read-only `list_tables` inspection of Supabase project `vqzrundafhfgpgsvpzwj`, schema `public`. No SQL mutations, migrations, stamps, or application deploys were performed.

## Observed tables
| Table | Rows reported | RLS | Primary key | Columns |
| --- | ---: | --- | --- | ---: |
| `missions` | 0 | enabled | `id` | 10 |
| `daily_metrics` | 0 | enabled | `id` | 24 |
| `youtube_integration` | 0 | enabled | `id` | 5 |

## Model comparison
- `backend/app/main.py` declares these same three table names.
- Compared against model declarations, the observed column names and broad SQL types appear consistent.
- Supabase has database-side defaults (including sequences and timestamps); SQLAlchemy often specifies Python-side defaults. These are not identical behaviors and must be considered during Alembic autogeneration.
- `missions.code` and `daily_metrics.date` are reported unique.
- This inspection does **not** establish parity for index names, all constraints, nullability, or migration history. Do not stamp or upgrade production yet.

## Safe next steps
1. Read-only inspect `pg_indexes` and information-schema constraints, plus `alembic_version` existence.
2. Verify precise schema parity and document intentional default differences.
3. Add Alembic to a separate feature branch and run migrations only against disposable local databases.
4. Require explicit approval and recovery plan before any production baseline stamp or migration.

## Risks and restrictions
- Production Vercel database connectivity and authenticated write-route protection are not yet verified.
- Never use application startup `create_all` as a substitute for reviewed migrations in production.
- Keep credentials out of source, logs, and audit reports.
