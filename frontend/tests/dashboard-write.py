"""Run against a built frontend with backend requirements installed."""
import hashlib
import os
from pathlib import Path
import secrets
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time

import httpx

ROOT = Path(__file__).resolve().parents[2]


def port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def ready(url, process):
    for _ in range(150):
        if process.poll() is not None:
            raise RuntimeError(f"Server stopped before {url} was ready")
        try:
            if httpx.get(url, timeout=1).status_code < 500:
                return
        except httpx.TransportError:
            pass
        time.sleep(0.2)
    raise RuntimeError(f"Timed out waiting for {url}")


def expect(response, status):
    assert response.status_code == status, (response.request.url, response.status_code, status)


def run(directory):
    dashboard_port, api_port = port(), port()
    origin = f"http://127.0.0.1:{dashboard_port}"
    api = f"http://127.0.0.1:{api_port}"
    reader, writer, token = (secrets.token_hex(32) for _ in range(3))
    database = Path(directory) / "isolated.db"
    env = {**os.environ,
           "DATABASE_URL": f"sqlite:///{database}",
           "VERCEL_ENV": "production",
           "ZERO_CODE_SKIP_SEED": "1",
           "CORS_ORIGINS": origin,
           "ZCS_DASHBOARD_ORIGIN": origin,
           "ZCS_DASHBOARD_API_ORIGIN": api,
           "ZCS_DASHBOARD_SESSION_KEY": secrets.token_hex(32),
           "ZCS_DASHBOARD_SESSION_SERVICE_TOKEN": secrets.token_hex(32),
           "ZERO_CODE_METRICS_WRITE_TOKEN": token,
           "ZCS_DASHBOARD_LOGIN_SHA256": hashlib.sha256(reader.encode()).hexdigest(),
           "ZCS_DASHBOARD_WRITE_LOGIN_SHA256": hashlib.sha256(writer.encode()).hexdigest()}
    api_command = """
import sys
import uvicorn
from app import main
with main.SessionLocal.begin() as db:
    db.add(main.Mission(code="MISSION 01", title="Test", status="active", progress=0))
main.youtube.configured = lambda: True
main.youtube.fetch_metrics = lambda day: ({"youtube_views": 17, "youtube_subscribers": 3}, None)
uvicorn.run(main.app, host="127.0.0.1", port=int(sys.argv[1]), access_log=False)
"""
    processes = []
    try:
        processes.append(subprocess.Popen([sys.executable, "-c", api_command, str(api_port)], cwd=ROOT / "backend", env=env))
        ready(f"{api}/health", processes[-1])
        processes.append(subprocess.Popen(
            ["node", "node_modules/next/dist/bin/next", "start", "-H", "127.0.0.1", "-p", str(dashboard_port)],
            cwd=ROOT / "frontend", env=env))
        ready(origin, processes[-1])
        manual = "/api/dashboard/write/manual"
        youtube = "/api/dashboard/write/youtube"
        session = "/api/dashboard/session"
        payload = {"tiktok_views": 11}
        with httpx.Client(base_url=origin, headers={"Origin": origin}, timeout=30) as client:
            expect(client.post(manual, json=payload), 401)
            expect(client.post(youtube), 401)
            expect(client.post(session, json={"credential": reader}), 200)
            assert client.get(session).json()["canWrite"] is False
            expect(client.patch(manual, json=payload), 403)
            expect(client.post(youtube), 403)
            expect(client.post(session, json={"credential": writer}), 200)
            assert client.get(session).json()["canWrite"] is True
            cookie = client.cookies.get("zcs-dashboard-local")
            expect(httpx.patch(origin + manual, cookies={"zcs-dashboard-local": cookie}, json=payload), 403)
            expect(client.post(youtube, headers={"Origin": "https://example.invalid"}), 403)
            expect(client.patch(youtube), 404)
            expect(httpx.patch(api + "/api/metrics/manual", json=payload), 401)
            expect(httpx.post(api + "/api/integrations/youtube/sync"), 401)
            with sqlite3.connect(database) as db:
                assert db.execute("SELECT count(*) FROM daily_metrics").fetchone() == (0,)
            for response in (client.post(manual, json=payload),
                             client.patch(manual, json={"tiktok_views": 13}),
                             client.post(youtube)):
                expect(response, 200)
                assert token not in response.text and token not in str(response.headers)
            with sqlite3.connect(database) as db:
                assert db.execute("SELECT tiktok_views, youtube_views, youtube_subscribers FROM daily_metrics").fetchall() == [(13, 17, 3)]
            expect(client.delete(session), 200)
            client.cookies.set("zcs-dashboard-local", cookie)
            expect(client.patch(manual, json=payload), 401)
            expect(client.post(youtube), 401)
            client.cookies.clear()
            expect(client.post(session, json={"credential": writer}), 200)
            with sqlite3.connect(database) as db:
                db.execute("UPDATE dashboard_sessions SET expires_at = 1")
            expect(client.patch(manual, json=payload), 401)
            assert token not in client.get("/").text
        for file in (ROOT / "frontend/.next/static").rglob("*.js"):
            assert token.encode() not in file.read_bytes()
        print("PASS dashboard write: login, role, Origin, POST/PATCH, mocked YouTube, persisted values, logout, expiry, server-only token")
    finally:
        for process in reversed(processes):
            process.terminate()
            process.wait(timeout=15)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="zcs-dashboard-write-") as directory:
        run(directory)
