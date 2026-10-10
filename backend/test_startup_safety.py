"""Fresh subprocesses prevent module caching from masking startup mutations."""
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

BACKEND = Path(__file__).resolve().parent


class StartupSafetyTests(unittest.TestCase):
    def run_python(self, database, code, skip=None):
        env = {key: os.environ[key] for key in ('PATH', 'SYSTEMROOT') if key in os.environ}
        env['DATABASE_URL'] = f'sqlite:///{database}'
        if skip is not None:
            env['ZERO_CODE_SKIP_SEED'] = skip
        result = subprocess.run([sys.executable, '-c', code], cwd=BACKEND, env=env,
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)

    def snapshot(self, database):
        with sqlite3.connect(database) as db:
            return list(db.iterdump())

    def test_import_and_startup_never_create_schema_with_or_without_skip(self):
        with tempfile.TemporaryDirectory() as folder:
            for skip in (None, '0', '1'):
                database = Path(folder) / f'empty-{skip}.db'
                self.run_python(database, '''
from app.main import app
from api.index import app as vercel_app
assert app is vercel_app
from fastapi.testclient import TestClient
from pathlib import Path
import os
assert not Path(os.environ['DATABASE_URL'].removeprefix('sqlite:///')).exists()
try:
    with TestClient(app):
        raise AssertionError('Uninitialized schema should fail startup')
except RuntimeError as error:
    assert 'schema is not ready' in str(error)
''', skip)
                with sqlite3.connect(database) as db:
                    self.assertEqual(db.execute('SELECT name FROM sqlite_master').fetchall(), [])

    def test_existing_data_and_schema_unchanged_on_cold_start(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / 'existing.db'
            self.run_python(database, '''
from app.main import seed, engine
from sqlalchemy import text
seed()
with engine.begin() as db:
    db.execute(text('UPDATE daily_metrics SET day=999, level=999, xp=999'))
''')
            before = self.snapshot(database)
            for skip in (None, '1'):
                self.run_python(database, '''
from app.main import app
from fastapi.testclient import TestClient
with TestClient(app) as client:
    assert client.get('/health').status_code == 200
''', skip)
                self.assertEqual(self.snapshot(database), before)

    def test_old_schema_fails_without_altering_or_seeding(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / 'old.db'
            self.run_python(database, '''
from app.main import seed, engine
from sqlalchemy import text
seed()
with engine.begin() as db:
    db.execute(text('ALTER TABLE daily_metrics DROP COLUMN xp'))
''')
            before = self.snapshot(database)
            self.run_python(database, '''
from app.main import app
from fastapi.testclient import TestClient
try:
    with TestClient(app):
        raise AssertionError('Outdated schema should fail startup')
except RuntimeError as error:
    assert 'schema is outdated' in str(error)
''')
            self.assertEqual(self.snapshot(database), before)

    def test_explicit_commands_separate_schema_from_seed(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / 'commands.db'
            env = {key: os.environ[key] for key in ('PATH', 'SYSTEMROOT') if key in os.environ}
            env['DATABASE_URL'] = f'sqlite:///{database}'
            def command(action, expected=0):
                result = subprocess.run([sys.executable, '-m', 'app.db_admin', action],
                                        cwd=BACKEND, env=env, capture_output=True, timeout=20)
                self.assertEqual(result.returncode, expected, result.stderr.decode())
            command('migrate')
            with sqlite3.connect(database) as db:
                self.assertEqual(db.execute('SELECT count(*) FROM daily_metrics').fetchone()[0], 0)
                schema = db.execute('SELECT sql FROM sqlite_master ORDER BY name').fetchall()
            before = database.read_bytes()
            command('check')
            command('ready', 1)
            self.assertEqual(database.read_bytes(), before)
            command('seed')
            command('ready')
            command('seed')
            with sqlite3.connect(database) as db:
                self.assertEqual(db.execute('SELECT count(*) FROM daily_metrics').fetchone()[0], 1)
                self.assertEqual(db.execute('SELECT sql FROM sqlite_master ORDER BY name').fetchall(), schema)
            del env['DATABASE_URL']
            command('migrate', 2)
            command('seed', 2)
            command('check', 2)
            command('ready', 2)
