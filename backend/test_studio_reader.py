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
        self.assertEqual(self.client.get('/api/studio/media/' + self.id, headers=self.auth).status_code, 503)

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

    def test_unreviewed_text_never_disclosed_even_with_nested_secrets(self):
        d = copy.deepcopy(self.original)
        payload = 'sensitive fictional personal detail, no recognizable pattern'
        d['assets'][0].update(title=payload, source='C:\\private\\memo',
                              metadata={'version': 'token=synthetic-only', 'extra': {'password': 'fake'}})
        d['history'][0]['note'] = '/home/test-user x@example.test Authorization: fake'
        self.production.write_text(json.dumps(d))
        try:
            result = builder.build(self.config, self.root / 'withheld')
            public = json.dumps(result['index'])
            for forbidden in [payload, 'private', 'token=', 'example.test', 'Authorization', 'password']:
                self.assertNotIn(forbidden, public.replace('private-copy://', ''))
        finally:
            self.production.write_text(json.dumps(self.original))

    def test_review_digest_not_regex_is_primary_disclosure_gate(self):
        safe = '作画参考候補'
        digest = hashlib.sha256(safe.encode()).hexdigest()
        self.assertNotEqual(builder.public_text(safe), safe)
        self.assertEqual(builder.public_text(safe, {digest}), safe)
        for secret in ['/etc/passwd', '/home/synthetic', 'C:\\private\\memo',
                       'user@example.test', 'password=not-real', 'Authorization: fake',
                       '+81 90 1234 5678', 'https://user:fake@example.test']:
            approved = {hashlib.sha256(secret.encode()).hexdigest()}
            self.assertNotEqual(builder.public_text(secret, approved), secret)

    def test_raw_documents_not_attached(self):
        note = self.source / 'memo.md'; note.write_text('arbitrary secret without patterns')
        d = copy.deepcopy(self.original); d['assets'][0]['original_path'] = str(note)
        self.production.write_text(json.dumps(d))
        try:
            result = builder.build(self.config, self.root / 'text-blocked')
            self.assertIsNone(result['index']['assets'][0]['media'])
            self.assertEqual(result['files'], {})
        finally: self.production.write_text(json.dumps(self.original))

    def test_partial_copy_and_disk_full_never_publish(self):
        import errno
        for code in [errno.EIO, errno.ENOSPC]:
            target = self.root / ('failed-' + str(code))
            def broken(source, dest):
                Path(dest).write_bytes(b'partial')
                raise OSError(code, 'synthetic copy fault')
            with patch.object(builder.shutil, 'copyfile', broken):
                with self.assertRaises(ValueError): builder.build(self.config, target)
            self.assertFalse(target.exists())
            self.assertEqual(list(self.root.glob('.studio-import-*')), [])

    def test_source_change_during_copy_aborts(self):
        original_copy = builder.shutil.copyfile
        def changed(source, dest):
            original_copy(source, dest)
            Path(source).write_bytes(b'changed while importing')
        target = self.root / 'changed-source'
        with patch.object(builder.shutil, 'copyfile', changed):
            with self.assertRaises(ValueError): builder.build(self.config, target)
        self.assertFalse(target.exists())

    def test_size_limit_withholds_and_growth_aborts(self):
        result = builder.build({**self.config, 'max_file_bytes': 2}, self.root / 'oversize')
        self.assertIsNone(result['index']['assets'][0]['media'])
        self.assertEqual(result['files'], {})
        original_copy = builder.shutil.copyfile
        def oversized(source, dest):
            original_copy(source, dest); Path(dest).write_bytes(b'x' * 101)
        with patch.object(builder.shutil, 'copyfile', oversized):
            with self.assertRaises(ValueError):
                builder.build({**self.config, 'max_file_bytes': 100}, self.root / 'growth')
        self.assertFalse((self.root / 'growth').exists())

    def test_receipt_failure_never_publishes_manifest(self):
        original_write = Path.write_text
        def fail_receipt(path, *args, **kwargs):
            if path.name == 'import_receipt.private.json': raise OSError('synthetic receipt failure')
            return original_write(path, *args, **kwargs)
        with patch.object(Path, 'write_text', fail_receipt):
            with self.assertRaises(OSError): builder.build(self.config, self.root / 'bad-receipt')
        self.assertFalse((self.root / 'bad-receipt').exists())

    def test_incomplete_snapshot_rejected(self):
        (self.snapshot / 'COMPLETE').unlink()
        for route in ['/api/studio/index', '/api/studio/media/' + self.id]:
            self.assertEqual(self.client.get(route, headers=self.auth).status_code, 503)

    def test_pass_is_only_work_qc_and_never_producer_approval(self):
        package = self.source / 'qc'; package.mkdir(); (package / 'rough_keys').mkdir()
        (package / 'QC.md').write_text('**PASS**')
        result = builder.build({**self.config, 'packages': [{'version': 'r04', 'path': str(package)}]}, self.root / 'self-pass')
        self.assertEqual(result['index']['reviews'][0]['actor'], 'Work')
        self.assertFalse(result['index']['cuts'][0]['next_stage_allowed'])
        self.assertIn('未承認', result['index']['cuts'][0]['producer_approval'])

    def test_total_capacity_failure_aborts_snapshot(self):
        with self.assertRaises(ValueError):
            builder.build({**self.config, 'max_total_bytes': 1}, self.root / 'over-budget')
        self.assertFalse((self.root / 'over-budget').exists())

    def test_unexpected_nested_dto_field_rejected(self):
        self.manifest['index']['assets'][0]['private_note'] = 'not permitted'
        target = self.snapshot / 'manifest.json'; target.write_text(json.dumps(self.manifest))
        (self.snapshot / 'COMPLETE').write_text(hashlib.sha256(target.read_bytes()).hexdigest())
        self.assertEqual(self.client.get('/api/studio/index', headers=self.auth).status_code, 503)


if __name__ == '__main__': unittest.main()
