import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from unittest.mock import patch

temporary_db = tempfile.TemporaryDirectory()
os.environ['DATABASE_URL'] = f'sqlite:///{temporary_db.name}/test.db'

from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from app.main import Base, DailyMetrics, Mission, SessionLocal, app, engine, seed

TODAY = date(2026, 10, 7)


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.clock = patch('app.main.metrics_today', return_value=TODAY)
        self.clock.start()
        Base.metadata.drop_all(engine)
        seed()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.clock.stop()

    def update(self, **values):
        response = self.client.patch('/api/metrics/manual', json=values)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_health(self):
        self.assertEqual(self.client.get('/health').json(), {'status': 'ok'})

    def test_initial_status_and_idempotent_seed(self):
        seed()
        data = self.client.get('/api/status').json()
        self.assertEqual((data['day'], data['level'], data['total_revenue_yen']), (0, 0, 0))
        self.assertEqual(data['youtube'], {'subscribers': 0, 'views': 0})
        self.assertEqual(data['tiktok'], {'followers': 0, 'views': 0})
        self.assertEqual(data['mission']['progress'], None)
        self.assertEqual(data['mission']['metric_type'], 'revenue')
        self.assertEqual(data['mission']['target_value'], 1)
        self.assertTrue(all(value is None for value in data['observed_on'].values()))
        self.assertIsNone(data['delta']['total_revenue_yen'])
        with SessionLocal() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(DailyMetrics)), 1)
            self.assertEqual(db.scalar(select(func.count()).select_from(Mission)), 1)

    def test_same_day_partial_update_zero_and_persistence(self):
        data = self.update(tiktok_followers=12, tiktok_views=34, total_revenue_yen=1)
        self.assertEqual(data['mission']['status'], 'completed')
        data = self.update(tiktok_followers=0)
        self.assertEqual(data['tiktok'], {'followers': 0, 'views': 34})
        seed()
        self.assertEqual(self.client.get('/api/status').json(), data)
        self.assertEqual(len(self.client.get('/api/metrics/history').json()), 1)
        self.assertEqual(self.client.get('/api/missions').json()[0], data['mission'])
        self.assertEqual(self.update(total_revenue_yen=0)['mission']['status'], 'completed')

    def test_rollover_deltas_and_history(self):
        self.update(tiktok_followers=12, tiktok_views=100, total_revenue_yen=0)
        with SessionLocal() as db:
            row = db.scalar(select(DailyMetrics))
            row.day, row.level = 3, 2
            row.youtube_subscribers, row.youtube_views = 7, 40
            row.youtube_observed_on = TODAY
            db.commit()
        with patch('app.main.metrics_today', return_value=TODAY + timedelta(days=1)):
            data = self.update(tiktok_followers=10, tiktok_views=120, total_revenue_yen=5)
            self.assertEqual(data['delta']['tiktok'], {'followers': -2, 'views': 20})
            self.assertEqual(data['delta']['total_revenue_yen'], 5)
            self.assertIsNone(data['delta']['youtube']['views'])  # Carried != newly observed.
            self.assertEqual(data['youtube'], {'subscribers': 7, 'views': 40})
            self.assertEqual((data['day'], data['level']), (2, 2))
            self.update(total_revenue_yen=6)
        history = self.client.get('/api/metrics/history').json()
        self.assertEqual([r['date'] for r in history], ['2026-10-08', '2026-10-07'])
        self.assertEqual([r['total_revenue_yen'] for r in history], [6, 0])
        self.assertEqual(self.client.get('/api/metrics/latest').json(), history[0])
        self.assertEqual(len(self.client.get('/api/metrics/history?limit=1').json()), 1)

    def test_missing_day_and_omitted_observation(self):
        self.update(tiktok_followers=10, total_revenue_yen=5)
        with patch('app.main.metrics_today', return_value=TODAY + timedelta(days=2)):
            data = self.update(tiktok_views=100)
            self.assertIsNone(data['delta']['tiktok']['views'])
            self.assertEqual(data['observed_on']['tiktok_followers'], TODAY.isoformat())
            self.assertEqual(data['tiktok']['followers'], 10)
        with patch('app.main.metrics_today', return_value=TODAY + timedelta(days=3)):
            data = self.update(tiktok_followers=11, tiktok_views=100)
            self.assertIsNone(data['delta']['tiktok']['followers'])
            self.assertEqual(data['delta']['tiktok']['views'], 0)
        self.assertEqual(len(self.client.get('/api/metrics/history').json()), 3)

    def test_youtube_delta_when_both_observed(self):
        with SessionLocal() as db:
            row = db.scalar(select(DailyMetrics))
            row.youtube_observed_on = TODAY
            row.youtube_subscribers, row.youtube_views = 10, 100
            db.add(DailyMetrics(date=TODAY + timedelta(days=1), youtube_observed_on=TODAY + timedelta(days=1),
                                youtube_subscribers=9, youtube_views=150))
            db.commit()
        self.assertEqual(self.client.get('/api/status').json()['delta']['youtube'], {'subscribers': -1, 'views': 50})

    def test_validation_does_not_write(self):
        before = self.client.get('/api/metrics/history').json()
        for payload in ({}, {'total_revenue_yen': None}, {'tiktok_views': -1}, {'tiktok_views': 1.2},
                        {'tiktok_views': True}, {'tiktok_views': '3'}, {'youtube_views': 100},
                        {'date': '2026-10-08'}, {'total_revenue_yen': 9007199254740992}):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post('/api/metrics/manual', json=payload).status_code, 422)
        self.assertEqual(self.client.get('/api/metrics/history').json(), before)
        for limit in ('0', '367', 'invalid'):
            self.assertEqual(self.client.get(f'/api/metrics/history?limit={limit}').status_code, 422)

    def test_generic_mission_and_safe_invalid_target(self):
        with SessionLocal() as db:
            mission = db.scalar(select(Mission))
            mission.target_value = 100
            db.commit()
        self.assertEqual(self.update(total_revenue_yen=25)['mission']['progress'], 25)
        self.assertEqual(self.update(total_revenue_yen=200)['mission']['progress'], 100)
        with SessionLocal() as db:
            mission = db.scalar(select(Mission))
            mission.metric_type = 'followers'
            db.commit()
        self.assertEqual(self.update(tiktok_followers=50)['mission']['progress'], 100)
        with SessionLocal() as db:
            mission = db.scalar(select(Mission))
            mission.target_value = 0
            db.commit()
        self.assertEqual(self.client.get('/api/status').json()['mission']['progress'], 100)

    def test_concurrent_rollover_keeps_both_updates(self):
        with patch('app.main.metrics_today', return_value=TODAY + timedelta(days=1)):
            def send(payload):
                with TestClient(app) as client:
                    return client.post('/api/metrics/manual', json=payload).status_code
            with ThreadPoolExecutor(max_workers=2) as pool:
                codes = list(pool.map(send, [{'tiktok_followers': 4}, {'total_revenue_yen': 2}]))
            self.assertEqual(codes, [200, 200])
        data = self.client.get('/api/status').json()
        self.assertEqual((data['tiktok']['followers'], data['total_revenue_yen']), (4, 2))
        self.assertEqual(len(self.client.get('/api/metrics/history').json()), 2)

    def test_phase_one_migration_preserves_data(self):
        # Reconstruct the actual Phase 1 schema by removing only new columns.
        with engine.begin() as connection:
            for column in ('metric_type', 'target_value'):
                connection.execute(text(f'ALTER TABLE missions DROP COLUMN {column}'))
            for column in ('youtube_observed_on', 'tiktok_followers_observed_on',
                           'tiktok_views_observed_on', 'total_revenue_yen_observed_on'):
                connection.execute(text(f'ALTER TABLE daily_metrics DROP COLUMN {column}'))
            connection.execute(text('UPDATE daily_metrics SET total_revenue_yen=42, day=5, level=2'))
        seed()
        seed()
        data = self.client.get('/api/status').json()
        self.assertEqual((data['total_revenue_yen'], data['day'], data['level']), (42, 0, 0))
        self.assertEqual(data['mission']['progress'], None)
        self.assertIsNone(data['observed_on']['total_revenue_yen'])
        self.assertEqual(len(self.client.get('/api/metrics/history').json()), 1)


if __name__ == '__main__':
    unittest.main()
