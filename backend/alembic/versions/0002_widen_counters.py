"""Preserve the public safe-integer range on PostgreSQL.

SQLite INTEGER already stores signed 64-bit integers: leave its tables intact.
Existing installations must explicitly apply this revision before large writes;
application startup and legacy additive setup never widen existing columns.
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_widen_counters"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None

COLUMNS = {
    "daily_metrics": (
        "youtube_subscribers", "youtube_views", "youtube_watch_minutes",
        "youtube_likes", "youtube_comments", "tiktok_followers", "tiktok_views",
        "total_revenue_yen",
    ),
    "missions": ("target_value",),
}


def upgrade() -> None:
    dialect = op.get_context().dialect.name
    if dialect == "sqlite":
        return
    if dialect != "postgresql":
        raise RuntimeError("Counter widening supports only PostgreSQL and SQLite.")
    for table, columns in COLUMNS.items():
        for column in columns:
            op.alter_column(table, column, existing_type=sa.Integer(),
                            type_=sa.BigInteger(), existing_nullable=False)


def downgrade() -> None:
    # A narrowing cast can overflow or discard previously accepted data.
    raise RuntimeError("Counter narrowing is disabled. Restore from a reviewed backup.")
