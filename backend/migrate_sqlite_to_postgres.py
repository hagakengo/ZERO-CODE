"""Explicit SQLite -> PostgreSQL copy; never creates schema or rebuilds data.

Prepare a NEW target using an approved Alembic upgrade (PR #4), or db_admin
migrate for disposable local databases, before running this utility. Production
migration/copy needs separate approval. All application target tables must be empty.
"""
import os
from pathlib import Path

from sqlalchemy import MetaData, create_engine, func, inspect, select, text

TABLES = ("missions", "daily_metrics", "youtube_integration")


def copy_data(source_engine, target_engine):
    """Copy saved values atomically. Caller explicitly prepares target schema."""
    from app.main import Base
    source_meta, target_meta = MetaData(), MetaData()
    source_meta.reflect(bind=source_engine, only=list(TABLES))
    # No app import side effects or DDL: verify prepared target before copying.
    with source_engine.connect() as source, target_engine.begin() as target:
        inspector = inspect(target)
        for table in Base.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                raise RuntimeError("Target schema is not ready; run an approved migration first.")
            if not set(table.columns.keys()) <= {c['name'] for c in inspector.get_columns(table.name)}:
                raise RuntimeError("Target schema is outdated; run an approved migration first.")
        target_meta.reflect(bind=target, only=list(TABLES))
        if target.dialect.name == "postgresql":
            # Serialize concurrent copies and ordinary writers; lock tables too.
            target.execute(text("SELECT pg_advisory_xact_lock(9001001)"))
            target.execute(text("LOCK TABLE missions, daily_metrics, youtube_integration IN ACCESS EXCLUSIVE MODE"))
        for name in TABLES:
            if target.scalar(select(func.count()).select_from(target_meta.tables[name])):
                raise RuntimeError("Target database is not empty; refusing to overwrite it.")
        for name in TABLES:
            source_table, target_table = source_meta.tables[name], target_meta.tables[name]
            if not set(source_table.columns.keys()) <= set(target_table.columns.keys()):
                raise RuntimeError("Target schema cannot preserve source columns.")
            rows = [dict(row._mapping) for row in source.execute(select(source_table))]
            if rows:
                target.execute(target_table.insert(), rows)
        # PostgreSQL setval is not transactional; perform it only after all inserts.
        # A failed sequence operation still requires operator review before retry.
        if target.dialect.name == "postgresql":
            for name in TABLES:
                target.execute(text(
                    "SELECT setval(pg_get_serial_sequence(:table_name, 'id'), "
                    "COALESCE((SELECT MAX(id) FROM " + name + "), 1), "
                    "(SELECT COUNT(*) > 0 FROM " + name + "))"
                ), {"table_name": name})


def main():
    source_path = Path(os.getenv("SQLITE_SOURCE_PATH", Path(__file__).with_name("zero_code.db"))).resolve()
    target_url = os.getenv("DATABASE_URL", "").strip()
    if not target_url.startswith(("postgres://", "postgresql://", "postgresql+psycopg://")):
        raise SystemExit("Set DATABASE_URL explicitly to the target PostgreSQL database.")
    if not source_path.is_file():
        raise SystemExit("SQLite source file is missing.")
    from app.main import engine
    source_engine = create_engine(f"sqlite:///{source_path}")
    try:
        copy_data(source_engine, engine)
    finally:
        source_engine.dispose()
    print("Copy complete. Saved values preserved; no seed or progression rebuild performed.")


if __name__ == "__main__":
    main()
