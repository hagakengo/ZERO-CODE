import tempfile
from pathlib import Path
import unittest
import test_startup_safety


class ReadinessTests(unittest.TestCase):
    run_python = test_startup_safety.StartupSafetyTests.run_python
    # Only the new test belongs here; inherited startup tests remain in their suite.
    def test_readiness_schema_data_failure_and_no_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / 'ready.db'
            self.run_python(database, '''
from app.main import app, engine, seed_data
from app.db_admin import initialize_schema
from fastapi.testclient import TestClient
from sqlalchemy import text
from unittest.mock import patch
client = TestClient(app, raise_server_exceptions=False) # no lifespan
assert client.get('/health').status_code == 200
assert client.get('/ready').json() == {'status': 'not_ready'}
initialize_schema()
with TestClient(app) as client:
    assert client.get('/health').status_code == 200
    result = client.get('/ready')
    assert result.status_code == 503 and result.json() == {'status': 'not_ready'}
    assert result.headers['cache-control'] == 'no-store'
    import os
    os.environ['ZERO_CODE_WRITE_TOKEN'] = 'test-only'
    probe = TestClient(app, raise_server_exceptions=False)
    assert probe.get('/api/status', headers={'Authorization': 'Bearer test-only'}).status_code == 500
seed_data()
with engine.connect() as conn:
    before = list(conn.execute(text('SELECT * FROM daily_metrics')))
assert client.get('/ready').status_code == 200
with engine.connect() as conn:
    assert list(conn.execute(text('SELECT * FROM daily_metrics'))) == before
with engine.begin() as conn:
    conn.execute(text('DELETE FROM missions'))
assert client.get('/ready').status_code == 503
with patch('app.main.validate_readiness', side_effect=RuntimeError('secret database URL')):
    assert client.get('/ready').json() == {'status': 'not_ready'}
''')
