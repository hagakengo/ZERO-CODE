"""Real Next.js -> FastAPI HTTP tests; temporary SQLite and dummy credentials only.
Run after `cd frontend && npm ci && npm run build`, using Python 3.11+.
"""
import base64
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
WRITE = 'integration-only-write-secret'
READ = 'integration-only-read-secret'
PASSWORD = 'integration-only-admin-password'
AUTH = 'Basic ' + base64.b64encode(f'operator:{PASSWORD}'.encode()).decode()


def port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def request(base, path, method='GET', auth=None, data=None, extra_headers=None):
    headers = {} if auth is None else {'Authorization': auth}
    if method not in ('GET', 'HEAD', 'OPTIONS'):
        headers['Origin'] = base
    headers.update(extra_headers or {})
    headers = {key: value for key, value in headers.items() if value is not None}
    body = None if data is None else json.dumps(data).encode()
    if body is not None:
        headers['Content-Type'] = 'application/json'
    try:
        response = urlopen(Request(base + path, data=body, headers=headers, method=method), timeout=10)
    except HTTPError as error:
        response = error
    with response:
        return response.status, response.headers, response.read()


class DashboardAuthIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Refuse local credential files; tests must never load operator settings.
        for folder in ('backend', 'frontend'):
            for candidate in (ROOT / folder).glob('.env*'):
                if candidate.name != '.env.example':
                    raise RuntimeError('Run integration tests in a clean checkout without .env files')
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.processes = []
        cls.env = {key: os.environ[key] for key in ('PATH', 'SYSTEMROOT') if key in os.environ}
        cls.env.update(DATABASE_URL=f'sqlite:///{cls.temp.name}/auth.db',
                       ZERO_CODE_WRITE_TOKEN=WRITE, ZERO_CODE_READ_TOKEN=READ,
                       ZERO_CODE_ADMIN_USER='operator', ZERO_CODE_ADMIN_PASSWORD=PASSWORD,
                       METRICS_TIMEZONE='Asia/Tokyo', NEXT_TELEMETRY_DISABLED='1')
        cls.backend = f'http://127.0.0.1:{port()}'
        cls.frontend = f'http://127.0.0.1:{port()}'
        cls.env['ZERO_CODE_BACKEND_URL'] = cls.backend
        cls.env['ZERO_CODE_FRONTEND_ORIGIN'] = cls.frontend
        subprocess.run([sys.executable, '-m', 'app.db_admin', 'migrate'],
                       cwd=ROOT / 'backend', env=cls.env, check=True)
        subprocess.run([sys.executable, '-m', 'app.db_admin', 'seed'],
                       cwd=ROOT / 'backend', env=cls.env, check=True)
        cls.start([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1',
                   '--port', cls.backend.rsplit(':', 1)[1]], ROOT / 'backend', cls.backend, '/health')
        cls.start(['node', 'node_modules/next/dist/bin/next', 'start', '--hostname', '127.0.0.1',
                   '--port', cls.frontend.rsplit(':', 1)[1]], ROOT / 'frontend', cls.frontend, '/')

    @classmethod
    def start(cls, command, cwd, base, path, overrides=None):
        log = open(Path(cls.temp.name) / f'{len(cls.processes)}.log', 'wb')
        cls.addClassCleanup(log.close)
        process = subprocess.Popen(command, cwd=cwd, env={**cls.env, **(overrides or {})}, stdout=log, stderr=log)
        cls.processes.append(process)
        def stop():
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        cls.addClassCleanup(stop)
        for _ in range(150):
            if process.poll() is not None:
                raise RuntimeError('Test server exited; inspect isolated server log')
            try:
                request(base, path)
                return stop
            except (URLError, TimeoutError):
                time.sleep(0.1)
        raise RuntimeError('Test server did not become ready')

    def safe(self, result):
        status, headers, body = result
        exposed = str(headers).encode() + body
        for secret in (WRITE, READ, PASSWORD):
            self.assertNotIn(secret.encode(), exposed)
        return status, body

    def test_unauthorized_page_and_proxy(self):
        before = request(self.backend, '/api/metrics/history', auth=f'Bearer {READ}')[2]
        for auth in (None, 'Basic invalid', 'Basic ' + base64.b64encode(b'operator:wrong').decode(), f'Bearer {WRITE}'):
            for path, method, data in (('/', 'GET', None), ('/api/private/status', 'GET', None),
                                      ('/api/private/manual', 'PATCH', {'total_revenue_yen': 9})):
                with self.subTest(path=path, auth=auth):
                    result = request(self.frontend, path, method, auth, data)
                    self.assertEqual(self.safe(result)[0], 401)
                    self.assertIn('no-store', result[1]['Cache-Control'])
        self.assertEqual(request(self.backend, '/api/metrics/history', auth=f'Bearer {READ}')[2], before)

    def test_authenticated_read_and_write(self):
        for action in ('status', 'history', 'youtube_status', 'buffer_status'):
            result = request(self.frontend, f'/api/private/{action}', auth=AUTH)
            self.assertEqual(self.safe(result)[0], 200)
            self.assertIn('no-store', result[1]['Cache-Control'])
        result = request(self.frontend, '/api/private/manual', 'PATCH', AUTH, {'tiktok_views': 42})
        self.assertEqual(self.safe(result)[0], 200)
        self.assertEqual(json.loads(result[2])['tiktok']['views'], 42)
        direct = request(self.backend, '/api/status', auth=f'Bearer {READ}')
        self.assertEqual(json.loads(direct[2])['tiktok']['views'], 42)

    def test_backend_permission_boundary(self):
        for path in ('/api/status', '/api/metrics/history', '/api/integrations/buffer/status'):
            for auth in (None, AUTH, 'Bearer wrong'):
                self.assertEqual(self.safe(request(self.backend, path, auth=auth))[0], 401)
        for path, method in (('/api/metrics/manual', 'PATCH'),
                             ('/api/integrations/youtube/sync', 'POST'),
                             ('/api/integrations/buffer/schedule', 'POST')):
            self.assertEqual(self.safe(request(self.backend, path, method, f'Bearer {READ}', {}))[0], 401)

    def test_action_method_and_payload_boundary(self):
        for path, method in (('/api/private/unknown', 'GET'), ('/api/private/manual', 'GET'),
                             ('/api/private/status', 'POST')):
            self.assertEqual(self.safe(request(self.frontend, path, method, AUTH))[0], 404)
        self.assertEqual(self.safe(request(self.frontend, '/api/private/manual', 'PATCH', AUTH, {'tiktok_views': -1}))[0], 422)
        self.assertEqual(self.safe(request(self.frontend, '/api/private/manual', 'PATCH', AUTH, {'padding': 'x' * 9000}))[0], 413)

    def test_proxy_configuration_fails_closed(self):
        for overrides, expected in (
            ({'ZERO_CODE_WRITE_TOKEN': ''}, 503),
            ({'ZERO_CODE_WRITE_TOKEN': 'incorrect-test-token'}, 401),
            ({'ZERO_CODE_WRITE_TOKEN': READ}, 401),
            ({'ZERO_CODE_BACKEND_URL': 'http://untrusted.example'}, 503),
            ({'ZERO_CODE_ADMIN_PASSWORD': ''}, 401),
            ({'ZERO_CODE_FRONTEND_ORIGIN': ''}, 503),
            ({'ZERO_CODE_FRONTEND_ORIGIN': 'https://example.invalid/path'}, 503),
            ({'ZERO_CODE_FRONTEND_ORIGIN': 'http://example.invalid'}, 503),
        ):
            with self.subTest(configuration=list(overrides)):
                base = f'http://127.0.0.1:{port()}'
                stop = self.start(['node', 'node_modules/next/dist/bin/next', 'start',
                                   '--hostname', '127.0.0.1', '--port', base.rsplit(':', 1)[1]],
                                  ROOT / 'frontend', base, '/', {'ZERO_CODE_FRONTEND_ORIGIN': base, **overrides})
                try:
                    before = request(self.backend, '/api/metrics/history', auth=f'Bearer {READ}')[2]
                    result = request(base, '/api/private/manual', 'PATCH', AUTH, {'tiktok_views': 99})
                    self.assertEqual(self.safe(result)[0], expected)
                    self.assertEqual(request(self.backend, '/api/metrics/history', auth=f'Bearer {READ}')[2], before)
                finally:
                    stop()

    def test_csrf_mutations_fail_closed_without_writing(self):
        before = request(self.backend, '/api/metrics/history', auth=f'Bearer {READ}')[2]
        for action, method in (('manual', 'PATCH'), ('youtube', 'POST'), ('buffer', 'POST')):
            for headers in (
                {'Origin': 'https://attacker.invalid', 'Sec-Fetch-Site': 'cross-site'},
                {'Origin': None}, {'Origin': 'null'},
                {'Origin': self.frontend + '/'},
                {'Origin': self.frontend + ', https://attacker.invalid'},
                {'Origin': self.frontend, 'Sec-Fetch-Site': 'cross-site'},
                {'Origin': 'https://attacker.invalid', 'X-Forwarded-Host': 'attacker.invalid',
                 'X-Forwarded-Proto': 'https'},
                {'Origin': self.frontend, 'Host': 'attacker.invalid'},
            ):
                with self.subTest(action=action, headers=headers):
                    result = request(self.frontend, '/api/private/' + action, method, AUTH,
                                     {'tiktok_views': 123}, headers)
                    self.assertEqual(self.safe(result)[0], 403)
                    self.assertIn('no-store', result[1]['Cache-Control'])
        self.assertEqual(request(self.backend, '/api/metrics/history', auth=f'Bearer {READ}')[2], before)

    def test_csrf_same_origin_and_fetch_metadata(self):
        for site in (None, 'same-origin', 'same-site'):
            result = request(self.frontend, '/api/private/manual', 'PATCH', AUTH,
                             {'tiktok_views': 42}, {'Sec-Fetch-Site': site})
            self.assertEqual(self.safe(result)[0], 200)
        # Valid-origin POST reaches safe unconfigured integration, never real OAuth.
        self.assertEqual(self.safe(request(self.frontend, '/api/private/youtube', 'POST', AUTH))[0], 409)
        # Read-only proxy remains available to non-browser HTTP clients without Origin.
        self.assertEqual(self.safe(request(self.frontend, '/api/private/status', auth=AUTH,
                                          extra_headers={'Origin': None}))[0], 200)

    def test_csrf_rejection_never_calls_upstream_and_buffer_dry_run_passes(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from threading import Thread
        calls = []
        class Spy(BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers.get('Content-Length', '0')))
                calls.append((self.path, json.loads(body)))
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"dry_run":true,"created":false}')
            def do_PATCH(self):
                self.do_POST()
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Spy)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{port()}'
        stop = self.start(['node', 'node_modules/next/dist/bin/next', 'start',
                           '--hostname', '127.0.0.1', '--port', base.rsplit(':', 1)[1]],
                          ROOT / 'frontend', base, '/', {
                              'ZERO_CODE_FRONTEND_ORIGIN': base,
                              'ZERO_CODE_BACKEND_URL': f'http://127.0.0.1:{server.server_port}'})
        try:
            for action, method in (('manual', 'PATCH'), ('youtube', 'POST'), ('buffer', 'POST')):
                for origin in (None, 'null', 'https://attacker.invalid'):
                    result = request(base, '/api/private/' + action, method, AUTH,
                                     {'text': 'TEST', 'dry_run': True}, {'Origin': origin})
                    self.assertEqual(result[0], 403)
            self.assertEqual(calls, [])
            result = request(base, '/api/private/buffer', 'POST', AUTH,
                             {'text': 'TEST', 'dry_run': True})
            self.assertEqual(result[0], 200)
            self.assertEqual(calls, [('/api/integrations/buffer/schedule',
                                      {'text': 'TEST', 'dry_run': True})])
        finally:
            stop()
            server.shutdown()
            server.server_close()
            thread.join()

    def test_no_secrets_in_html_or_browser_assets(self):
        result = request(self.frontend, '/', auth=AUTH)
        self.assertEqual(self.safe(result)[0], 200)
        self.assertIsNone(result[1].get('Set-Cookie'))  # Basic auth, no session cookie.
        assets = list((ROOT / 'frontend/.next/static').rglob('*.js'))
        self.assertTrue(assets)
        for asset in assets:
            contents = asset.read_bytes()
            for secret in (WRITE, READ, PASSWORD):
                self.assertNotIn(secret.encode(), contents, asset.name)
            self.assertNotIn(b'ZERO_CODE_WRITE_TOKEN', contents, asset.name)
            self.assertNotIn(b'ZERO_CODE_ADMIN_PASSWORD', contents, asset.name)


if __name__ == '__main__':
    unittest.main(verbosity=2)
