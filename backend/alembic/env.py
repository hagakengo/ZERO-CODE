"""Offline-only migration scaffold; no production connection."""
from alembic import context
from app.main import Base

target_metadata = Base.metadata

def run_migrations_offline():
    url = context.get_x_argument(as_dictionary=True).get("db_url", "sqlite:///:memory:")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    raise RuntimeError("Online migrations disabled pending reviewed schema baseline and approval")

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
