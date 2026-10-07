from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import DateTime, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = f"sqlite:///{Path(__file__).resolve().parent.parent / 'zero_code.db'}"
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
    progress: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


def seed() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if not db.scalar(select(Mission).where(Mission.code == "MISSION 01")):
            db.add(Mission(code="MISSION 01", title="最初の1円を生み出せ。", status="active", progress=0))
            db.commit()


def get_db():
    with SessionLocal() as db:
        yield db


seed()
app = FastAPI(title="ZERO CODE OS", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/missions")
def missions(db: Session = Depends(get_db)):
    rows = db.scalars(select(Mission).order_by(Mission.id)).all()
    return [{"code": row.code, "title": row.title, "status": row.status, "progress": row.progress} for row in rows]
