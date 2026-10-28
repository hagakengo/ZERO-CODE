import os
import re
import secrets
from datetime import date, datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator
from pathlib import Path

from fastapi import Depends, FastAPI, Query, HTTPException, Request, Header
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv
from . import youtube, buffer, sns_ops
from threading import Lock

load_dotenv(youtube.ENV_PATH)
sync_lock = Lock()
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Date, DateTime, Integer, String, create_engine, select, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{Path(__file__).resolve().parent.parent / 'zero_code.db'}")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL.removeprefix("postgres://")
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL.removeprefix("postgresql://")
IS_SQLITE = DATABASE_URL.startswith("sqlite:")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if IS_SQLITE else {},
    pool_pre_ping=not IS_SQLITE,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def begin_write(db: Session) -> None:
    """Serialize write paths on both SQLite and PostgreSQL."""
    if IS_SQLITE:
        db.execute(text("BEGIN IMMEDIATE"))
    else:
        # One app-wide transaction lock avoids duplicate same-day rows and
        # conflicting integration writes without exposing a separate lock table.
        db.execute(text("SELECT pg_advisory_xact_lock(9001001)"))


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


class SocialPost(Base):
    __tablename__ = "social_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[str] = mapped_column(String(96), unique=True, index=True)
    platform: Mapped[str] = mapped_column(String(24), default="x")
    note_title: Mapped[str] = mapped_column(String(500))
    note_url: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    post_text: Mapped[str] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(24), default="DRAFT", index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    buffer_post_id: Mapped[str | None] = mapped_column(String(128), nullable=True, unique=True)
    x_public_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class SocialPostAttempt(Base):
    __tablename__ = "social_post_attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    post_id: Mapped[str] = mapped_column(String(96), index=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    outcome: Mapped[str] = mapped_column(String(32))
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    buffer_post_id: Mapped[str | None] = mapped_column(String(128), nullable=True)


def metrics_today() -> date:
    return datetime.now(ZoneInfo(os.getenv("METRICS_TIMEZONE", "Asia/Tokyo"))).date()


def migrate() -> None:
    """Additive migration for existing SQLite/PostgreSQL databases."""
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


def seed() -> None:
    Base.metadata.create_all(engine)
    migrate()
    with SessionLocal() as db:
        begin_write(db)
        if not db.scalar(select(Mission).where(Mission.code == "MISSION 01")):
            db.add(Mission(code="MISSION 01", title="最初の1円を生み出せ。", status="active", progress=0))
        if not db.scalar(select(DailyMetrics.id).limit(1)):
            db.add(DailyMetrics(date=metrics_today()))
        db.flush()
        refresh_progression(db)
        db.commit()


def get_db():
    with SessionLocal() as db:
        yield db


app = FastAPI(title="ZERO CODE OS", version="0.4.5")
app.include_router(buffer.router)
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","), allow_methods=["*"], allow_headers=["*"])


app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[host.strip() for host in os.getenv(
        "ALLOWED_HOSTS", "localhost,127.0.0.1,testserver,*.vercel.app"
    ).split(",") if host.strip()],
)


@app.get("/health")
def health():
    return {"status": "ok"}


METRIC_FIELDS = (
    "youtube_subscribers", "youtube_views", "youtube_watch_minutes", "youtube_likes",
    "youtube_comments", "tiktok_followers", "tiktok_views", "total_revenue_yen",
)
OBSERVATION_FIELDS = ("youtube_observed_on", "tiktok_followers_observed_on",
                      "tiktok_views_observed_on", "total_revenue_yen_observed_on",
                      "youtube_analytics_observed_on")
ANALYTICS_DATES = ("youtube_analytics_start_on", "youtube_analytics_end_on")
Counter = Annotated[int, Field(strict=True, ge=0, le=9007199254740991)]


class ManualUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tiktok_followers: Counter | None = None
    tiktok_views: Counter | None = None
    total_revenue_yen: Counter | None = None

    @model_validator(mode="after")
    def require_values(self):
        if not self.model_fields_set or any(getattr(self, key) is None for key in self.model_fields_set):
            raise ValueError("Supply at least one non-null cumulative counter")
        return self


def latest_metrics(db: Session):
    return db.scalars(select(DailyMetrics).order_by(DailyMetrics.date.desc()).limit(1)).one()


DAILY_RECORD_XP = 10
MISSION_COMPLETION_XP = 100
XP_PER_LEVEL = 100
MISSION_FIELDS = {"revenue": "total_revenue_yen", "followers": "tiktok_followers",
                  "views": "tiktok_views", **{name: name for name in METRIC_FIELDS}}


def metric_observation(field):
    if field in ("youtube_subscribers", "youtube_views"):
        return "youtube_observed_on"
    if field.startswith("youtube_"):
        return "youtube_analytics_observed_on"
    return f"{field}_observed_on"


def mission_state(mission: Mission, metrics: DailyMetrics):
    field = MISSION_FIELDS.get(mission.metric_type)
    current = (getattr(metrics, field) if field and
               getattr(metrics, metric_observation(field)) is not None else None)
    progress = (min(max(current, 0) / mission.target_value, 1) * 100
                if current is not None and mission.target_value > 0 else None)
    completed = mission.completed_at is not None
    return {"code": mission.code, "title": mission.title,
            "status": "completed" if completed else mission.status,
            "completed_at": mission.completed_at,
            "metric_type": mission.metric_type, "target_value": mission.target_value,
            "current_value": current, "progress": 100 if completed else progress}


def recorded(row: DailyMetrics) -> bool:
    return any(getattr(row, key) == row.date for key in OBSERVATION_FIELDS)


def refresh_progression(db: Session) -> None:
    """Rebuild derived snapshots; retain observed counters and timestamps.

    Caller owns the transaction. Historical completions use the earliest saved
    qualifying row timestamp; unknown provenance and carried values do not count.
    """
    db.flush()
    rows = list(db.scalars(select(DailyMetrics).order_by(DailyMetrics.date)))
    all_missions = list(db.scalars(select(Mission).order_by(Mission.id)))
    for mission in all_missions:
        if mission.completed_at is not None or mission.status == "locked":
            continue
        field = MISSION_FIELDS.get(mission.metric_type)
        if field is None:
            continue
        for row in rows:
            if (mission_state(mission, row)["progress"] == 100 and
                    getattr(row, metric_observation(field)) == row.date):
                mission.status = "completed"
                mission.completed_at = row.updated_at
                mission.completed_recorded_on = row.date
                break
    day = 0
    for row in rows:
        day += int(recorded(row))
        row.day = day
        row.xp = day * DAILY_RECORD_XP + sum(
            MISSION_COMPLETION_XP for m in all_missions
            if m.completed_at is not None and m.completed_recorded_on is not None
            and m.completed_recorded_on <= row.date)
        row.level = 1 + row.xp // XP_PER_LEVEL if day else 0


def progression(db: Session):
    rows = list(db.scalars(select(DailyMetrics).order_by(DailyMetrics.date)))
    dates = [r.date for r in rows if recorded(r)]
    completed_count = sum(1 for m in db.scalars(select(Mission))
                          if m.completed_at is not None and m.completed_recorded_on is not None)
    xp = len(dates) * DAILY_RECORD_XP + completed_count * MISSION_COMPLETION_XP
    return {"day": len(dates), "level": 1 + xp // XP_PER_LEVEL if dates else 0,
            "xp": xp, "xp_to_next_level": XP_PER_LEVEL - xp % XP_PER_LEVEL,
            "first_recorded_on": dates[0] if dates else None,
            "last_recorded_on": dates[-1] if dates else None,
            "recorded_days": len(dates), "completed_missions": completed_count,
            "rules": {"daily_record_xp": DAILY_RECORD_XP,
                      "mission_completion_xp": MISSION_COMPLETION_XP, "xp_per_level": XP_PER_LEVEL}}


if os.getenv("ZERO_CODE_SKIP_SEED") == "1":
    Base.metadata.create_all(engine)
    migrate()
else:
    seed()


def serialize_metrics(row: DailyMetrics):
    return {"date": row.date, **{key: getattr(row, key) for key in METRIC_FIELDS},
            **{key: getattr(row, key) for key in ANALYTICS_DATES},
            "day": row.day, "level": row.level, "xp": row.xp,
            "recorded": recorded(row),
            "measured": {key: getattr(row, key) if getattr(row, metric_observation(key)) == row.date else None
                         for key in METRIC_FIELDS},
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "observed_on": {key.removesuffix("_observed_on"): getattr(row, key)
                            for key in OBSERVATION_FIELDS}}


@app.get("/api/status")
def system_status(db: Session = Depends(get_db)):
    metrics = latest_metrics(db)
    previous = db.scalar(select(DailyMetrics).where(DailyMetrics.date == metrics.date - timedelta(days=1)))
    def delta(field, observation):
        if (previous is None or getattr(metrics, observation) != metrics.date
                or getattr(previous, observation) != previous.date):
            return None
        return getattr(metrics, field) - getattr(previous, field)
    mission = db.scalars(select(Mission).where(Mission.code == "MISSION 01")).one()
    progress = progression(db)
    return {
        "progression": progress,
        "date": metrics.date, "today": metrics_today(),
        "timezone": os.getenv("METRICS_TIMEZONE", "Asia/Tokyo"),
        "observed_on": serialize_metrics(metrics)["observed_on"],
        "day": progress["day"], "level": progress["level"],
        "youtube": {"subscribers": metrics.youtube_subscribers, "views": metrics.youtube_views},
        "tiktok": {"followers": metrics.tiktok_followers, "views": metrics.tiktok_views},
        "total_revenue_yen": metrics.total_revenue_yen,
        "delta": {
            "youtube": {"subscribers": delta("youtube_subscribers", "youtube_observed_on"),
                        "views": delta("youtube_views", "youtube_observed_on")},
            "tiktok": {"followers": delta("tiktok_followers", "tiktok_followers_observed_on"),
                       "views": delta("tiktok_views", "tiktok_views_observed_on")},
            "total_revenue_yen": delta("total_revenue_yen", "total_revenue_yen_observed_on"),
        },
        "mission": mission_state(mission, metrics),
    }


def _require_read_token(authorization: str | None) -> None:
    expected = os.getenv("ZERO_CODE_READ_TOKEN", "").strip()
    if not expected:
        raise HTTPException(503, "Remote read access is not configured.")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Unauthorized")
    supplied = authorization.removeprefix("Bearer ").strip()
    if not secrets.compare_digest(supplied, expected):
        raise HTTPException(401, "Unauthorized")


@app.get("/api/public/status")
def public_status(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """Minimal read-only snapshot for trusted remote clients/agents."""
    _require_read_token(authorization)
    current = system_status(db)
    metrics = latest_metrics(db)
    observed = current["observed_on"]
    return {
        "date": current["date"],
        "timezone": current["timezone"],
        "progression": current["progression"],
        "youtube": {
            "subscribers": metrics.youtube_subscribers if observed.get("youtube") else None,
            "views": metrics.youtube_views if observed.get("youtube") else None,
            "observed_on": observed.get("youtube"),
        },
        "tiktok": {
            "followers": metrics.tiktok_followers if observed.get("tiktok_followers") else None,
            "views": metrics.tiktok_views if observed.get("tiktok_views") else None,
            "followers_observed_on": observed.get("tiktok_followers"),
            "views_observed_on": observed.get("tiktok_views"),
        },
        "revenue": {
            "yen": metrics.total_revenue_yen if observed.get("total_revenue_yen") else None,
            "observed_on": observed.get("total_revenue_yen"),
        },
        "mission": current["mission"],
        "delta": current["delta"],
        "last_updated_at": metrics.updated_at,
    }


SNS_STATUSES = {"DRAFT", "READY", "SCHEDULED", "PUBLISHED", "FAILED", "HOLD"}
X_STATUS_URL = re.compile(r"https://x\.com/sora1993xny/status/\d+")


def record_social_attempt(db: Session, row: SocialPost, outcome: str,
                          error: str | None = None, buffer_post_id: str | None = None):
    db.add(SocialPostAttempt(post_id=row.post_id, outcome=outcome, error=error,
                             buffer_post_id=buffer_post_id))


def serialize_social_post(row: SocialPost):
    return {
        "post_id": row.post_id, "platform": row.platform,
        "note_title": row.note_title, "note_url": row.note_url,
        "post_text": row.post_text, "status": row.status,
        "scheduled_at": row.scheduled_at, "buffer_post_id": row.buffer_post_id,
        "x_public_url": row.x_public_url, "published_at": row.published_at,
        "last_checked_at": row.last_checked_at, "error": row.error,
        "retry_count": row.retry_count,
    }


def require_local_origin(request: Request):
    allowed = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if request.headers.get("origin") and request.headers["origin"] not in allowed:
        raise HTTPException(403, "Origin not allowed")


def require_sns_write_token(supplied: str | None):
    expected = os.getenv("SNS_WRITE_TOKEN", "").strip()
    if not expected:
        raise HTTPException(503, "SNS write access is not configured.")
    if not supplied or not secrets.compare_digest(supplied, expected):
        raise HTTPException(401, "Unauthorized")


@app.get("/api/sns/posts")
def social_posts(request: Request, x_zcs_sns_token: str | None = Header(default=None),
                 db: Session = Depends(get_db)):
    require_local_origin(request)
    require_sns_write_token(x_zcs_sns_token)
    return [serialize_social_post(row) for row in
            db.scalars(select(SocialPost).order_by(SocialPost.created_at.desc()))]


class SnsReconcileInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dry_run: StrictBool = True
    automation: StrictBool = False
    now: datetime | None = None


@app.post("/api/sns/reconcile")
def reconcile_social_posts(payload: SnsReconcileInput, request: Request,
                           x_zcs_sns_token: str | None = Header(default=None),
                           db: Session = Depends(get_db)):
    """Detect note entries and, only when explicitly enabled, persist/schedule them."""
    require_local_origin(request)
    require_sns_write_token(x_zcs_sns_token)
    rss_url = os.getenv("NOTE_RSS_URL", "").strip()
    if not rss_url:
        raise HTTPException(409, "note RSS is not configured.")
    try:
        entries = sns_ops.fetch_note_rss(rss_url)
    except sns_ops.FeedError as error:
        raise HTTPException(502, str(error)) from None
    now = (payload.now or datetime.now(timezone.utc)).astimezone(sns_ops.JST)
    automation_enabled = os.getenv("SNS_AUTO_SCHEDULE_ENABLED", "0") == "1"
    dry_run = payload.dry_run or (payload.automation and not automation_enabled)
    if not dry_run:
        begin_write(db)
    occupied = {
        row.scheduled_at.replace(tzinfo=timezone.utc).astimezone(sns_ops.JST)
        if row.scheduled_at and row.scheduled_at.tzinfo is None else row.scheduled_at.astimezone(sns_ops.JST)
        for row in db.scalars(select(SocialPost).where(SocialPost.scheduled_at.is_not(None)))
    }
    actions = []
    for entry in entries:
        existing = db.scalar(select(SocialPost).where(SocialPost.note_url == entry["url"]))
        if existing:
            actions.append({"note_url": entry["url"], "action": "existing",
                            "status": existing.status})
            continue
        safe = sns_ops.normal_announcement(entry["title"], entry["summary"])
        status = "READY" if safe else "HOLD"
        body = sns_ops.draft_text(entry["title"], entry["url"])
        slot = sns_ops.next_slot(now, occupied) if safe else None
        action = {"note_url": entry["url"], "action": "detected", "status": status,
                  "scheduled_at": slot}
        if dry_run:
            actions.append(action)
            if slot:
                occupied.add(slot)
            continue
        post_id = "NOTE-" + entry["url"].rsplit("/", 1)[-1]
        row = SocialPost(post_id=post_id, note_title=entry["title"],
                         note_url=entry["url"], post_text=body, status=status,
                         scheduled_at=slot.astimezone(timezone.utc).replace(tzinfo=None) if slot else None,
                         retry_count=0)
        db.add(row)
        if status == "READY":
            if not buffer.configured():
                row.status, row.error = "HOLD", "Buffer is not configured."
                action.update(status="HOLD", error=row.error)
            else:
                try:
                    result = buffer.schedule_post(body, slot)
                    row.buffer_post_id = result["post_id"]
                    row.status = "SCHEDULED"
                    row.error = None
                    record_social_attempt(db, row, "SCHEDULED", buffer_post_id=row.buffer_post_id)
                    action.update(status="SCHEDULED", buffer_post_id=row.buffer_post_id,
                                  duplicate=result["duplicate"])
                    occupied.add(slot)
                except buffer.BufferError as error:
                    row.status, row.error = "FAILED", str(error)
                    row.retry_count = (row.retry_count or 0) + 1
                    record_social_attempt(db, row, "FAILED", error=str(error))
                    action.update(status="FAILED", error=str(error))
        actions.append(action)
    if not dry_run:
        db.commit()
    return {"dry_run": dry_run, "automation": payload.automation,
            "auto_schedule_enabled": automation_enabled, "actions": actions}


@app.post("/api/sns/refresh")
def refresh_social_posts(request: Request, automation: StrictBool = Query(default=False),
                         x_zcs_sns_token: str | None = Header(default=None),
                         db: Session = Depends(get_db)):
    """Reconcile Buffer state. Sent is not PUBLISHED until an X URL is verified."""
    require_local_origin(request)
    require_sns_write_token(x_zcs_sns_token)
    if automation and os.getenv("SNS_AUTO_REFRESH_ENABLED", "0") != "1":
        return {"skipped": True, "reason": "automatic refresh is disabled", "posts": []}
    if not buffer.configured():
        raise HTTPException(409, "Buffer is not configured.")
    try:
        channel = buffer.resolve_x(buffer.channels())
        by_status = {
            status: {item["id"]: item for item in buffer.posts(channel, (status,))}
            for status in ("scheduled", "sent", "failed")
        }
    except buffer.BufferError as error:
        raise HTTPException(502, str(error)) from None
    begin_write(db)
    changed = []
    now = datetime.now(timezone.utc)
    for row in db.scalars(select(SocialPost).where(SocialPost.buffer_post_id.is_not(None))):
        row.last_checked_at = now
        if row.buffer_post_id in by_status["failed"]:
            row.status, row.error = "FAILED", "Buffer reports delivery failure."
        elif row.buffer_post_id in by_status["sent"] and row.status != "PUBLISHED":
            sent = by_status["sent"][row.buffer_post_id]
            public_url = sent.get("externalLink")
            if isinstance(public_url, str) and X_STATUS_URL.fullmatch(public_url):
                row.status = "PUBLISHED"
                row.x_public_url = public_url
                row.published_at = now
                row.error = None
                record_social_attempt(db, row, "PUBLISHED", buffer_post_id=row.buffer_post_id)
            else:
                row.error = "Buffer sent; verified @sora1993xny X URL is unavailable."
        elif row.buffer_post_id in by_status["scheduled"]:
            row.status, row.error = "SCHEDULED", None
        row.updated_at = now
        changed.append(serialize_social_post(row))
    db.commit()
    return {"posts": changed}


@app.post("/api/sns/posts/{post_id}/retry")
def retry_social_post(post_id: str, request: Request,
                      x_zcs_sns_token: str | None = Header(default=None),
                      db: Session = Depends(get_db)):
    require_local_origin(request)
    require_sns_write_token(x_zcs_sns_token)
    if not buffer.configured():
        raise HTTPException(409, "Buffer is not configured.")
    begin_write(db)
    row = db.scalar(select(SocialPost).where(SocialPost.post_id == post_id))
    if not row:
        raise HTTPException(404, "SNS post not found.")
    if row.status != "FAILED" or not row.scheduled_at:
        raise HTTPException(409, "Only FAILED scheduled posts can be retried.")
    scheduled = row.scheduled_at.replace(tzinfo=timezone.utc)
    try:
        result = buffer.schedule_post(row.post_text, scheduled)
    except buffer.BufferError as error:
        row.retry_count += 1
        row.error = str(error)
        record_social_attempt(db, row, "FAILED", error=str(error))
        db.commit()
        raise HTTPException(502, str(error)) from None
    row.buffer_post_id = result["post_id"]
    row.status, row.error = "SCHEDULED", None
    row.retry_count += 1
    row.updated_at = datetime.now(timezone.utc)
    record_social_attempt(db, row, "SCHEDULED", buffer_post_id=row.buffer_post_id)
    db.commit()
    return {**serialize_social_post(row), "duplicate": result["duplicate"]}


class PublishConfirmation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x_public_url: str
    published_at: datetime


@app.post("/api/sns/posts/{post_id}/confirm-published")
def confirm_social_post(post_id: str, payload: PublishConfirmation, request: Request,
                        x_zcs_sns_token: str | None = Header(default=None),
                        db: Session = Depends(get_db)):
    """Record X evidence; Buffer sent state alone never promotes to PUBLISHED."""
    require_local_origin(request)
    require_sns_write_token(x_zcs_sns_token)
    if not X_STATUS_URL.fullmatch(payload.x_public_url):
        raise HTTPException(422, "A verified @sora1993xny X status URL is required.")
    begin_write(db)
    row = db.scalar(select(SocialPost).where(SocialPost.post_id == post_id))
    if not row:
        raise HTTPException(404, "SNS post not found.")
    row.status = "PUBLISHED"
    row.x_public_url = payload.x_public_url
    row.published_at = payload.published_at
    row.last_checked_at = datetime.now(timezone.utc)
    row.error = None
    row.updated_at = datetime.now(timezone.utc)
    record_social_attempt(db, row, "PUBLISHED", buffer_post_id=row.buffer_post_id)
    db.commit()
    return serialize_social_post(row)


@app.get("/api/metrics/latest")
def latest(db: Session = Depends(get_db)):
    return history(1, db)[0]


@app.get("/api/metrics/history")
def history(limit: int = Query(30, ge=1, le=366), db: Session = Depends(get_db)):
    rows = db.scalars(select(DailyMetrics).order_by(DailyMetrics.date.desc()).limit(limit))
    result = []
    for row in rows:
        previous = db.scalar(select(DailyMetrics).where(DailyMetrics.date == row.date - timedelta(days=1)))
        result.append({**serialize_metrics(row), "computed_day": row.day,
                       "delta": metric_deltas(row, previous)})
    return result


@app.post("/api/metrics/manual")
@app.patch("/api/metrics/manual")
def update_manual(payload: ManualUpdate, db: Session = Depends(get_db)):
    row = writable_today(db)
    today = row.date
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
        setattr(row, f"{field}_observed_on", today)
    row.updated_at = datetime.now(timezone.utc)
    refresh_progression(db)
    db.commit()
    return system_status(db)


@app.get("/api/missions")
def missions(db: Session = Depends(get_db)):
    metrics = latest_metrics(db)
    return [mission_state(row, metrics) for row in db.scalars(select(Mission).order_by(Mission.id))]


def writable_today(db):
    # Serialize writers before reading so simultaneous rollover updates cannot
    # create duplicate dates or overwrite each other's omitted fields.
    begin_write(db)
    today = metrics_today()
    row = db.scalar(select(DailyMetrics).where(DailyMetrics.date == today))
    if row is None:
        previous = db.scalar(select(DailyMetrics).where(DailyMetrics.date < today)
                             .order_by(DailyMetrics.date.desc()).limit(1))
        carried = {key: getattr(previous, key) for key in
                   (*METRIC_FIELDS, *OBSERVATION_FIELDS, *ANALYTICS_DATES, "day", "level")} if previous else {}
        row = DailyMetrics(date=today, **carried)
        db.add(row)
    return row


@app.get("/api/integrations/youtube/status")
def youtube_status(db: Session = Depends(get_db)):
    integration = db.get(YouTubeIntegration, 1)
    configured = youtube.configured()
    return {"state": integration.state if configured and integration else "disconnected",
            "configured": configured,
            "error": integration.error if configured and integration else None,
            "warning": integration.warning if integration else None,
            "last_synced_at": integration.last_synced_at if integration else None,
            "last_observed_on": latest_metrics(db).youtube_observed_on}


@app.post("/api/integrations/youtube/sync")
def sync_youtube(request: Request, db: Session = Depends(get_db)):
    origin = request.headers.get("origin")
    allowed = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if origin and origin not in allowed:
        raise HTTPException(403, "Origin not allowed")
    if not youtube.configured():
        raise HTTPException(409, "YouTube未接続: backend/.envとOAuthを設定してください。")
    if not sync_lock.acquire(blocking=False):
        raise HTTPException(409, "YouTube sync is already running.")
    try:
        try:
            values, warning = youtube.fetch_metrics(metrics_today())
        except youtube.YouTubeError as error:
            begin_write(db)
            integration = db.get(YouTubeIntegration, 1) or YouTubeIntegration(id=1)
            integration.state, integration.error = "error", str(error)
            db.add(integration)
            db.commit()
            raise HTTPException(502, str(error)) from None
        row = writable_today(db)
        for field, value in values.items():
            setattr(row, field, value)
        row.youtube_observed_on = row.date
        row.updated_at = datetime.now(timezone.utc)
        integration = db.get(YouTubeIntegration, 1) or YouTubeIntegration(id=1)
        integration.state, integration.error, integration.warning = "connected", None, warning
        integration.last_synced_at = datetime.now(timezone.utc)
        db.add(integration)
        refresh_progression(db)
        db.commit()
        return {"status": system_status(db), "integration": youtube_status(db)}
    finally:
        sync_lock.release()



def metric_deltas(row, previous):
    return {field: (getattr(row, field) - getattr(previous, field)
                   if previous is not None and
                   getattr(row, metric_observation(field)) == row.date and
                   getattr(previous, metric_observation(field)) == previous.date else None)
            for field in METRIC_FIELDS}


@app.get("/api/progression")
def progression_status(db: Session = Depends(get_db)):
    metrics = latest_metrics(db)
    mission_list = missions(db)
    rows = list(db.scalars(select(DailyMetrics).order_by(DailyMetrics.date)))
    return {**progression(db), "metrics_date": metrics.date,
            "current_mission": next((m for m in mission_list if m["status"] == "active"), None),
            "missions": mission_list,
            "history_summary": {"record_count": len(rows), "first_date": rows[0].date,
                                "last_date": rows[-1].date},
            "achievements": {"enabled": False, "items": []}}
