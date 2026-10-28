import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from unittest.mock import patch

import test_api
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app import sns_ops
from app.main import Base, SessionLocal, SocialPost, SocialPostAttempt, app, engine, seed


ENTRY = {
    "title": "ZERO CODE制作記録",
    "url": "https://note.com/sora199312/n/nabc123",
    "summary": "公開済みの通常記事",
}


class SnsHelperTests(unittest.TestCase):
    def test_rss_and_url_validation(self):
        xml = """<rss><channel><item><title>Article</title>
        <link>https://note.com/sora199312/n/nabc123?x=1</link>
        <description>summary</description></item></channel></rss>"""
        self.assertEqual(sns_ops.parse_note_rss(xml)[0]["url"], ENTRY["url"])
        with self.assertRaises(ValueError):
            sns_ops.canonical_note_url("https://example.com/private")

    def test_schedule_and_hold_policy(self):
        start = datetime.fromisoformat("2026-10-27T21:00:00+09:00")
        first = sns_ops.next_slot(start, set())
        self.assertEqual(first.isoformat(), "2026-10-28T20:00:00+09:00")
        second = sns_ops.next_slot(start, {first})
        self.assertEqual(second.isoformat(), "2026-10-30T20:00:00+09:00")
        self.assertFalse(sns_ops.normal_announcement("未公開キャラクター設定"))


class SnsApiTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.drop_all(engine)
        seed()
        self.client = TestClient(app)
        self.feed = patch("app.sns_ops.fetch_note_rss", return_value=[ENTRY])
        self.feed.start()
        self.env = patch.dict("os.environ", {
            "NOTE_RSS_URL": "https://note.com/sora199312/rss",
            "SNS_WRITE_TOKEN": "sns-test-token",
            "BUFFER_API_KEY": "buffer-test-key",
        })
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.feed.stop()
        self.client.close()

    def reconcile(self, dry_run=False):
        return self.client.post("/api/sns/reconcile",
                                headers={"X-ZCS-SNS-Token": "sns-test-token"}, json={
            "dry_run": dry_run, "now": "2026-10-27T21:00:00+09:00"})

    def list_posts(self):
        return self.client.get("/api/sns/posts",
                               headers={"X-ZCS-SNS-Token": "sns-test-token"})

    def test_dry_run_does_not_write(self):
        result = self.reconcile(dry_run=True)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["actions"][0]["status"], "READY")
        with SessionLocal() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(SocialPost)), 0)

    def test_automation_defaults_fail_closed(self):
        result = self.client.post("/api/sns/reconcile",
                                  headers={"X-ZCS-SNS-Token": "sns-test-token"},
                                  json={"dry_run": False, "automation": True})
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json()["dry_run"])
        self.assertFalse(result.json()["auto_schedule_enabled"])
        refresh = self.client.post("/api/sns/refresh?automation=true",
                                   headers={"X-ZCS-SNS-Token": "sns-test-token"})
        self.assertEqual(refresh.status_code, 200)
        self.assertTrue(refresh.json()["skipped"])

    def test_automation_requires_explicit_enable_flag(self):
        response = {"post_id": "buffer-auto", "duplicate": False,
                    "scheduled_at": "2026-10-28T11:00:00Z"}
        with patch.dict("os.environ", {"SNS_AUTO_SCHEDULE_ENABLED": "1"}), \
                patch("app.buffer.schedule_post", return_value=response):
            result = self.client.post("/api/sns/reconcile",
                                      headers={"X-ZCS-SNS-Token": "sns-test-token"},
                                      json={"dry_run": False, "automation": True})
        self.assertFalse(result.json()["dry_run"])
        self.assertEqual(result.json()["actions"][0]["status"], "SCHEDULED")

    def test_success_is_persistent_and_idempotent(self):
        response = {"post_id": "buffer-1", "duplicate": False,
                    "scheduled_at": "2026-10-28T11:00:00Z"}
        with patch("app.buffer.schedule_post", return_value=response) as schedule:
            first = self.reconcile()
            second = self.reconcile()
        self.assertEqual(first.json()["actions"][0]["status"], "SCHEDULED")
        self.assertEqual(second.json()["actions"][0]["action"], "existing")
        self.assertEqual(schedule.call_count, 1)
        rows = self.list_posts().json()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["buffer_post_id"], "buffer-1")

    def test_buffer_failure_is_not_scheduled(self):
        from app.buffer import BufferError
        with patch("app.buffer.schedule_post", side_effect=BufferError("Buffer is unavailable.")):
            result = self.reconcile()
        self.assertEqual(result.json()["actions"][0]["status"], "FAILED")
        self.assertEqual(self.list_posts().json()[0]["status"], "FAILED")

    def test_sensitive_article_is_held_without_buffer_call(self):
        sensitive = {**ENTRY, "title": "未公開キャラクター設定"}
        with patch("app.sns_ops.fetch_note_rss", return_value=[sensitive]), \
                patch("app.buffer.schedule_post") as schedule:
            result = self.reconcile()
        self.assertEqual(result.json()["actions"][0]["status"], "HOLD")
        schedule.assert_not_called()

    def test_published_requires_x_evidence(self):
        with patch("app.buffer.schedule_post", return_value={
            "post_id": "buffer-1", "duplicate": False, "scheduled_at": "x"}):
            self.reconcile()
        headers = {"X-ZCS-SNS-Token": "sns-test-token"}
        invalid = self.client.post("/api/sns/posts/NOTE-nabc123/confirm-published", headers=headers, json={
            "x_public_url": "https://example.com/fake", "published_at": "2026-10-28T20:01:00+09:00"})
        self.assertEqual(invalid.status_code, 422)
        valid = self.client.post("/api/sns/posts/NOTE-nabc123/confirm-published", headers=headers, json={
            "x_public_url": "https://x.com/sora1993xny/status/123456",
            "published_at": "2026-10-28T20:01:00+09:00"})
        self.assertEqual(valid.json()["status"], "PUBLISHED")

    def test_foreign_origin_is_rejected(self):
        result = self.client.post("/api/sns/reconcile", headers={
            "Origin": "https://evil.example", "X-ZCS-SNS-Token": "sns-test-token"},
                                  json={"dry_run": True})
        self.assertEqual(result.status_code, 403)

    def test_missing_write_token_is_rejected(self):
        result = self.client.post("/api/sns/reconcile", json={"dry_run": True})
        self.assertEqual(result.status_code, 401)
        self.assertEqual(self.client.get("/api/sns/posts").status_code, 401)

    def test_unconfigured_buffer_holds_safely(self):
        with patch.dict("os.environ", {"BUFFER_API_KEY": ""}):
            result = self.reconcile()
        self.assertEqual(result.json()["actions"][0]["status"], "HOLD")

    def test_concurrent_detection_creates_one_row(self):
        response = {"post_id": "buffer-1", "duplicate": False,
                    "scheduled_at": "2026-10-28T11:00:00Z"}
        with patch("app.buffer.schedule_post", return_value=response) as schedule:
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: self.reconcile(), range(2)))
        self.assertTrue(all(result.status_code == 200 for result in results))
        self.assertEqual(schedule.call_count, 1)
        self.assertEqual(len(self.list_posts().json()), 1)

    def test_sent_buffer_post_is_not_published_without_x_url(self):
        with patch("app.buffer.schedule_post", return_value={
            "post_id": "buffer-1", "duplicate": False, "scheduled_at": "x"}):
            self.reconcile()
        sent = [{"id": "buffer-1", "text": "x", "dueAt": "x", "channelId": "channel",
                 "externalLink": None}]
        def posts(_channel, statuses):
            return sent if statuses == ("sent",) else []
        headers = {"X-ZCS-SNS-Token": "sns-test-token"}
        with patch("app.buffer.channels", return_value=[{"id": "channel", "service": "twitter"}]), \
                patch("app.buffer.posts", side_effect=posts):
            result = self.client.post("/api/sns/refresh", headers=headers)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["posts"][0]["status"], "SCHEDULED")
        self.assertIn("X URL", result.json()["posts"][0]["error"])

    def test_sent_buffer_post_is_published_with_verified_x_url(self):
        with patch("app.buffer.schedule_post", return_value={
            "post_id": "buffer-1", "duplicate": False, "scheduled_at": "x"}):
            self.reconcile()
        sent = [{"id": "buffer-1", "text": "x", "dueAt": "x", "channelId": "channel",
                 "externalLink": "https://x.com/sora1993xny/status/123456"}]
        def posts(_channel, statuses):
            return sent if statuses == ("sent",) else []
        headers = {"X-ZCS-SNS-Token": "sns-test-token"}
        with patch("app.buffer.channels", return_value=[{"id": "channel", "service": "twitter"}]), \
                patch("app.buffer.posts", side_effect=posts):
            result = self.client.post("/api/sns/refresh", headers=headers)
        post = result.json()["posts"][0]
        self.assertEqual(post["status"], "PUBLISHED")
        self.assertEqual(post["x_public_url"], sent[0]["externalLink"])

    def test_attempt_history_is_recorded(self):
        with patch("app.buffer.schedule_post", return_value={
            "post_id": "buffer-1", "duplicate": False, "scheduled_at": "x"}):
            self.reconcile()
        with SessionLocal() as db:
            attempts = list(db.scalars(select(SocialPostAttempt)))
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0].outcome, "SCHEDULED")

    def test_retry_uses_buffer_dedup_result(self):
        from app.buffer import BufferError
        with patch("app.buffer.schedule_post", side_effect=BufferError("timeout")):
            self.reconcile()
        headers = {"X-ZCS-SNS-Token": "sns-test-token"}
        with patch("app.buffer.schedule_post", return_value={
            "post_id": "buffer-existing", "duplicate": True, "scheduled_at": "x"}):
            result = self.client.post("/api/sns/posts/NOTE-nabc123/retry", headers=headers)
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json()["duplicate"])
        self.assertEqual(result.json()["status"], "SCHEDULED")


if __name__ == "__main__":
    unittest.main()
