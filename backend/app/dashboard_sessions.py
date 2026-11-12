"""Shared state for the Dashboard login and authorization."""
import hashlib
import os
import re
import secrets
import time

from fastapi import Header, HTTPException
from sqlalchemy import BigInteger, Column, Integer, MetaData, String, Table, delete, select, text
from sqlalchemy.orm import Session

metadata = MetaData()
attempts = Table(
    "dashboard_login_limit", metadata,
    Column("id", Integer, primary_key=True, autoincrement=False),
    Column("reset_at", BigInteger, nullable=False),
    Column("attempts", Integer, nullable=False),
)
sessions = Table(
    "dashboard_sessions", metadata,
    Column("nonce_hash", String(64), primary_key=True),
    Column("expires_at", BigInteger, nullable=False),
)
SESSION_SECONDS = 900
ATTEMPT_WINDOW = 300
ATTEMPT_LIMIT = 5

# One row, shared across all callers. Rejected attempts do not extend the window.
reserve_attempt = text("""
    INSERT INTO dashboard_login_limit (id, reset_at, attempts)
    VALUES (1, :reset, 1)
    ON CONFLICT (id) DO UPDATE
    SET reset_at = CASE WHEN dashboard_login_limit.reset_at <= :now
                        THEN :reset ELSE dashboard_login_limit.reset_at END,
        attempts = CASE WHEN dashboard_login_limit.reset_at <= :now
                        THEN 1 ELSE dashboard_login_limit.attempts + 1 END
    WHERE dashboard_login_limit.reset_at <= :now OR dashboard_login_limit.attempts < :limit
    RETURNING id
""")


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def require_session_service(authorization: list[str] | None = Header(default=None)) -> dict[str, str]:
    key = os.getenv("ZCS_DASHBOARD_SESSION_SERVICE_TOKEN", "").strip()
    verifier = os.getenv("ZCS_DASHBOARD_LOGIN_SHA256", "")
    writer = os.getenv("ZCS_DASHBOARD_WRITE_LOGIN_SHA256", "")
    other = ("ZERO_CODE_READ_TOKEN", "ZERO_CODE_WRITE_TOKEN", "ZERO_CODE_DASHBOARD_READ_TOKEN", "SNS_WRITE_TOKEN",
             "ZERO_CODE_METRICS_WRITE_TOKEN")
    if (not re.fullmatch(r"[a-f0-9]{64}", key) or not re.fullmatch(r"[a-f0-9]{64}", verifier)
            or (writer and (not re.fullmatch(r"[a-f0-9]{64}", writer) or writer == verifier))
            or any(secrets.compare_digest(key.encode(), os.getenv(name, "").strip().encode()) for name in other)):
        raise HTTPException(503, "Dashboard unavailable")
    if (not authorization or len(authorization) != 1
            or not secrets.compare_digest(authorization[0].encode(), ("Bearer " + key).encode())):
        raise HTTPException(401, "Unauthorized")
    return {"read": verifier, **({"write": writer} if writer else {})}


def nonce_field(value):
    if isinstance(value, str) and re.fullmatch(r"[a-f0-9]{32}", value):
        return value


def login(db: Session, verifiers: dict[str, str], credential_digest: str, previous: str | None):
    now = int(time.time())
    with db.begin():
        reserved = db.execute(reserve_attempt, {
            "reset": now + ATTEMPT_WINDOW, "now": now, "limit": ATTEMPT_LIMIT,
        }).scalar_one_or_none()
        if reserved is None:
            raise HTTPException(429, "Too many attempts", headers={"Retry-After": str(ATTEMPT_WINDOW)})
        matched = [f"{role}:{verifier}" for role, verifier in verifiers.items()
                   if secrets.compare_digest(credential_digest, verifier)]
        if not matched:
            return
        db.execute(delete(sessions).where(sessions.c.expires_at <= now))
        if previous:
            for role, verifier in verifiers.items():
                revoke(db, f"{role}:{verifier}", previous)
        nonce = secrets.token_hex(16)
        expires = now + SESSION_SECONDS
        db.execute(sessions.insert().values(nonce_hash=digest(matched[0] + nonce), expires_at=expires))
    return {"nonce": nonce, "expires": expires}


def valid(db: Session, verifier: str, nonce: str, expires: int) -> bool:
    return db.scalar(select(sessions.c.expires_at).where(
        sessions.c.nonce_hash == digest(verifier + nonce),
        sessions.c.expires_at == expires,
        sessions.c.expires_at > int(time.time()),
    )) is not None


def revoke(db: Session, verifier: str, nonce: str) -> None:
    db.execute(delete(sessions).where(sessions.c.nonce_hash == digest(verifier + nonce)))
