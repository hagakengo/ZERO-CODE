import unittest
from unittest.mock import patch
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
import httpx
import test_api
from test_api import TODAY
from app import youtube
from app.main import SessionLocal, Mission, engine, seed, sync_lock
from sqlalchemy import select, text

CONFIG = {'YOUTUBE_CLIENT_ID': 'id', 'YOUTUBE_CLIENT_SECRET': 'secret', 'YOUTUBE_REFRESH_TOKEN': 'refresh', 'YOUTUBE_CHANNEL_ID': 'channel'}
VALUES = {'youtube_subscribers': 12, 'youtube_views': 100}

class SyncTests(unittest.TestCase):
    setUp = test_api.ApiTests.setUp
    tearDown = test_api.ApiTests.tearDown
    update = test_api.ApiTests.update

    def sync(self):
        return self.client.post('/api/integrations/youtube/sync')

    def test_disconnected_and_unknown_mission(self):
        with SessionLocal() as db:
            mission = db.scalar(select(Mission))
            mission.metric_type = 'youtube_views'
            db.commit()
        before = self.client.get('/api/metrics/history').json()
        with patch.object(youtube, 'settings', return_value={}):
            self.assertEqual(self.sync().status_code, 409)
            self.assertEqual(self.client.get('/api/integrations/youtube/status').json()['state'], 'disconnected')
        self.assertEqual(self.client.get('/api/metrics/history').json(), before)
        self.assertIsNone(self.client.get('/api/status').json()['mission']['progress'])

    @patch.object(youtube, 'settings', return_value=CONFIG)
    @patch.object(youtube, 'fetch_metrics', return_value=(VALUES, None))
    def test_sync_persistence_rollover_mission(self, fetch, config):
        self.update(tiktok_followers=5, total_revenue_yen=2)
        with SessionLocal() as db:
            mission = db.scalar(select(Mission))
            mission.metric_type, mission.target_value = 'youtube_views', 200
            db.commit()
        result = self.sync().json()
        self.assertEqual(result['status']['mission']['progress'], 50)
        self.assertEqual(result['integration']['state'], 'connected')
        self.assertEqual(result['status']['observed_on']['youtube'], TODAY.isoformat())
        self.assertEqual(self.sync().status_code, 200)
        self.assertEqual(len(self.client.get('/api/metrics/history').json()), 1)
        with patch('app.main.metrics_today', return_value=TODAY+timedelta(days=1)):
            result = self.sync().json()['status']
            self.assertEqual(result['delta']['youtube'], {'subscribers': 0, 'views': 0})
            self.assertEqual(result['tiktok']['followers'], 5)
            self.assertEqual(result['total_revenue_yen'], 2)
        seed()
        self.assertEqual(len(self.client.get('/api/metrics/history').json()), 2)
        self.assertEqual(self.client.get('/api/integrations/youtube/status').json()['state'], 'connected')

    @patch.object(youtube, 'settings', return_value=CONFIG)
    def test_failure_preserves_and_recovers(self, config):
        with patch.object(youtube, 'fetch_metrics', return_value=(VALUES, None)):
            self.sync()
        before = self.client.get('/api/metrics/history').json()
        last = self.client.get('/api/integrations/youtube/status').json()['last_synced_at']
        with patch.object(youtube, 'fetch_metrics', side_effect=youtube.YouTubeError('API failed')):
            self.assertEqual(self.sync().status_code, 502)
        self.assertEqual(self.client.get('/api/metrics/history').json(), before)
        status = self.client.get('/api/integrations/youtube/status').json()
        self.assertEqual(status['state'], 'error')
        self.assertEqual(status['last_synced_at'], last)
        with patch.object(youtube, 'fetch_metrics', return_value=(VALUES, None)):
            self.assertEqual(self.sync().json()['integration']['state'], 'connected')

    @patch.object(youtube, 'settings', return_value=CONFIG)
    def test_analytics_preserved_on_failure(self, config):
        full = {**VALUES, 'youtube_watch_minutes': 30, 'youtube_likes': 4, 'youtube_comments': 1,
                'youtube_analytics_observed_on': TODAY, 'youtube_analytics_start_on': TODAY-timedelta(days=5),
                'youtube_analytics_end_on': TODAY-timedelta(days=1)}
        with patch.object(youtube, 'fetch_metrics', return_value=(full, None)):
            self.sync()
        with patch('app.main.metrics_today', return_value=TODAY+timedelta(days=1)), patch.object(youtube, 'fetch_metrics', return_value=(VALUES, 'Unavailable')):
            self.assertEqual(self.sync().json()['integration']['warning'], 'Unavailable')
        row = self.client.get('/api/metrics/latest').json()
        self.assertEqual(row['youtube_watch_minutes'], 30)
        self.assertEqual(row['observed_on']['youtube_analytics'], TODAY.isoformat())

    @patch.object(youtube, 'settings', return_value=CONFIG)
    @patch.object(youtube, 'fetch_metrics', return_value=(VALUES, None))
    def test_concurrent_manual_sync(self, fetch, config):
        with patch('app.main.metrics_today', return_value=TODAY+timedelta(days=1)):
            with ThreadPoolExecutor(max_workers=2) as pool:
                sync = pool.submit(self.sync)
                manual = pool.submit(self.client.patch, '/api/metrics/manual', json={'tiktok_views': 45})
                self.assertEqual(sync.result().status_code, 200)
                self.assertEqual(manual.result().status_code, 200)
        data = self.client.get('/api/status').json()
        self.assertEqual(data['tiktok']['views'], 45)
        self.assertEqual(data['youtube']['views'], 100)

    @patch.object(youtube, 'settings', return_value=CONFIG)
    def test_security_and_busy(self, config):
        self.assertEqual(self.client.post('/api/integrations/youtube/sync', headers={'Origin': 'https://evil.example'}).status_code, 403)
        with sync_lock:
            self.assertEqual(self.sync().status_code, 409)

    def test_phase_two_migration(self):
        self.update(total_revenue_yen=7)
        with engine.begin() as db:
            db.execute(text('DROP TABLE youtube_integration'))
            for field in ('youtube_analytics_observed_on', 'youtube_analytics_start_on', 'youtube_analytics_end_on'):
                db.execute(text(f'ALTER TABLE daily_metrics DROP COLUMN {field}'))
        seed(); seed()
        self.assertEqual(self.client.get('/api/status').json()['total_revenue_yen'], 7)

class ServiceTests(unittest.TestCase):
    def run_api(self, mode=None):
        calls = []
        def handler(request):
            calls.append(request)
            if request.url.host == 'oauth2.googleapis.com':
                return httpx.Response(400, json={'error': 'secret'}) if mode == 'auth' else httpx.Response(200, json={'access_token': 'access'})
            self.assertEqual(request.headers['Authorization'], 'Bearer access')
            if request.url.host == 'www.googleapis.com':
                if mode == 'timeout':
                    raise httpx.ReadTimeout('secret', request=request)
                if mode in (403, 429, 500):
                    return httpx.Response(mode, json={'error': 'secret'})
                stats = {'subscriberCount': '0', 'viewCount': '123'}
                if mode == 'missing': del stats['subscriberCount']
                if mode == 'hidden': stats['hiddenSubscriberCount'] = True
                if mode == 'invalid': stats['viewCount'] = '-2'
                return httpx.Response(200, json={'items': [] if mode == 'empty' else [
                    {'id': 'other' if mode == 'wrong' else 'channel', 'statistics': stats}]})
            if mode == 'analytics': return httpx.Response(403, json={'error': 'secret'})
            return httpx.Response(200, json={'columnHeaders': [{'name': k} for k in ['estimatedMinutesWatched', 'likes', 'comments']],
                'rows': [] if mode == 'no_rows' else [[30, 4, 0]]})
        client = httpx.Client(transport=httpx.MockTransport(handler))
        with patch.object(youtube, 'settings', return_value=CONFIG), patch.object(youtube.httpx, 'Client', return_value=client):
            return youtube.fetch_metrics(TODAY), calls

    def test_success_and_real_zero(self):
        (values, warning), calls = self.run_api()
        self.assertEqual(values['youtube_subscribers'], 0)
        self.assertEqual(values['youtube_watch_minutes'], 30)
        self.assertEqual(values['youtube_analytics_end_on'], TODAY-timedelta(days=1))
        self.assertIsNone(warning)
        self.assertIn('grant_type=refresh_token', calls[0].content.decode())
        self.assertEqual(calls[1].url.params['mine'], 'true')

    def test_required_errors_sanitized(self):
        for mode in ('auth', 'timeout', 403, 429, 500, 'missing', 'hidden', 'invalid', 'empty', 'wrong'):
            with self.subTest(mode=mode):
                with self.assertRaises(youtube.YouTubeError) as raised:
                    self.run_api(mode)
                self.assertNotIn('secret', str(raised.exception))

    def test_optional_analytics_failure(self):
        for mode in ('analytics', 'no_rows'):
            (values, warning), _ = self.run_api(mode)
            self.assertEqual(values, {'youtube_subscribers': 0, 'youtube_views': 123})
            self.assertTrue(warning)
