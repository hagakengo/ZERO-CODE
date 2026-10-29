"""Vercel entrypoint that preserves paths after the catch-all rewrite."""

from urllib.parse import parse_qs

from app.main import app as upstream_app


async def app(scope, receive, send):
    if scope.get("type") == "http":
        scope = dict(scope)
        rewritten = parse_qs(scope.get("query_string", b"").decode("utf-8")).get(
            "__path", []
        )
        if rewritten:
            scope["path"] = "/" + rewritten[0].lstrip("/")
            scope["query_string"] = b""
            scope["raw_path"] = scope["path"].encode("utf-8")
    await upstream_app(scope, receive, send)
