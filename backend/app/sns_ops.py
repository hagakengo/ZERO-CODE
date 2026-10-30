"""Pure helpers for note-to-X operations. No credentials are stored here."""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from urllib.parse import urlparse
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

import httpx

JST = ZoneInfo("Asia/Tokyo")
POSTING_WEEKDAYS = {0, 2, 4}  # Monday, Wednesday, Friday
HOLD_PATTERNS = (
    "未公開", "機密", "confidential", "secret", "master承認", "正式発表前",
    "課金", "有料サービス", "キャラクター設定", "脚本全文",
)
NOTE_URL = re.compile(r"^https://note\.com/[A-Za-z0-9_-]+/n/[A-Za-z0-9_-]+/?$")


class FeedError(Exception):
    pass


def canonical_note_url(value: str) -> str:
    value = value.strip().split("#", 1)[0].split("?", 1)[0].rstrip("/")
    if not NOTE_URL.fullmatch(value):
        raise ValueError("Only published note article URLs are accepted.")
    return value


def normal_announcement(title: str, summary: str = "") -> bool:
    text = f"{title}\n{summary}".casefold()
    return not any(term.casefold() in text for term in HOLD_PATTERNS)


def draft_text(title: str, url: str) -> str:
    url = canonical_note_url(url)
    text = f"ZERO CODE STUDIOの制作記録をnoteで公開しました。\n\n{title}\n{url}"
    if len(text) > 260:
        text = f"ZERO CODE STUDIOの新しい記事を公開しました。\n\n{title[:100]}\n{url}"
    return text


def next_slot(after: datetime, occupied: set[datetime]) -> datetime:
    cursor = after.astimezone(JST)
    candidate = cursor.replace(hour=20, minute=0, second=0, microsecond=0)
    if candidate <= cursor:
        candidate += timedelta(days=1)
    while candidate.weekday() not in POSTING_WEEKDAYS or candidate in occupied:
        candidate += timedelta(days=1)
    return candidate


def parse_note_rss(xml: str) -> list[dict[str, str]]:
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError:
        raise FeedError("note RSS returned invalid XML.") from None
    items = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = (item.findtext("description") or "").strip()
        if not title or not link:
            continue
        try:
            link = canonical_note_url(link)
        except ValueError:
            continue
        items.append({"title": title, "url": link, "summary": description})
    return items


def fetch_note_rss(url: str, timeout: float = 15) -> list[dict[str, str]]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "note.com" or not parsed.path.endswith("/rss"):
        raise FeedError("NOTE_RSS_URL must be an https://note.com/.../rss URL.")
    try:
        response = httpx.get(url, timeout=timeout, follow_redirects=False)
        response.raise_for_status()
        return parse_note_rss(response.text)
    except FeedError:
        raise
    except Exception:
        raise FeedError("note RSS is unavailable.") from None
