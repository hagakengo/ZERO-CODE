"""One-time SQLite -> PostgreSQL copy for ZERO CODE OS.

Usage:
  cd backend
  source .venv/bin/activate
  DATABASE_URL='postgresql://...' python migrate_sqlite_to_postgres.py

The target database must be empty. The script creates the current schema without
seeding, copies existing rows verbatim, fixes PostgreSQL identity sequences, then
runs the normal seed/progression refresh.
"""
import os
from pathlib import Path

from sqlalchemy import MetaData, Table, create_engine, func, select, text

source_path = Path(os.getenv("SQLITE_SOURCE_PATH", Path(__file__).with_name("zero_code.db"))).resolve()
target_url = os.getenv("DATABASE_URL", "").strip()

if not source_path.exists():
    raise SystemExit(f"SQLite source not found: {source_path}")
if not target_url or target_url.startswith("sqlite:"):
    raise SystemExit("DATABASE_URL must point to the target PostgreSQL database.")

os.environ["ZERO_CODE_SKIP_SEED"] = "1"

from app.main import engine as target_engine, seed  # noqa: E402

source_engine = create_engine(f"sqlite:///{source_path}", connect_args={"check_same_thread": False})
tables = ("missions", "daily_metrics", "youtube_integration")

source_meta = MetaData()
target_meta = MetaData()
source_meta.reflect(bind=source_engine, only=list(tables))
target_meta.reflect(bind=target_engine, only=list(tables))

with target_engine.begin() as target_conn:
    occupied = {
        name: target_conn.scalar(select(func.count()).select_from(target_meta.tables[name]))
        for name in tables
    }
    nonempty = {name: count for name, count in occupied.items() if count}
    if nonempty:
        raise SystemExit(
            "Target PostgreSQL is not empty; refusing to overwrite it. "
            f"Rows found: {nonempty}"
        )

with source_engine.connect() as source_conn, target_engine.begin() as target_conn:
    for name in tables:
        source_table = source_meta.tables[name]
        target_table = target_meta.tables[name]
        source_columns = {column.name for column in source_table.columns}
        target_columns = {column.name for column in target_table.columns}
        missing = source_columns - target_columns
        if missing:
            raise SystemExit(f"Target table {name} is missing columns: {sorted(missing)}")

        rows = [dict(row._mapping) for row in source_conn.execute(select(source_table))]
        if rows:
            target_conn.execute(target_table.insert(), rows)

        if "id" in target_columns:
            target_conn.execute(text(
                "SELECT setval(pg_get_serial_sequence(:table_name, 'id'), "
                "COALESCE((SELECT MAX(id) FROM " + name + "), 1), "
                "(SELECT COUNT(*) > 0 FROM " + name + "))"
            ), {"table_name": name})

seed()
print("Migration complete. PostgreSQL now contains the copied ZERO CODE OS data.")
