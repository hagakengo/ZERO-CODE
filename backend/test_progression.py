from datetime import date, datetime, timezone, timedelta
from unittest.mock import patch
from sqlalchemy import select, text
import unittest
import test_api
TODAY = test_api.TODAY
from app.main import DailyMetrics, Mission, ProgressionSettings, SessionLocal, engine, seed, metrics_today


class ProgressionTests(unittest.TestCase):
    setUp = test_api.ApiTests.setUp
    tearDown = test_api.ApiTests.tearDown
    update = test_api.ApiTests.update

    def test_calendar_gaps_and_no_synthetic_rows(self):
        self.update(tiktok_followers=0)
        with patch('app.main.metrics_today', return_value=TODAY + timedelta(days=4)):
            state = self.client.get('/api/progression').json()
            self.assertEqual(state['day'], 5)
            self.assertEqual(state['history_summary']['record_count'], 1)
            self.update(tiktok_followers=10)
        rows = self.client.get('/api/metrics/history').json()
        self.assertEqual([r['computed_day'] for r in rows], [5, 1])
        self.assertIsNone(rows[0]['delta']['tiktok_followers'])
        self.assertEqual(rows[0]['day'], 0)  # Legacy snapshot is preserved.

    def test_timezone_midnight(self):
        with patch('app.main.datetime') as clock:
            clock.now.side_effect = lambda zone: datetime(2026, 10, 7, 15, tzinfo=timezone.utc).astimezone(zone)
            self.assertEqual(metrics_today(), date(2026, 10, 8))
        with patch('app.main.datetime') as clock:
            clock.now.side_effect = lambda zone: datetime(2026, 10, 7, 14, 59, tzinfo=timezone.utc).astimezone(zone)
            self.assertEqual(metrics_today(), TODAY)

    def test_unobserved_counters_do_not_unlock_level(self):
        with SessionLocal() as db:
            row = db.scalar(select(DailyMetrics))
            row.total_revenue_yen, row.tiktok_followers, row.youtube_views = 100, 100, 1000
            db.commit()
        self.assertEqual(self.client.get('/api/progression').json()['calculated_level'], 0)
        self.update(total_revenue_yen=100, tiktok_followers=100)
        self.assertEqual(self.client.get('/api/progression').json()['level'], 1)
        with SessionLocal() as db:
            row = db.scalar(select(DailyMetrics))
            row.youtube_observed_on = TODAY
            db.commit()
        self.assertEqual(self.client.get('/api/progression').json()['level'], 2)
        self.update(total_revenue_yen=0)
        self.assertEqual(self.client.get('/api/progression').json()['level'], 0)

    def test_missions_only_explicit_rows_and_all_states(self):
        with SessionLocal() as db:
            db.add(Mission(code='TEST LOCKED', title='Test only', status='locked', target_value=1))
            db.add(Mission(code='TEST ACTIVE', title='Test only', metric_type='youtube_views', target_value=2000))
            db.commit()
        self.update(total_revenue_yen=1)
        state = self.client.get('/api/progression').json()
        self.assertEqual([m['status'] for m in state['missions']], ['completed', 'locked', 'active'])
        self.assertEqual(state['current_mission']['code'], 'TEST ACTIVE')
        self.assertIsNone(state['current_mission']['progress'])
        self.assertEqual(state['achievements'], {'enabled': False, 'items': []})
        seed()
        self.assertEqual(len(self.client.get('/api/missions').json()), 3)

    def test_phase_three_migration_legacy_anchor_and_idempotency(self):
        with engine.begin() as conn:
            conn.execute(text('DROP TABLE progression_settings'))
            conn.execute(text('UPDATE daily_metrics SET day=5, level=3, total_revenue_yen=42'))
        seed()
        seed()
        state = self.client.get('/api/progression').json()
        self.assertEqual(state['start_on'], (TODAY - timedelta(days=4)).isoformat())
        self.assertEqual((state['day'], state['level'], state['calculated_level']), (5, 3, 0))
        with patch('app.main.metrics_today', return_value=TODAY + timedelta(days=2)):
            self.assertEqual(self.client.get('/api/progression').json()['day'], 7)
        self.assertEqual(self.client.get('/api/metrics/latest').json()['total_revenue_yen'], 42)

    def test_explicit_start_future_day_zero_and_first_observation_migration(self):
        with engine.begin() as conn:
            conn.execute(text('DELETE FROM progression_settings'))
        with patch.dict('os.environ', {'PROGRESSION_START_DATE': '2026-10-09'}):
            seed()
        self.assertEqual(self.client.get('/api/progression').json()['day'], 0)
        with patch('app.main.metrics_today', return_value=date(2026, 10, 9)):
            self.assertEqual(self.client.get('/api/progression').json()['day'], 1)
        self.update(tiktok_views=0)
        with engine.begin() as conn:
            conn.execute(text('DROP TABLE progression_settings'))
        seed()
        self.assertEqual(self.client.get('/api/progression').json()['start_on'], TODAY.isoformat())

    def test_replaceable_rules_and_invalid_requirements(self):
        self.update(tiktok_views=50)
        rules = ({"level": 4, "requirements": {"tiktok_views": 50}},
                 {"level": 5, "requirements": {}},
                 {"level": 6, "requirements": {"unknown": 1}},
                 {"level": 7, "requirements": {"tiktok_views": 0}})
        with patch('app.main.LEVEL_RULES', rules):
            self.assertEqual(self.client.get('/api/progression').json()['level'], 4)
        self.update(total_revenue_yen=1)
        state = self.client.get('/api/progression').json()
        self.assertIsNone(state['current_mission'])
        self.assertEqual(len(state['missions']), 1)
