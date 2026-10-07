"""Phase 4 tests exclusively use test_api's temporary SQLite database."""
import unittest
from datetime import timedelta
from unittest.mock import patch
from sqlalchemy import select, text, func
import test_api as support
from app.main import DailyMetrics, Mission, SessionLocal, engine, seed
TODAY = support.TODAY


class ProgressionTests(unittest.TestCase):
    setUp = support.ApiTests.setUp
    tearDown = support.ApiTests.tearDown
    update = support.ApiTests.update

    def status(self):
        return self.client.get('/api/status').json()['progression']

    def test_no_observation_no_progression(self):
        self.assertEqual(self.status()['day'], 0)
        self.assertEqual(self.status()['xp'], 0)
        self.assertIsNone(self.status()['first_recorded_on'])
        with patch('app.main.metrics_today', return_value=TODAY + timedelta(days=30)):
            self.assertEqual(self.status()['day'], 0)
        history = self.client.get('/api/metrics/history').json()
        self.assertFalse(history[0]['recorded'])
        self.assertTrue(all(v is None for v in history[0]['measured'].values()))

    def test_zero_is_recorded_once_and_persisted(self):
        self.update(tiktok_views=0)
        self.update(tiktok_views=0, total_revenue_yen=0)
        seed()
        p = self.status()
        self.assertEqual((p['day'], p['level'], p['xp'], p['xp_to_next_level']), (1, 1, 10, 90))
        self.assertEqual(p['first_recorded_on'], TODAY.isoformat())
        row = self.client.get('/api/metrics/latest').json()
        self.assertEqual((row['day'], row['level'], row['xp']), (1, 1, 10))
        self.assertEqual(row['measured']['tiktok_views'], 0)
        self.assertIsNone(row['measured']['youtube_views'])

    def test_missing_days_and_carried_values(self):
        self.update(tiktok_views=50)
        with patch('app.main.metrics_today', return_value=TODAY + timedelta(days=9)):
            self.assertEqual(self.status()['day'], 1)
            self.update(tiktok_followers=0)
        p = self.status()
        self.assertEqual((p['day'], p['xp']), (2, 20))
        self.assertEqual(p['last_recorded_on'], (TODAY + timedelta(days=9)).isoformat())
        rows = self.client.get('/api/metrics/history').json()
        self.assertEqual(len(rows), 2)
        self.assertIsNone(rows[0]['measured']['tiktok_views'])
        self.assertEqual(rows[0]['tiktok_views'], 50)

    def test_completion_latches_timestamp_and_xp_without_next_mission(self):
        s = self.update(total_revenue_yen=1)
        completed = s['mission']['completed_at']
        self.assertIsNotNone(completed)
        self.assertEqual((s['progression']['xp'], s['progression']['level']), (110, 2))
        s = self.update(total_revenue_yen=0)
        self.assertEqual(s['mission']['status'], 'completed')
        self.assertEqual(s['mission']['completed_at'], completed)
        self.assertEqual(s['progression']['xp'], 110)
        seed()
        self.assertEqual(len(self.client.get('/api/missions').json()), 1)

    def test_level_boundary(self):
        for offset in range(10):
            with patch('app.main.metrics_today', return_value=TODAY + timedelta(days=offset * 2)):
                self.update(tiktok_views=0)
                p = self.status()
                self.assertEqual(p['day'], offset + 1)
                self.assertEqual(p['level'], 2 if offset == 9 else 1)
        self.assertEqual((p['xp'], p['xp_to_next_level']), (100, 100))

    def test_generic_and_locked_missions_require_provenance(self):
        with SessionLocal() as db:
            db.add(Mission(code='DEFINED TEST', title='Test', metric_type='youtube_views', target_value=1))
            db.add(Mission(code='LOCKED TEST', title='Test', status='locked', metric_type='views', target_value=1))
            row = db.scalar(select(DailyMetrics))
            row.youtube_views = 500  # Unknown origin cannot award XP.
            db.commit()
        self.update(tiktok_views=1)
        missions = self.client.get('/api/missions').json()
        self.assertIsNone(missions[1]['progress'])
        self.assertEqual(missions[2]['status'], 'locked')
        self.assertEqual(self.status()['xp'], 10)

    def test_phase_three_migration_uses_only_saved_evidence(self):
        self.update(total_revenue_yen=1)
        with engine.begin() as db:
            original = db.execute(text('SELECT updated_at FROM daily_metrics')).scalar()
            for name in ('completed_at', 'completed_recorded_on'):
                db.execute(text(f'ALTER TABLE missions DROP COLUMN {name}'))
            db.execute(text('ALTER TABLE daily_metrics DROP COLUMN xp'))
        seed(); seed()
        self.assertEqual(self.status()['xp'], 110)
        self.assertEqual(self.client.get('/api/status').json()['mission']['completed_at'], original.replace(' ', 'T'))
        with engine.connect() as db:
            self.assertEqual(db.execute(text('SELECT updated_at FROM daily_metrics')).scalar(), original)
            self.assertEqual(db.execute(text('SELECT total_revenue_yen FROM daily_metrics')).scalar(), 1)

    def test_history_limit_does_not_truncate_progression(self):
        self.update(tiktok_views=0)
        with patch('app.main.metrics_today', return_value=TODAY + timedelta(days=1)):
            self.update(tiktok_views=1)
        self.assertEqual(len(self.client.get('/api/metrics/history?limit=1').json()), 1)
        self.assertEqual(self.status()['day'], 2)

    def test_generic_completion_and_invalid_targets(self):
        with SessionLocal() as db:
            db.add(Mission(code='VIEWS TEST', title='Test', metric_type='views', target_value=5))
            db.add(Mission(code='INVALID TEST', title='Test', metric_type='views', target_value=0))
            db.commit()
        self.update(tiktok_views=5)
        missions = self.client.get('/api/missions').json()
        self.assertEqual(missions[1]['status'], 'completed')
        self.assertIsNotNone(missions[1]['completed_at'])
        self.assertIsNone(missions[2]['progress'])
        self.assertIsNone(missions[2]['completed_at'])
        self.assertEqual(self.status()['xp'], 110)
        with patch('app.main.metrics_today', return_value=TODAY + timedelta(days=5)):
            s = self.update(tiktok_views=0)
        self.assertEqual(s['progression']['xp'], 120)
        rows = self.client.get('/api/metrics/history').json()
        self.assertEqual([row['xp'] for row in rows], [120, 110])

    def test_historical_completion_survives_lower_latest_record(self):
        self.update(total_revenue_yen=2)
        first = self.client.get('/api/status').json()['mission']['completed_at']
        with patch('app.main.metrics_today', return_value=TODAY + timedelta(days=2)):
            self.update(total_revenue_yen=0)
        with engine.begin() as db:
            for name in ('completed_at', 'completed_recorded_on'):
                db.execute(text(f'ALTER TABLE missions DROP COLUMN {name}'))
            db.execute(text('ALTER TABLE daily_metrics DROP COLUMN xp'))
        seed()
        s = self.client.get('/api/status').json()
        self.assertEqual(s['mission']['completed_at'], first)
        self.assertEqual(s['mission']['status'], 'completed')
        self.assertEqual(s['progression']['xp'], 120)

    def test_existing_progression_api_and_settings_table_are_preserved(self):
        with engine.begin() as db:
            db.execute(text('CREATE TABLE progression_settings (id INTEGER PRIMARY KEY, start_on DATE)'))
            db.execute(text("INSERT INTO progression_settings VALUES (1, '2020-01-01')"))
        try:
            seed()
            self.update(tiktok_views=0)
            p = self.client.get('/api/progression').json()
            self.assertEqual(p['day'], 1)  # Old calendar anchor cannot create days.
            self.assertEqual(p['xp'], 10)
            self.assertEqual(len(p['missions']), 1)
            self.assertEqual(p['history_summary']['record_count'], 1)
            row = self.client.get('/api/metrics/history').json()[0]
            self.assertEqual(row['computed_day'], 1)
            self.assertIsNone(row['delta']['tiktok_views'])
            with engine.connect() as db:
                self.assertEqual(db.execute(text('SELECT start_on FROM progression_settings')).scalar(), '2020-01-01')
        finally:
            with engine.begin() as db:
                db.execute(text('DROP TABLE progression_settings'))
