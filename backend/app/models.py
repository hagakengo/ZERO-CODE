"""SQLAlchemy model definitions without application initialization."""
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Mission(Base):
    __tablename__ = "missions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="active")
    metric_type: Mapped[str] = mapped_column(String(32), default="revenue")
    target_value: Mapped[int] = mapped_column(Integer, default=1)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_recorded_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class DailyMetrics(Base):
    __tablename__ = "daily_metrics"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    youtube_subscribers: Mapped[int] = mapped_column(Integer, default=0)
    youtube_views: Mapped[int] = mapped_column(Integer, default=0)
    youtube_watch_minutes: Mapped[int] = mapped_column(Integer, default=0)
    youtube_likes: Mapped[int] = mapped_column(Integer, default=0)
    youtube_comments: Mapped[int] = mapped_column(Integer, default=0)
    tiktok_followers: Mapped[int] = mapped_column(Integer, default=0)
    tiktok_views: Mapped[int] = mapped_column(Integer, default=0)
    total_revenue_yen: Mapped[int] = mapped_column(Integer, default=0)
    # Observation dates distinguish initial/carried values from measurements.
    tiktok_followers_observed_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    tiktok_views_observed_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_revenue_yen_observed_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    youtube_observed_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    youtube_analytics_observed_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    youtube_analytics_start_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    youtube_analytics_end_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    day: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class YouTubeIntegration(Base):
    __tablename__ = "youtube_integration"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    state: Mapped[str] = mapped_column(String(32), default="disconnected")
    error: Mapped[str | None] = mapped_column(String(255), nullable=True)
    warning: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
