import os
import unittest
from unittest.mock import patch

import test_api  # isolated SQLite DATABASE_URL before app import
from fastapi.testclient import TestClient
from app.main import app


class WriteAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

    def test_missing_configuration_fails_closed(self):
        with patch.dict(os.environ, {"ZERO_CODE_WRITE_TOKEN": ""}):
            for method, url, payload in (
                ("PATCH", "/api/metrics/manual", {"tiktok_views": 1}),
                ("POST", "/api/integrations/youtube/sync", None),
                ("POST", "/api/integrations/buffer/schedule",
                 {"text": "test", "scheduled_at": "2099-01-01T00:00:00Z"}),
            ):
                with self.subTest(url=url):
                    response = self.client.request(method, url, json=payload)
                    self.assertEqual(response.status_code, 503, response.text)

    def test_missing_wrong_and_malformed_tokens_are_rejected(self):
        with patch.dict(os.environ, {"ZERO_CODE_WRITE_TOKEN": "expected-test-token"}):
            for headers in ({}, {"Authorization": "Bearer wrong"},
                            {"Authorization": "Basic expected-test-token"},
                            {"Authorization": "Bearer"}):
                for url in ("/api/metrics/manual", "/api/integrations/youtube/sync",
                            "/api/integrations/buffer/schedule"):
                    with self.subTest(url=url, headers=headers):
                        response = self.client.post(url, headers=headers, json={})
                        self.assertEqual(response.status_code, 401, response.text)
                        self.assertEqual(response.headers["www-authenticate"], "Bearer")

    def test_read_only_health_still_accessible(self):
        with patch.dict(os.environ, {"ZERO_CODE_WRITE_TOKEN": ""}):
            self.assertEqual(self.client.get("/health").status_code, 200)


if __name__ == "__main__":
    unittest.main()
