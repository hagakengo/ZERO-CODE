import os
import secrets
from datetime import date, datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pathlib import Path

from fastapi import Depends, FastAPI, Query, HTTPException, Request, Header
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv
from . import youtube, buffer
from .security import require_write_token
from threading import Lock
from contextlib import asynccontextmanager

load_dotenv(youtube.ENV_PATH)
sync_lock = Lock()
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import BigInteger, Date, DateTime, Integer, String, create_engine, select, inspect, text
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
    target_value: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), default=1)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_recorded_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class DailyMetrics(Base):
    __tablename__ = "daily_metrics"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    youtube_subscribers: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), default=0)
    youtube_views: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), default=0)
    youtube_watch_minutes: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), default=0)
    youtube_likes: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), default=0)
    youtube_comments: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), default=0)
    tiktok_followers: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), default=0)
    tiktok_views: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), default=0)
    total_revenue_yen: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), default=0)
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


def metrics_today() -> date:
    return datetime.now(ZoneInfo(os.getenv("METRICS_TIMEZONE", "Asia/Tokyo"))).date()


def seed() -> None:
    """Explicit compatibility helper for isolated tests/legacy local setup only."""
    from .db_admin import initialize_schema
    initialize_schema()
    seed_data()


def seed_data() -> None:
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


def validate_schema() -> None:
    """Read-only startup validation; never create, migrate or seed here."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    for table in Base.metadata.sorted_tables:
        if table.name not in tables:
            raise RuntimeError("Database schema is not ready; run an approved migration explicitly.")
        columns = {column["name"] for column in inspector.get_columns(table.name)}
        if not set(table.columns.keys()) <= columns:
            raise RuntimeError("Database schema is outdated; run an approved migration explicitly.")


def validate_readiness() -> None:
    """Read-only local dashboard prerequisites; no external integration calls."""
    validate_schema()
    with SessionLocal() as db:
        # Load full models to detect unreadable required columns, not just IDs.
        if db.scalar(select(DailyMetrics).limit(1)) is None:
            raise RuntimeError("Database required data is not ready.")
        if db.scalar(select(Mission).where(Mission.code == "MISSION 01")) is None:
            raise RuntimeError("Database required data is not ready.")
        db.scalars(select(YouTubeIntegration).limit(1)).all()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_schema()
    yield


app = FastAPI(title="ZERO CODE OS", version="0.4.5", lifespan=lifespan)
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


@app.get("/ready")
def readiness():
    from fastapi.responses import JSONResponse
    try:
        validate_readiness()
    except Exception:
        # Never expose SQL, URLs, credentials, table names or driver errors.
        return JSONResponse({"status": "not_ready"}, status_code=503,
                            headers={"Cache-Control": "no-store"})
    return JSONResponse({"status": "ready"}, headers={"Cache-Control": "no-store"})


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
def update_manual(payload: ManualUpdate, _authorized: None = Depends(require_write_token), db: Session = Depends(get_db)):
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
def sync_youtube(request: Request, _authorized: None = Depends(require_write_token), db: Session = Depends(get_db)):
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
