import os
import tempfile
import unittest
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

temporary_db = tempfile.TemporaryDirectory()
os.environ["DATABASE_URL"] = f"sqlite:///{temporary_db.name}/test.db"
if port := os.getenv("ZCS_TEST_POSTGRES_PORT"):
    os.environ["DATABASE_URL"] = f"postgresql://postgres:zcs-test@127.0.0.1:{int(port)}/postgres"

from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.main import AssetRegistration, Base, SessionLocal, app, engine, migrate


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
            "size_bytes": 123,
            "provenance": {"verifier": "test-verifier", "evidence_sha256": "b" * 64},
        }
        self.url = f"/api/assets/{self.asset['asset_id']}/r01"

    def test_register_read_and_retry(self):
        self.assertEqual(self.client.get(self.url).status_code, 404)
        for expected_status in (201, 200):
            result = self.client.post("/api/assets", json=self.asset)
            self.assertEqual(result.status_code, expected_status, result.text)
            if expected_status == 201:
                record = result.json()
                self.assertIsNotNone(datetime.fromisoformat(record["registered_at"]).tzinfo)
                self.assertEqual({k: record[k] for k in self.asset}, self.asset)
            self.assertEqual(result.json(), record)
        self.assertEqual(self.client.get(self.url).json(), record)

    def test_conflicts_and_new_revision(self):
        self.assertEqual(self.client.post("/api/assets", json=self.asset).status_code, 201)
        changed = dict(self.asset, sha256="b" * 64)
        self.assertEqual(self.client.post("/api/assets", json=changed).status_code, 409)
        alias = dict(self.asset, asset_id="ZCS-EP01-CUT02-ALIAS")
        self.assertEqual(self.client.post("/api/assets", json=alias).status_code, 409)
        revision = dict(changed, version="r02")
        self.assertEqual(self.client.post("/api/assets", json=revision).status_code, 201)
        history = self.client.get(self.url.rsplit("/", 1)[0]).json()
        self.assertEqual([row["version"] for row in history], ["r01", "r02"])
        self.assertEqual(history[0]["sha256"], self.asset["sha256"])
        self.assertEqual(history[1]["sha256"], revision["sha256"])

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
            self.assertEqual(anonymous.get(self.url.rsplit("/", 1)[0]).status_code, 401)
            self.assertEqual(anonymous.post("/api/assets", json=self.asset).status_code, 401)
        for headers, expected in (
            ({"X-ZCS-Asset-Token": "incorrect"}, 401),
            ({"Origin": "https://untrusted.invalid"}, 403),
            ({"Origin": "null"}, 403),
        ):
            with self.subTest(headers=headers):
                self.assertEqual(self.client.get(self.url, headers=headers).status_code, expected)
                self.assertEqual(self.client.post("/api/assets", json=self.asset, headers=headers).status_code,
                                 expected)
        for headers, expected in (
            ({"X-ZCS-Asset-Token": "incorrect"}, 401),
            ({"Origin": "https://untrusted.invalid"}, 403),
        ):
            self.assertEqual(self.client.get(self.url.rsplit("/", 1)[0], headers=headers).status_code,
                             expected)
        with patch.dict(os.environ, {"ZERO_CODE_ASSET_REGISTRY_TOKEN": ""}):
            self.assertEqual(self.client.get(self.url).status_code, 503)
            self.assertEqual(self.client.post("/api/assets", json=self.asset).status_code, 503)
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_legacy_rows_survive_additive_migration(self):
        legacy = {k: v for k, v in self.asset.items() if k not in {"size_bytes", "provenance"}}
        with engine.begin() as connection:
            for column in ("registered_at", "size_bytes", "provenance"):
                connection.execute(text(f"ALTER TABLE asset_registrations DROP COLUMN {column}"))
            names = ", ".join(legacy)
            values = ", ".join(f":{name}" for name in legacy)
            connection.execute(text(f"INSERT INTO asset_registrations ({names}) VALUES ({values})"), legacy)
        migrate()
        migrate()
        response = self.client.post("/api/assets", json=legacy)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), dict(legacy, registered_at=None, size_bytes=None, provenance=None))

    def test_database_constraints(self):
        self.assertEqual(self.client.post("/api/assets", json=self.asset).status_code, 201)
        for changes in (
            {"sha256": "c" * 64},
            {"asset_id": "ALIAS"},
            {"asset_id": "OTHER", "sha256": "c" * 64, "status": "READY"},
        ):
            with self.subTest(changes=changes), SessionLocal() as db:
                db.add(AssetRegistration(**dict(self.asset, **changes)))
                with self.assertRaises(IntegrityError):
                    db.commit()

    def test_concurrent_retries_create_one_row(self):
        def submit(_):
            return self.client.post("/api/assets", json=self.asset).status_code

        with ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(sorted(pool.map(submit, range(4))), [200, 200, 200, 201])
        with SessionLocal() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(AssetRegistration)), 1)
