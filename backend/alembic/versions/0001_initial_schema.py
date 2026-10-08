"""Initial ZERO CODE OS schema (fresh databases only).

Existing Supabase tables were created separately. Do not upgrade them with this
revision. Review schema parity and backup/recovery, then explicitly stamp after
approval; stamping changes alembic_version and is a production DB write.
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "missions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("metric_type", sa.String(32), nullable=False, server_default="revenue"),
        sa.Column("target_value", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("completed_recorded_on", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("code", name="uq_missions_code"),
    )
    op.create_index("ix_missions_code", "missions", ["code"])

    op.create_table(
        "daily_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("date", sa.Date(), nullable=False, unique=True),
        sa.Column("youtube_subscribers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("youtube_views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("youtube_watch_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("youtube_likes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("youtube_comments", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tiktok_followers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tiktok_views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_revenue_yen", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tiktok_followers_observed_on", sa.Date(), nullable=True),
        sa.Column("tiktok_views_observed_on", sa.Date(), nullable=True),
        sa.Column("total_revenue_yen_observed_on", sa.Date(), nullable=True),
        sa.Column("youtube_observed_on", sa.Date(), nullable=True),
        sa.Column("youtube_analytics_observed_on", sa.Date(), nullable=True),
        sa.Column("youtube_analytics_start_on", sa.Date(), nullable=True),
        sa.Column("youtube_analytics_end_on", sa.Date(), nullable=True),
        sa.Column("xp", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("day", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "youtube_integration",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("state", sa.String(32), nullable=False, server_default="disconnected"),
        sa.Column("error", sa.String(255), nullable=True),
        sa.Column("warning", sa.String(255), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    raise RuntimeError("Destructive downgrade is intentionally disabled. Restore from a reviewed backup.")
