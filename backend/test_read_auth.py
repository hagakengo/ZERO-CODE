import os
import unittest
from unittest.mock import patch

import test_api  # configure disposable SQLite before app import
from fastapi.testclient import TestClient
from app.main import app


class DashboardReadAuthorizationTests(unittest.TestCase):
    PATHS = (
        "/api/status",
        "/api/metrics/latest",
        "/api/metrics/history",
        "/api/missions",
        "/api/integrations/youtube/status",
        "/api/integrations/buffer/status",
        "/api/progression",
    )

    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

    def test_read_endpoints_reject_unauthenticated_access(self):
        with patch.dict(os.environ, {"ZERO_CODE_WRITE_TOKEN": "test-write", "ZERO_CODE_READ_TOKEN": "test-read"}):
            for path in self.PATHS:
                with self.subTest(path=path):
                    self.assertEqual(self.client.get(path).status_code, 401)
                    self.assertEqual(self.client.get(path, headers={"Authorization": "Bearer invalid"}).status_code, 401)

    def test_read_endpoints_fail_closed_without_configuration(self):
        with patch.dict(os.environ, {"ZERO_CODE_WRITE_TOKEN": "", "ZERO_CODE_READ_TOKEN": ""}):
            for path in self.PATHS:
                with self.subTest(path=path):
                    self.assertEqual(self.client.get(path).status_code, 503)

    def test_operator_token_can_read_and_read_only_token_cannot_write(self):
        with patch.dict(os.environ, {"ZERO_CODE_WRITE_TOKEN": "test-write", "ZERO_CODE_READ_TOKEN": "test-read"}):
            for token in ("test-write", "test-read"):
                for path in self.PATHS:
                    with self.subTest(path=path, token=token):
                        response = self.client.get(path, headers={"Authorization": f"Bearer {token}"})
                        self.assertEqual(response.status_code, 200, response.text)
            response = self.client.patch(
                "/api/metrics/manual",
                json={"tiktok_views": 123},
                headers={"Authorization": "Bearer test-read"},
            )
            self.assertEqual(response.status_code, 401)

    def test_health_remains_public(self):
        self.assertEqual(self.client.get("/health").status_code, 200)


if __name__ == "__main__":
    unittest.main()
