"""Fail-closed bearer authorization for operations that mutate data or schedule posts."""
import os
import secrets

from fastapi import Header, HTTPException


def require_write_token(authorization: str | None = Header(default=None)) -> None:
    expected = os.getenv("ZERO_CODE_WRITE_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Write API is not configured")
    scheme, separator, provided = (authorization or "").partition(" ")
    if (not separator or scheme.lower() != "bearer" or
            not secrets.compare_digest(provided, expected)):
        raise HTTPException(
            status_code=401,
            detail="Invalid write authorization",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_dashboard_read_token(authorization: str | None = Header(default=None)) -> None:
    """Protect private dashboard reads. Accept operator write or dedicated read token."""
    configured = [value.strip() for value in (
        os.getenv("ZERO_CODE_WRITE_TOKEN", ""),
        os.getenv("ZERO_CODE_READ_TOKEN", ""),
    ) if value.strip()]
    if not configured:
        raise HTTPException(status_code=503, detail="Read API is not configured")
    scheme, separator, provided = (authorization or "").partition(" ")
    valid = separator and scheme.lower() == "bearer" and any(
        secrets.compare_digest(provided, expected) for expected in configured
    )
    if not valid:
        raise HTTPException(
            status_code=401, detail="Invalid read authorization",
            headers={"WWW-Authenticate": "Bearer"},
        )
