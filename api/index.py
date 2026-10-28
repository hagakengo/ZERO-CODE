"""Vercel Preview entrypoint for the existing ZERO CODE FastAPI backend."""

from backend.app.main import app as upstream_app
from urllib.parse import parse_qs


async def app(scope, receive, send):
    """Preserve the public path after Vercel rewrites to ``/api/index``."""
    if scope.get("type") == "http":
        scope = dict(scope)
        path = scope.get("path", "")
        prefix = "/api/index"
        rewritten = parse_qs(scope.get("query_string", b"").decode("utf-8")).get(
            "__path", []
        )
        if rewritten:
            scope["path"] = "/" + rewritten[0].lstrip("/")
            scope["query_string"] = b""
            scope["raw_path"] = scope["path"].encode("utf-8")
        elif path.startswith(prefix):
            scope["path"] = path[len(prefix):] or "/"
            scope["raw_path"] = scope["path"].encode("utf-8")
    await upstream_app(scope, receive, send)


__all__ = ["app"]
