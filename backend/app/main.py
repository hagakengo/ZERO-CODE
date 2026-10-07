import os
from datetime import date, datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pathlib import Path

from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Date, DateTime, Integer, String, create_engine, select, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{Path(__file__).resolve().parent.parent / 'zero_code.db'}")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


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
    day: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


def metrics_today() -> date:
    return datetime.now(ZoneInfo(os.getenv("METRICS_TIMEZONE", "Asia/Tokyo"))).date()


def migrate() -> None:
    """Additive SQLite migration: retain Phase 1 rows and unknown provenance."""
    additions = {
        "missions": {"metric_type": "VARCHAR(32) NOT NULL DEFAULT 'revenue'",
                     "target_value": "INTEGER NOT NULL DEFAULT 1"},
        "daily_metrics": {name: "DATE" for name in (
            "tiktok_followers_observed_on", "tiktok_views_observed_on",
            "total_revenue_yen_observed_on", "youtube_observed_on")},
    }
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
        if not db.scalar(select(Mission).where(Mission.code == "MISSION 01")):
            db.add(Mission(code="MISSION 01", title="最初の1円を生み出せ。", status="active", progress=0))
        if not db.scalar(select(DailyMetrics.id).limit(1)):
            db.add(DailyMetrics(date=metrics_today()))
        db.commit()


def get_db():
    with SessionLocal() as db:
        yield db


seed()
app = FastAPI(title="ZERO CODE OS", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","), allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok"}


METRIC_FIELDS = (
    "youtube_subscribers", "youtube_views", "youtube_watch_minutes", "youtube_likes",
    "youtube_comments", "tiktok_followers", "tiktok_views", "total_revenue_yen",
)
OBSERVATION_FIELDS = ("youtube_observed_on", "tiktok_followers_observed_on",
                      "tiktok_views_observed_on", "total_revenue_yen_observed_on")
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


def mission_state(mission: Mission, metrics: DailyMetrics):
    fields = {"revenue": "total_revenue_yen", "followers": "tiktok_followers",
              "views": "tiktok_views", **{name: name for name in METRIC_FIELDS}}
    field = fields.get(mission.metric_type)
    current = getattr(metrics, field) if field else None
    progress = (min(max(current, 0) / mission.target_value, 1) * 100
                if current is not None and mission.target_value > 0 else None)
    status = mission.status if mission.status == "locked" or progress is None else (
        "completed" if progress >= 100 else "active")
    return {"code": mission.code, "title": mission.title, "status": status,
            "metric_type": mission.metric_type, "target_value": mission.target_value,
            "current_value": current, "progress": progress}


def serialize_metrics(row: DailyMetrics):
    return {"date": row.date, **{key: getattr(row, key) for key in METRIC_FIELDS},
            "day": row.day, "level": row.level, "created_at": row.created_at,
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
    return {
        "date": metrics.date, "today": metrics_today(),
        "timezone": os.getenv("METRICS_TIMEZONE", "Asia/Tokyo"),
        "observed_on": serialize_metrics(metrics)["observed_on"],
        "day": metrics.day, "level": metrics.level,
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


@app.get("/api/metrics/latest")
def latest(db: Session = Depends(get_db)):
    return serialize_metrics(latest_metrics(db))


@app.get("/api/metrics/history")
def history(limit: int = Query(30, ge=1, le=366), db: Session = Depends(get_db)):
    return [serialize_metrics(row) for row in db.scalars(
        select(DailyMetrics).order_by(DailyMetrics.date.desc()).limit(limit))]


@app.post("/api/metrics/manual")
@app.patch("/api/metrics/manual")
def update_manual(payload: ManualUpdate, db: Session = Depends(get_db)):
    # Serialize SQLite writers before reading, so simultaneous rollover updates
    # cannot create duplicate dates or overwrite each other's omitted fields.
    db.execute(text("BEGIN IMMEDIATE"))
    today = metrics_today()
    row = db.scalar(select(DailyMetrics).where(DailyMetrics.date == today))
    if row is None:
        previous = db.scalar(select(DailyMetrics).where(DailyMetrics.date < today)
                             .order_by(DailyMetrics.date.desc()).limit(1))
        carried = {key: getattr(previous, key) for key in
                   (*METRIC_FIELDS, *OBSERVATION_FIELDS, "day", "level")} if previous else {}
        row = DailyMetrics(date=today, **carried)
        db.add(row)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
        setattr(row, f"{field}_observed_on", today)
    row.updated_at = datetime.now(timezone.utc)
    db.commit()
    return system_status(db)


@app.get("/api/missions")
def missions(db: Session = Depends(get_db)):
    metrics = latest_metrics(db)
    return [mission_state(row, metrics) for row in db.scalars(select(Mission).order_by(Mission.id))]
