# Alembic adoption plan (no production mutations)

## Existing state
- SQLAlchemy models currently live in `backend/app/main.py`.
- The application currently runs `Base.metadata.create_all()` and a custom additive `migrate()`.
- Supabase already contains the `missions`, `daily_metrics`, and `youtube_integration` tables.
- Never run a generated initial CREATE TABLE migration against these existing tables.

## Safe rollout
1. Move ORM Base/models into `backend/app/models.py` without changing behavior.
2. Add Alembic and configure `target_metadata = Base.metadata` with secrets read only from the environment.
3. Verify that the SQLAlchemy metadata matches the existing Supabase schema using a read-only comparison.
4. Create a baseline revision representing the existing schema; do not apply destructive changes.
5. Only after schema parity is confirmed, `alembic stamp <baseline>` on the existing database, with approval.
6. Remove production startup DDL (`create_all` and custom `migrate`) once Alembic is validated.
7. Require reviewed migration scripts, a backup, and explicit approval before `alembic upgrade head` on production.

## CI/CD
- PR: run isolated SQLite tests and Alembic static checks; never connect to production DB.
- Production: run approved migrations as a separate controlled operation before releasing incompatible application changes.
- Do not print DATABASE_URL, tokens, credentials, or migration environment variables in logs.
