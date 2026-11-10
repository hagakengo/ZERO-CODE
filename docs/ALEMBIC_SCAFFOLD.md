# Alembic offline scaffold

This branch only introduces offline scaffolding. Online migrations are explicitly blocked in `backend/alembic/env.py`.

The no-op revision `20261008_0001` represents a potential baseline for **existing** Supabase tables; it does not create tables and is **not** approved for production stamping.

## Offline smoke check

In an isolated development environment with Alembic installed:

```sh
cd backend
python -m alembic -c alembic.ini upgrade head --sql
```

This generates SQL without connecting to a database. Do not use `alembic stamp` or `alembic upgrade` against Supabase.

## Before online activation
1. Extract models to an import-safe module and review changes.
2. Check schema parity including lengths, nullability, indexes, constraints, defaults.
3. Test with a disposable PostgreSQL database.
4. Review backup/rollback and obtain explicit approval for any production stamp or migration.
