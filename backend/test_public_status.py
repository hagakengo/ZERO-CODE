import os
import unittest
from unittest.mock import patch

import test_api  # configures isolated DATABASE_URL before importing app.main
from fastapi.testclient import TestClient
from app.main import app


class PublicStatusTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"ZERO_CODE_READ_TOKEN": "read-secret"})
        self.env.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.env.stop()

    def test_requires_bearer_token(self):
        self.assertEqual(self.client.get("/api/public/status").status_code, 401)
        self.assertEqual(
            self.client.get("/api/public/status", headers={"Authorization": "Bearer wrong"}).status_code,
            401,
        )

    def test_returns_safe_snapshot(self):
        response = self.client.get(
            "/api/public/status",
            headers={"Authorization": "Bearer read-secret"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        self.assertIn("progression", data)
        self.assertIn("mission", data)
        self.assertIn("youtube", data)
        self.assertIn("tiktok", data)
        self.assertIn("revenue", data)
        serialized = response.text.lower()
        for forbidden in ("buffer_api_key", "youtube_refresh_token", "client_secret", "read-secret"):
            self.assertNotIn(forbidden, serialized)

    def test_unconfigured_remote_access_is_closed(self):
        os.environ["ZERO_CODE_READ_TOKEN"] = ""
        self.assertEqual(self.client.get("/api/public/status").status_code, 503)


if __name__ == "__main__":
    unittest.main()
