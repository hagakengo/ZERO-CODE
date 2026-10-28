"""Vercel Preview entrypoint for the existing ZERO CODE FastAPI backend."""

from backend.app.main import app as upstream_app


async def app(scope, receive, send):
    """Preserve the public path after Vercel rewrites to ``/api/index``."""
    if scope.get("type") == "http":
        scope = dict(scope)
        path = scope.get("path", "")
        prefix = "/api/index"
        if path.startswith(prefix):
            scope["path"] = path[len(prefix):] or "/"
            scope["raw_path"] = scope["path"].encode("utf-8")
    await upstream_app(scope, receive, send)


__all__ = ["app"]
