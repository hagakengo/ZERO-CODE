"""Minimal Buffer GraphQL integration. Never propagate upstream error bodies."""
import json
import os
import re
from datetime import datetime, timezone
import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, StrictBool

from .sns_auth import require_sns_write_token

router = APIRouter(prefix="/api/integrations/buffer")
ENDPOINT = "https://api.buffer.com"


class BufferError(Exception):
    pass


def configured():
    return bool(os.getenv("BUFFER_API_KEY", "").strip())


def graphql(query):
    key = os.getenv("BUFFER_API_KEY", "").strip()
    if not key:
        raise BufferError("Buffer is not configured.")
    try:
        response = httpx.post(ENDPOINT, headers={"Authorization": f"Bearer {key}"},
                              json={"query": query}, timeout=15, follow_redirects=False)
        if response.status_code in (401, 403):
            raise BufferError("Buffer authentication failed.")
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict) or body.get("errors") or not isinstance(body.get("data"), dict):
            raise BufferError("Buffer request failed.")
        return body["data"]
    except BufferError:
        raise
    except Exception:
        raise BufferError("Buffer is unavailable or returned an invalid response.") from None


def organizations():
    try:
        values = graphql("query { account { organizations { id } } }")["account"]["organizations"]
        if not values or any(not isinstance(value.get("id"), str) for value in values):
            raise ValueError()
        return [value["id"] for value in values]
    except BufferError:
        raise
    except Exception:
        raise BufferError("Buffer returned an invalid organization response.") from None


def channels():
    try:
        result = {}
        for organization_id in organizations():
            query = "query { channels(input: { organizationId: " + json.dumps(organization_id) + " }) { id service } }"
            for channel in graphql(query)["channels"]:
                if not isinstance(channel["id"], str) or not isinstance(channel["service"], str):
                    raise ValueError()
                result[channel["id"]] = channel
        return list(result.values())
    except BufferError:
        raise
    except Exception:
        raise BufferError("Buffer returned an invalid channel response.") from None


def posts(channel_id, statuses=("scheduled", "sent"), first=100):
    """Read posts for duplicate detection and delivery reconciliation."""
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", channel_id):
        raise BufferError("Invalid Buffer channel.")
    if not statuses or any(status not in {"scheduled", "sent", "failed"} for status in statuses):
        raise BufferError("Invalid Buffer post status filter.")
    organization_id = organizations()[0]
    status_list = ", ".join(statuses)
    query = (
        "query { posts(first: " + str(min(max(first, 1), 100)) +
        ", input: { organizationId: " + json.dumps(organization_id) +
        ", filter: { status: [" + status_list + "], channelIds: [" + json.dumps(channel_id) +
        "] } }) { edges { node { id text dueAt channelId externalLink } } pageInfo { hasNextPage endCursor } } }"
    )
    try:
        result = graphql(query)["posts"]
        values = [edge["node"] for edge in result["edges"]]
        if any(not isinstance(value.get("id"), str) or not isinstance(value.get("text"), str)
               for value in values):
            raise ValueError()
        return values
    except BufferError:
        raise
    except Exception:
        raise BufferError("Buffer returned an invalid posts response.") from None


def find_duplicate(items, text, due):
    normalized = text.strip()
    for item in items:
        if item.get("text", "").strip() != normalized:
            continue
        if due is None or item.get("dueAt") == due:
            return item
    return None


def schedule_post(text, scheduled_at, channel_id=None):
    """Idempotent create: inspect Buffer before every write or retry."""
    due = scheduled_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    channel = channel_id or resolve_x(channels())
    existing = find_duplicate(posts(channel), text, due)
    if existing:
        return {"duplicate": True, "post_id": existing["id"],
                "scheduled_at": existing.get("dueAt") or due}
    query = ("mutation { createPost(input: { text: " + json.dumps(text) +
             ", channelId: " + json.dumps(channel) +
             ", schedulingType: automatic, mode: customScheduled, dueAt: " + json.dumps(due) +
             " }) { ... on PostActionSuccess { post { id } } ... on MutationError { message } } }")
    action = graphql(query).get("createPost")
    if not isinstance(action, dict) or not isinstance(action.get("post"), dict):
        raise BufferError("Buffer scheduling failed. Check Buffer before retrying.")
    post_id = action["post"].get("id")
    if not isinstance(post_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", post_id):
        raise BufferError("Buffer returned an invalid post result. Check Buffer before retrying.")
    return {"duplicate": False, "post_id": post_id, "scheduled_at": due}


def resolve_x(items):
    targets = [c for c in items if c["service"].lower() == "twitter"]
    selected = os.getenv("BUFFER_X_CHANNEL_ID", "").strip()
    if selected:
        matches = [c for c in targets if c["id"] == selected]
        if not matches:
            raise BufferError("Configured Buffer X channel is unavailable.")
        return matches[0]["id"]
    if not targets:
        raise BufferError("No Buffer X channel is connected.")
    if len(targets) != 1:
        raise BufferError("Multiple X channels found; set BUFFER_X_CHANNEL_ID.")
    return targets[0]["id"]


@router.get("/status")
def status():
    result = dict(configured=configured(), connected=False, channel_count=0,
                  x_channel_available=False, error=None)
    if not result["configured"]:
        return result
    try:
        items = channels()
        result.update(connected=True, channel_count=len(items),
                      x_channel_available=any(c["service"].lower() == "twitter" for c in items))
        try:
            resolve_x(items)
        except BufferError as error:
            result["error"] = str(error)
    except BufferError as error:
        result["error"] = str(error)
    return result


class ScheduleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    scheduled_at: str
    dry_run: StrictBool = True


def validate(payload):
    # Conservative X weighting: non-Latin characters count as two; URLs are
    # deliberately counted in full. Reject long content instead of threading.
    text = payload.text.strip()
    weight = sum(1 if ord(c) <= 0x10ff or 0x2000 <= ord(c) <= 0x200d or
                 0x2010 <= ord(c) <= 0x201f or 0x2032 <= ord(c) <= 0x2037 else 2 for c in text)
    if not text or weight > 280:
        raise HTTPException(422, "X text must be non-empty and at most 280 weighted characters.")
    try:
        if not re.match(r"^\d{4}-\d{2}-\d{2}T", payload.scheduled_at):
            raise ValueError()
        due = datetime.fromisoformat(payload.scheduled_at.replace("Z", "+00:00"))
        if due.tzinfo is None or due <= datetime.now(timezone.utc):
            raise ValueError()
    except ValueError:
        raise HTTPException(422, "scheduled_at must be a future ISO 8601 datetime with timezone.") from None
    return text, due.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@router.post("/schedule")
def schedule(payload: ScheduleInput, request: Request,
             x_zcs_sns_token: str | None = Header(default=None)):
    require_sns_write_token(x_zcs_sns_token)
    allowed = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if request.headers.get("origin") and request.headers["origin"] not in allowed:
        raise HTTPException(403, "Origin not allowed")
    text, due = validate(payload)
    if not configured():
        raise HTTPException(409, "Buffer is not configured.")
    try:
        channel = resolve_x(channels())
        if payload.dry_run:
            existing = find_duplicate(posts(channel), text, due)
            if existing:
                return dict(dry_run=True, duplicate=True,
                            post_id=existing["id"], scheduled_at=existing.get("dueAt") or due)
            return dict(dry_run=True, channel_id=channel, scheduled_at=due)
        result = schedule_post(text, datetime.fromisoformat(due.replace("Z", "+00:00")), channel)
        return dict(dry_run=False, **result)
    except BufferError as error:
        raise HTTPException(502, str(error)) from None
