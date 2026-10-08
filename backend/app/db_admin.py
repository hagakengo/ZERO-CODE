"""Explicit schema/seed commands. Never invoked by application startup.

Legacy additive setup for local databases; PR #4 Alembic remains the reviewed
migration path for fresh isolated databases. Production changes require approval.
"""
import argparse
import os


def initialize_schema() -> None:
    from .main import Base, engine
    Base.metadata.create_all(engine)
    migrate()


def migrate() -> None:
    """Additive migration for existing SQLite/PostgreSQL databases."""
    from sqlalchemy import inspect, text
    from .main import IS_SQLITE, engine
    timestamp_type = "DATETIME" if IS_SQLITE else "TIMESTAMP"
    additions = {
        "missions": {"metric_type": "VARCHAR(32) NOT NULL DEFAULT 'revenue'",
                     "target_value": "INTEGER NOT NULL DEFAULT 1",
                     "completed_at": timestamp_type, "completed_recorded_on": "DATE"},
        "daily_metrics": {name: "DATE" for name in (
            "tiktok_followers_observed_on", "tiktok_views_observed_on",
            "total_revenue_yen_observed_on", "youtube_observed_on",
            "youtube_analytics_observed_on", "youtube_analytics_start_on", "youtube_analytics_end_on")},
    }
    additions["daily_metrics"]["xp"] = "INTEGER NOT NULL DEFAULT 0"
    with engine.begin() as connection:
        for table, columns in additions.items():
            existing = {c["name"] for c in inspect(connection).get_columns(table)}
            for name, definition in columns.items():
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))



def main() -> None:
    parser = argparse.ArgumentParser(description="Explicit ZERO CODE database administration")
    parser.add_argument("command", choices=("migrate", "seed", "check", "ready"))
    args = parser.parse_args()
    # Check before importing main/load_dotenv: never infer an operator database.
    if not os.environ.get("DATABASE_URL", "").strip():
        parser.error("Set DATABASE_URL explicitly; no default database is allowed.")
    from .main import seed_data, validate_schema, validate_readiness
    if args.command == "migrate":
        initialize_schema()
    elif args.command == "ready":
        try:
            validate_readiness()
        except Exception:
            parser.exit(1, "Database is not ready.\n")
    else:
        validate_schema()
        if args.command == "seed":
            seed_data()


if __name__ == "__main__":
    main()
