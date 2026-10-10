"""Counter boundaries, schema parity and non-destructive explicit migration."""
import io
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from alembic import command
from alembic.config import Config
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.schema import CreateTable

from test_api import ApiTests
from app.main import Base, DailyMetrics, Mission, SessionLocal, engine
from app.youtube import counter, YouTubeError


class CounterApiTests(unittest.TestCase):
    setUp = ApiTests.setUp
    tearDown = ApiTests.tearDown
    update = ApiTests.update

    def test_all_manual_boundaries(self):
        for value in (0, 2147483647, 2147483648, 9007199254740991):
            with self.subTest(value=value):
                data = self.update(tiktok_followers=value, tiktok_views=value, total_revenue_yen=value)
                self.assertEqual(data['tiktok'], {'followers': value, 'views': value})
                self.assertEqual(data['total_revenue_yen'], value)
                with SessionLocal() as db:
                    row = db.query(DailyMetrics).one()
                    self.assertEqual((row.tiktok_followers, row.tiktok_views, row.total_revenue_yen), (value,) * 3)


    def test_invalid_each_field_preserves_every_row(self):
        self.update(total_revenue_yen=2147483648)
        def snapshot():
            with engine.connect() as db:
                return {t.name: list(db.execute(t.select())) for t in Base.metadata.sorted_tables}
        before = snapshot()
        for field in ('tiktok_followers', 'tiktok_views', 'total_revenue_yen'):
            for value in (-1, 9007199254740992, 9223372036854775808, True, False, 1.5, '1', None):
                for method in ('post', 'patch'):
                    with self.subTest(field=field, value=value, method=method):
                        response = getattr(self.client, method)('/api/metrics/manual', json={field: value})
                        self.assertEqual(response.status_code, 422)
                        self.assertEqual(snapshot(), before)

    def test_large_mission_target_completes_only_at_threshold(self):
        with SessionLocal() as db:
            mission = db.query(Mission).one()
            mission.target_value = 9007199254740991
            db.commit()
        data = self.update(total_revenue_yen=2147483648)
        self.assertEqual(data['mission']['status'], 'active')
        self.assertEqual(data['mission']['target_value'], 9007199254740991)
        self.assertEqual(self.update(total_revenue_yen=9007199254740990)['mission']['status'], 'active')
        data = self.update(total_revenue_yen=9007199254740991)
        self.assertEqual(data['mission']['status'], 'completed')

# Avoid discovering the imported suite a second time.
del ApiTests


class CounterStorageTests(unittest.TestCase):
    def test_youtube_boundaries(self):
        for value in (0, 2147483647, 2147483648, 9007199254740991):
            self.assertEqual(counter(str(value)), value)
        for value in (-1, 9007199254740992, True, 1.5, None, 'bad'):
            with self.assertRaises(YouTubeError):
                counter(value)

    def test_postgres_offline_migration_matches_model(self):
        output = io.StringIO()
        config = Config('alembic.ini', output_buffer=output)
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://audit:audit@127.0.0.1:1/audit'}):
            command.upgrade(config, 'head', sql=True)
        sql = output.getvalue()
        fields = ('youtube_subscribers', 'youtube_views', 'youtube_watch_minutes',
                  'youtube_likes', 'youtube_comments', 'tiktok_followers', 'tiktok_views', 'total_revenue_yen')
        for table, names in ((DailyMetrics.__table__, fields), (Mission.__table__, ('target_value',))):
            for name in names:
                self.assertEqual(table.c[name].type.compile(dialect=postgresql.dialect()), 'BIGINT')
                self.assertEqual(table.c[name].type.compile(dialect=sqlite.dialect()), 'INTEGER')
                self.assertIn(f'ALTER TABLE {table.name} ALTER COLUMN {name} TYPE BIGINT;', sql)
        self.assertEqual(sql.count('TYPE BIGINT;'), 9)
        self.assertNotIn('DROP TABLE', sql)
        self.assertIn('id SERIAL', str(CreateTable(DailyMetrics.__table__).compile(dialect=postgresql.dialect())))

    def test_sqlite_upgrade_copy_restore_preserves_large_existing_values(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.db'
            config = Config('alembic.ini')
            with patch.dict(os.environ, {'DATABASE_URL': f'sqlite:///{source}'}):
                command.upgrade(config, '0001_initial_schema')
                with sqlite3.connect(source) as db:
                    db.execute("INSERT INTO missions (id,code,title,target_value) VALUES (1,'TEST','test',9007199254740991)")
                    db.execute("INSERT INTO daily_metrics (id,date,tiktok_views,total_revenue_yen,tiktok_views_observed_on) VALUES (1,'2026-10-10',2147483648,9007199254740991,'2026-10-10')")
                    for field in ('youtube_subscribers', 'youtube_views', 'youtube_watch_minutes', 'youtube_likes', 'youtube_comments'):
                        db.execute(f'UPDATE daily_metrics SET {field}=?', (9007199254740991,))
                def snapshot():
                    with sqlite3.connect(source) as db:
                        return (db.execute('SELECT * FROM missions').fetchall(),
                                db.execute('SELECT * FROM daily_metrics').fetchall(),
                                db.execute('SELECT name,sql FROM sqlite_master ORDER BY name').fetchall())
                before = snapshot()
                command.upgrade(config, 'head')
                command.upgrade(config, 'head')
                self.assertEqual(snapshot(), before)
                with self.assertRaises(RuntimeError):
                    command.downgrade(config, '0001_initial_schema')
                self.assertEqual(snapshot(), before)
                with sqlite3.connect(source) as db:
                    self.assertEqual(db.execute('SELECT version_num FROM alembic_version').fetchone()[0], '0002_widen_counters')
            from sqlalchemy import create_engine, text
            from migrate_sqlite_to_postgres import copy_data
            src = create_engine(f'sqlite:///{source}')
            dst = create_engine(f'sqlite:///{folder}/copy.db')
            Base.metadata.create_all(dst)
            copy_data(src, dst)
            with src.connect() as a, dst.connect() as b:
                for table in Base.metadata.sorted_tables:
                    self.assertEqual(list(a.execute(table.select())), list(b.execute(table.select())))
            src.dispose()
            dst.dispose()
            with sqlite3.connect(Path(folder) / 'copy.db') as a, sqlite3.connect(Path(folder) / 'restore.db') as b:
                a.backup(b)
                self.assertEqual(list(a.iterdump()), list(b.iterdump()))
