import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.studio_reader import app

spec = importlib.util.spec_from_file_location('snapshot_builder', Path(__file__).parent / 'tools/build_studio_snapshot.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class StudioReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / 'source'; self.source.mkdir()
        self.media = self.source / 'key.png'; self.media.write_bytes(b'dummy-png-for-isolated-test')
        self.db = sqlite3.connect(self.root / 'isolated-test.sqlite')
        self.db.execute('create table guard(value text)'); self.db.execute("insert into guard values ('unchanged')"); self.db.commit()
        self.production = self.source / 'production.json'
        self.original = {'revision': 7, 'assets': [{'id': 'test-key', 'title': 'ダミー素材', 'project': 'ep00',
            'original_path': str(self.media), 'status': '候補', 'metadata': {'reference_candidate': True}}],
            'history': [{'date': '2026-10-23', 'note': 'テスト履歴'}],
            'projects': [{'id': 'ep00', 'title': 'ダミーEP', 'state': 'TEST'}]}
        self.production.write_text(json.dumps(self.original))
        self.config = {'production_file': str(self.production), 'media_roots': [str(self.source)], 'packages': []}
        self.snapshot = self.root / 'snapshot'
        self.manifest = builder.build(self.config, self.snapshot)
        self.token = 'a-test-only-reader-token-of-at-least-32-characters'
        self.env = patch.dict(os.environ, {'STUDIO_READER_TOKEN': self.token, 'STUDIO_SNAPSHOT_DIR': str(self.snapshot)})
        self.env.start(); self.client = TestClient(app)
        self.auth = {'Authorization': 'Bearer ' + self.token}
        self.id = next(iter(self.manifest['files']))

    def tearDown(self):
        self.assertEqual(json.loads(self.production.read_text()), self.original)
        self.assertEqual(self.db.execute('select value from guard').fetchone()[0], 'unchanged')
        self.client.close(); self.env.stop(); self.db.close(); self.temp.cleanup()

    def test_auth_fail_closed_index_and_media(self):
        for url in ['/api/studio/index', '/api/studio/media/' + self.id]:
            r = self.client.get(url); self.assertEqual(r.status_code, 401)
            self.assertEqual(r.headers['cache-control'], 'private, no-store')
        self.assertEqual(self.client.get('/api/studio/index', headers={'Authorization': 'Bearer wrong'}).status_code, 401)

    def test_missing_auth_config(self):
        with patch.dict(os.environ, {'STUDIO_READER_TOKEN': ''}):
            self.assertEqual(self.client.get('/api/studio/index', headers=self.auth).status_code, 503)

    def test_index_no_paths_or_fabricated_connection(self):
        r = self.client.get('/api/studio/index', headers=self.auth)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['revision'], 7)
        self.assertNotIn(str(self.source), r.text)
        self.assertIn('閲覧用', r.json()['mode'])
        self.assertEqual(r.json()['assets'][0]['approval'], '表情作画の参考候補／完成原画・MASTER未承認')
        self.assertEqual(r.json()['cuts'][0]['verdict'], 'UNVERIFIED')

    def test_private_copy_and_range(self):
        self.media.write_bytes(b'changed-original-after-snapshot')
        r = self.client.get('/api/studio/media/' + self.id, headers={**self.auth, 'Range': 'bytes=0-4'})
        self.assertEqual(r.status_code, 206); self.assertEqual(r.content, b'dummy')
        self.assertEqual(r.headers['x-asset-sha256'], self.id)
        self.assertEqual(self.client.head('/api/studio/media/' + self.id, headers=self.auth).status_code, 200)
        self.assertEqual(self.client.get('/api/studio/media/' + self.id, headers={**self.auth, 'Range': 'bytes=9000-9100'}).status_code, 416)

    def test_no_write_or_legacy_routes(self):
        for method in ['post', 'put', 'patch', 'delete']:
            self.assertEqual(getattr(self.client, method)('/api/studio/index', headers=self.auth).status_code, 405)
        for url in ['/api/metrics/manual', '/api/status', '/docs', '/openapi.json']:
            self.assertEqual(self.client.get(url, headers=self.auth).status_code, 404)

    def test_unknown_and_traversal(self):
        for asset in ['unknown', '%2e%2e%2fmanifest.json', '%2Fetc%2Fpasswd']:
            self.assertEqual(self.client.get('/api/studio/media/' + asset, headers=self.auth).status_code, 404)

    def test_tampered_media(self):
        p = self.snapshot / self.manifest['files'][self.id]['copy']; p.write_bytes(b'tampered')
        self.assertEqual(self.client.get('/api/studio/media/' + self.id, headers=self.auth).status_code, 409)

    def test_manifest_escape_denied(self):
        self.manifest['files'][self.id]['copy'] = '../source/key.png'
        (self.snapshot / 'manifest.json').write_text(json.dumps(self.manifest))
        self.assertEqual(self.client.get('/api/studio/media/' + self.id, headers=self.auth).status_code, 409)

    def test_media_symlink_denied(self):
        p = self.snapshot / self.manifest['files'][self.id]['copy']; p.unlink(); p.symlink_to(self.media)
        self.assertEqual(self.client.get('/api/studio/media/' + self.id, headers=self.auth).status_code, 409)

    def test_missing_or_corrupt_snapshot(self):
        with patch.dict(os.environ, {'STUDIO_SNAPSHOT_DIR': str(self.root / 'missing')}):
            self.assertEqual(self.client.get('/api/studio/index', headers=self.auth).status_code, 503)
        (self.snapshot / 'manifest.json').write_text('{')
        self.assertEqual(self.client.get('/api/studio/index', headers=self.auth).status_code, 503)

    def test_no_overwrite_snapshot(self):
        with self.assertRaises(ValueError): builder.build(self.config, self.snapshot)

    def test_import_outside_root_or_missing_not_replaced(self):
        outside = self.root / 'outside.png'; outside.write_bytes(b'outside')
        d = copy.deepcopy(self.original); d['assets'][0]['original_path'] = str(outside)
        self.production.write_text(json.dumps(d))
        result = builder.build(self.config, self.root / 'second')
        self.assertIsNone(result['index']['assets'][0]['media'])
        self.production.write_text(json.dumps(self.original))

    def test_import_source_unchanged(self):
        self.assertEqual(json.loads(self.production.read_text()), self.original)
        receipt = json.loads((self.snapshot / 'import_receipt.private.json').read_text())
        self.assertEqual(receipt['production_sha256_before'], receipt['production_sha256_after'])
        self.assertNotEqual(self.snapshot / 'media' / (self.id + '.png'), self.media)

    def test_report_status_uses_verdict_not_mentions(self):
        package = self.source / 'package'; package.mkdir()
        (package / 'rough_keys').mkdir()
        (package / '自己QC報告.md').write_text('**PASS／判定**\n以前はREWORKだった。')
        config = {**self.config, 'packages': [{'version': 'r09', 'path': str(package)}]}
        result = builder.build(config, self.root / 'pass-report')
        self.assertEqual(result['index']['cuts'][0]['versions'][0]['verdict'], 'PASS')
        self.assertFalse(result['index']['cuts'][0]['next_stage_allowed'])

    def test_absent_report_never_infers_rework_from_version(self):
        package = self.source / 'package'; package.mkdir()
        (package / 'rough_keys').mkdir()
        config = {**self.config, 'packages': [{'version': 'r03', 'path': str(package)}]}
        result = builder.build(config, self.root / 'unknown-report')
        self.assertEqual(result['index']['cuts'][0]['verdict'], 'UNVERIFIED')


if __name__ == '__main__': unittest.main()
