"""Shared authentication boundary for SNS read and write operations."""
import os
import secrets

from fastapi import HTTPException


def require_sns_write_token(supplied: str | None) -> None:
    expected = os.getenv("SNS_WRITE_TOKEN", "").strip()
    if not expected:
        raise HTTPException(503, "SNS write access is not configured.")
    if not supplied or not secrets.compare_digest(supplied, expected):
        raise HTTPException(401, "Unauthorized")
