import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

temporary_db = tempfile.TemporaryDirectory()
os.environ["DATABASE_URL"] = f"sqlite:///{temporary_db.name}/test.db"

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.main import AssetRegistration, Base, SessionLocal, app, engine


class AssetRegistryTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.drop_all(engine, tables=[AssetRegistration.__table__])
        AssetRegistration.__table__.create(engine)
        token = patch.dict(os.environ, {"ZERO_CODE_ASSET_REGISTRY_TOKEN": "test-only"})
        token.start()
        self.addCleanup(token.stop)
        self.client = TestClient(app, headers={"X-ZCS-Asset-Token": "test-only"})
        self.addCleanup(self.client.close)
        self.asset = {
            "asset_id": "ZCS-EP01-CUT02-FRAME-01",
            "version": "r01",
            "episode": "EP01",
            "cut": "CUT-02",
            "sha256": "a" * 64,
            "dropbox_file_id": "id:test-frame",
            "dropbox_path": "/test/frame.png",
            "status": "DRAFT",
        }
        self.url = f"/api/assets/{self.asset['asset_id']}/r01"

    def test_register_read_and_retry(self):
        self.assertEqual(self.client.get(self.url).status_code, 404)
        for expected_status in (201, 200):
            result = self.client.post("/api/assets", json=self.asset)
            self.assertEqual(result.status_code, expected_status, result.text)
            self.assertEqual(result.json(), self.asset)
        self.assertEqual(self.client.get(self.url).json(), self.asset)

    def test_conflicts_and_new_revision(self):
        self.assertEqual(self.client.post("/api/assets", json=self.asset).status_code, 201)
        changed = dict(self.asset, sha256="b" * 64)
        self.assertEqual(self.client.post("/api/assets", json=changed).status_code, 409)
        alias = dict(self.asset, asset_id="ZCS-EP01-CUT02-ALIAS")
        self.assertEqual(self.client.post("/api/assets", json=alias).status_code, 409)
        revision = dict(changed, version="r02")
        self.assertEqual(self.client.post("/api/assets", json=revision).status_code, 201)
        self.assertEqual(self.client.get(self.url).json(), self.asset)

    def test_draft_only_and_validation(self):
        for invalid in ({"status": "MASTER"}, {"status": "APPROVED"}, {"sha256": "invalid"},
                        {"dropbox_file_id": "/path"}, {"master": True}):
            with self.subTest(invalid=invalid):
                response = self.client.post("/api/assets", json=dict(self.asset, **invalid))
                self.assertEqual(response.status_code, 422)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_requires_registry_token_for_read_and_write(self):
        with TestClient(app) as anonymous:
            self.assertEqual(anonymous.get(self.url).status_code, 401)
            self.assertEqual(anonymous.post("/api/assets", json=self.asset).status_code, 401)
        with patch.dict(os.environ, {"ZERO_CODE_ASSET_REGISTRY_TOKEN": ""}):
            self.assertEqual(self.client.get(self.url).status_code, 503)

    def test_concurrent_retries_create_one_row(self):
        def submit(_):
            return self.client.post("/api/assets", json=self.asset).status_code

        with ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(sorted(pool.map(submit, range(4))), [200, 200, 200, 201])
        with SessionLocal() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(AssetRegistration)), 1)
