import os
import unittest
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
import test_api
from app.main import app
from app import buffer


class BufferTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {
            "BUFFER_API_KEY": "test-secret", "BUFFER_X_CHANNEL_ID": "",
            "SNS_WRITE_TOKEN": "sns-test-token",
        })
        self.env.start()
        self.client = TestClient(app)
        self.calls = []
        self.service = "twitter"
        self.failure = None
        self.posts = []
        self.mock = patch.object(buffer.httpx, "post", side_effect=self.respond)
        self.mock.start()

    def tearDown(self):
        self.mock.stop()
        self.env.stop()
        self.client.close()

    def respond(self, url, **kwargs):
        self.assertEqual(url, "https://api.buffer.com")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-secret")
        q = kwargs["json"]["query"]
        self.calls.append(q)
        if self.failure == "auth":
            return httpx.Response(401, request=httpx.Request("POST", url), json={"secret": "test-secret"})
        if self.failure == "graphql":
            data = {"errors": [{"message": "test-secret"}]}
        elif "organizations" in q:
            data = {"data": {"account": {"organizations": [{"id": "org"}]}}}
        elif "channels(input" in q:
            data = {"data": {"channels": [{"id": "channel", "service": self.service}]}}
        elif "posts(" in q:
            data = {"data": {"posts": {"edges": [{"node": value} for value in self.posts],
                                       "pageInfo": {"hasNextPage": False, "endCursor": None}}}}
        elif self.failure == "mutation":
            data = {"data": {"createPost": {"message": "test-secret"}}}
        else:
            data = {"data": {"createPost": {"post": {"id": "post123"}}}}
        return httpx.Response(200, request=httpx.Request("POST", url), json=data)

    def schedule(self, **changes):
        return self.client.post("/api/integrations/buffer/schedule",
                                headers={"X-ZCS-SNS-Token": "sns-test-token"}, json={
            "text": 'Hello "X"', "scheduled_at": "2099-01-01T12:00:00+09:00", **changes})

    def test_missing_and_invalid_token_are_rejected_without_buffer_writes(self):
        payload = {"text": "hi", "scheduled_at": "2099-01-01T00:00:00Z", "dry_run": False}
        missing = self.client.post("/api/integrations/buffer/schedule", json=payload)
        invalid = self.client.post("/api/integrations/buffer/schedule",
                                   headers={"X-ZCS-SNS-Token": "wrong-token"}, json=payload)
        self.assertEqual(missing.status_code, 401)
        self.assertEqual(invalid.status_code, 401)
        self.assertEqual(self.calls, [])

    def test_valid_token_dry_run_does_not_write(self):
        result = self.schedule(dry_run=True)
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json()["dry_run"])
        self.assertFalse(any("mutation" in query for query in self.calls))

    def test_unconfigured(self):
        os.environ["BUFFER_API_KEY"] = ""
        self.assertFalse(self.client.get("/api/integrations/buffer/status").json()["configured"])
        self.assertEqual(self.schedule().status_code, 409)
        self.assertEqual(self.calls, [])

    def test_auth_failure(self):
        self.failure = "auth"
        result = self.client.get("/api/integrations/buffer/status")
        self.assertFalse(result.json()["connected"])
        self.assertNotIn("test-secret", result.text)

    def test_no_x(self):
        self.service = "instagram"
        result = self.client.get("/api/integrations/buffer/status").json()
        self.assertTrue(result["connected"])
        self.assertFalse(result["x_channel_available"])
        self.assertEqual(self.schedule(dry_run=False).status_code, 502)
        self.assertFalse(any("mutation" in q for q in self.calls))

    def test_dry_run_default_and_explicit(self):
        for payload in ({}, {"dry_run": True}):
            result = self.schedule(**payload)
            self.assertEqual(result.status_code, 200)
            self.assertTrue(result.json()["dry_run"])
            self.assertEqual(result.json()["scheduled_at"], "2099-01-01T03:00:00Z")
        self.assertFalse(any("mutation" in q for q in self.calls))

    def test_success(self):
        result = self.schedule(dry_run=False)
        self.assertEqual(result.json()["post_id"], "post123")
        query = self.calls[-1]
        self.assertIn("mode: customScheduled", query)
        self.assertIn("schedulingType: automatic", query)
        self.assertNotIn("thread", query)
        self.assertNotIn("shareNow", query)

    def test_duplicate_is_not_created(self):
        self.posts = [{"id": "already", "text": 'Hello "X"',
                       "dueAt": "2099-01-01T03:00:00Z", "channelId": "channel",
                       "externalLink": None}]
        result = self.schedule(dry_run=False)
        self.assertEqual(result.json()["post_id"], "already")
        self.assertTrue(result.json()["duplicate"])
        self.assertFalse(any("mutation" in q for q in self.calls))

    def test_posts_filter_is_scoped(self):
        buffer.posts("channel", ("scheduled", "sent"))
        query = self.calls[-1]
        self.assertIn("status: [scheduled, sent]", query)
        self.assertIn('channelIds: ["channel"]', query)
        self.assertIn("externalLink", query)

    def test_errors_are_safe(self):
        for failure in ("graphql", "mutation"):
            self.failure = failure
            result = self.schedule(dry_run=False)
            self.assertEqual(result.status_code, 502)
            self.assertNotIn("test-secret", result.text)
        with patch.object(buffer.httpx, "post", side_effect=RuntimeError("test-secret")):
            self.assertNotIn("test-secret", self.schedule().text)

    def test_validation_before_network(self):
        for payload in ({"text": " "}, {"text": "あ" * 141}, {"scheduled_at": "2000-01-01T00:00:00Z"},
                        {"scheduled_at": "2099-01-01T00:00:00"}, {"dry_run": "false"}, {"channel_id": "other"}):
            self.assertEqual(self.schedule(**payload).status_code, 422)
        self.assertEqual(self.calls, [])

    def test_channel_selection(self):
        items = [{"id": "a", "service": "twitter"}, {"id": "b", "service": "twitter"}]
        with self.assertRaises(buffer.BufferError):
            buffer.resolve_x(items)
        os.environ["BUFFER_X_CHANNEL_ID"] = "b"
        self.assertEqual(buffer.resolve_x(items), "b")
        with self.assertRaises(buffer.BufferError):
            buffer.resolve_x([{"id": "b", "service": "instagram"}])

    def test_origin(self):
        result = self.client.post("/api/integrations/buffer/schedule",
                                  json={"text": "hi", "scheduled_at": "2099-01-01T00:00:00Z",
                                        "dry_run": False},
                                  headers={"Origin": "https://evil.example",
                                           "X-ZCS-SNS-Token": "sns-test-token"})
        self.assertEqual(result.status_code, 403)
        self.assertEqual(self.calls, [])
