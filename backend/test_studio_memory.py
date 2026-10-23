"""Studio Memory tests use only temporary, synthetic notes."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.studio_reader import app
from app import memory_security


def note(memory_id, status, body):
    return f'''---
id: "{memory_id}"
title: "{body}"
kind: "test"
approval_status: "{status}"
approval_scope: "isolated test only"
source: "synthetic test source"
updated_at: "2026-10-23"
related: ["K07-PUBLICATION-001"]
assets: ["test-key"]
sources: ["instruction:synthetic-test"]
---

# {body}
'''


class StudioMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'K07-PUBLICATION-001.md').write_text(
            note('K07-PUBLICATION-001', 'APPROVED', 'K07 SNS公開承認。本編DRAFT。'), encoding='utf-8')
        (self.root / 'YUNA-EYE-001.md').write_text(
            note('YUNA-EYE-001', 'DRAFT', 'ユナの目元 r03不採用判断。'), encoding='utf-8')
        self.auth_root = self.root / 'auth'
        memory_security.initialize(self.auth_root)
        self.token = memory_security.issue(self.auth_root, 'work02', 'all')
        self.env = patch.dict(os.environ, {'STUDIO_MEMORY_AUTH_DIR': str(self.auth_root),
                                         'STUDIO_MEMORY_DIR': str(self.root)})
        self.env.start()
        self.client = TestClient(app)
        self.auth = {'Authorization': 'Bearer ' + self.token}

    def tearDown(self):
        self.client.close()
        self.env.stop()
        self.temp.cleanup()

    def test_japanese_search_and_provenance(self):
        result = self.client.get('/api/studio/memory/search?q=ユナの目元', headers=self.auth)
        self.assertEqual(result.status_code, 200)
        self.assertEqual([x['id'] for x in result.json()['results']], ['YUNA-EYE-001'])
        detail = self.client.get('/api/studio/memory/YUNA-EYE-001', headers=self.auth).json()
        for key in ['id', 'source', 'sources', 'approval_status', 'updated_at', 'related', 'assets', 'body']:
            self.assertIn(key, detail)
        self.assertEqual(detail['approval_status'], 'DRAFT')
        self.assertIn('K07-PUBLICATION-001', detail['related'])
        natural = self.client.get('/api/studio/memory/search?q=ユナのr03目元について、どんな判断があるか',
                                  headers=self.auth)
        self.assertEqual([x['id'] for x in natural.json()['results']], ['YUNA-EYE-001'])

    def test_approved_only_does_not_promote_draft(self):
        result = self.client.get('/api/studio/memory/search?approved_only=true', headers=self.auth)
        self.assertEqual([x['id'] for x in result.json()['results']], ['K07-PUBLICATION-001'])
        self.assertEqual(self.client.get('/api/studio/memory/YUNA-EYE-001?approved_only=true',
                                         headers=self.auth).status_code, 404)
        approved = self.client.get('/api/studio/memory/K07-PUBLICATION-001?approved_only=true',
                                   headers=self.auth).json()
        self.assertIn('本編DRAFT', approved['body'])
        self.assertEqual(approved['approval_scope'], 'isolated test only')

    def test_auth_and_no_write_routes(self):
        for url in ['/api/studio/memory/search', '/api/studio/memory/K07-PUBLICATION-001']:
            self.assertEqual(self.client.get(url).status_code, 401)
            self.assertEqual(self.client.get(url, headers={'Authorization': 'Bearer bad'}).status_code, 401)
            self.assertEqual(self.client.post(url, headers=self.auth).status_code, 405)

    def test_missing_vault_and_bad_note_fail_closed(self):
        with patch.dict(os.environ, {'STUDIO_MEMORY_DIR': ''}):
            self.assertEqual(self.client.get('/api/studio/memory/search', headers=self.auth).status_code, 503)
        path = self.root / 'YUNA-EYE-001.md'
        path.write_text('---\nid: invalid\n---\nsecret', encoding='utf-8')
        self.assertEqual(self.client.get('/api/studio/memory/search', headers=self.auth).status_code, 503)

    def test_symlink_and_path_traversal_denied(self):
        outside = self.root.parent / 'private-test-memory.md'
        target = self.root / 'YUNA-EYE-001.md'
        target.unlink()
        target.symlink_to(outside)
        self.assertEqual(self.client.get('/api/studio/memory/search', headers=self.auth).status_code, 503)
        self.assertEqual(self.client.get('/api/studio/memory/%2e%2e', headers=self.auth).status_code, 404)

    def test_multiple_notes_and_keyword_filter(self):
        (self.root / 'STUDIO-WORKFLOW-001.md').write_text(
            note('STUDIO-WORKFLOW-001', 'DRAFT', '架空の制作フロー。'), encoding='utf-8')
        result = self.client.get('/api/studio/memory/search?q=制作フロー', headers=self.auth)
        self.assertEqual([x['id'] for x in result.json()['results']], ['STUDIO-WORKFLOW-001'])
        approved = self.client.get('/api/studio/memory/search?approved_only=true', headers=self.auth)
        self.assertEqual([x['id'] for x in approved.json()['results']], ['K07-PUBLICATION-001'])

    def test_work_isolation_and_scope(self):
        work01 = memory_security.issue(self.auth_root, 'work01', 'approved')
        auth = {'Authorization': 'Bearer ' + work01}
        result = self.client.get('/api/studio/memory/search', headers=auth)
        self.assertEqual(result.status_code, 200)
        self.assertEqual([x['id'] for x in result.json()['results']], ['K07-PUBLICATION-001'])
        self.assertTrue(result.json()['approved_only'])
        self.assertEqual(self.client.get('/api/studio/memory/YUNA-EYE-001', headers=auth).status_code, 404)
        self.assertEqual(self.client.get('/api/studio/memory/K07-PUBLICATION-001', headers=auth).status_code, 200)
        with self.assertRaises(ValueError):
            memory_security.issue(self.auth_root, 'work01', 'all')

    def test_expiry_reissue_and_individual_revocation(self):
        expired = memory_security.issue(self.auth_root, 'work01', 'approved', now=1)
        self.assertEqual(self.client.get('/api/studio/memory/search', headers={'Authorization': 'Bearer ' + expired}).status_code, 401)
        work01 = memory_security.issue(self.auth_root, 'work01', 'approved')
        work01_auth = {'Authorization': 'Bearer ' + work01}
        self.assertEqual(self.client.get('/api/studio/memory/search', headers=work01_auth).status_code, 200)
        memory_security.revoke_token(self.auth_root, work01)
        self.assertEqual(self.client.get('/api/studio/memory/search', headers=work01_auth).status_code, 401)
        renewed = memory_security.issue(self.auth_root, 'work01', 'approved')
        self.assertEqual(self.client.get('/api/studio/memory/search', headers={'Authorization': 'Bearer ' + renewed}).status_code, 200)
        memory_security.revoke_work(self.auth_root, 'work01')
        self.assertEqual(self.client.get('/api/studio/memory/search', headers={'Authorization': 'Bearer ' + renewed}).status_code, 401)
        self.assertEqual(self.client.get('/api/studio/memory/search', headers=self.auth).status_code, 200)

    def test_least_privilege_and_audit_redaction(self):
        search_only = memory_security.issue(self.auth_root, 'work02', 'all', operations=('search',))
        headers = {'Authorization': 'Bearer ' + search_only}
        self.assertEqual(self.client.get('/api/studio/memory/search?q=private-query-sentinel', headers=headers).status_code, 200)
        self.assertEqual(self.client.get('/api/studio/memory/K07-PUBLICATION-001', headers=headers).status_code, 403)
        audit = (self.auth_root / 'audit.jsonl').read_text()
        events = [__import__('json').loads(line) for line in audit.splitlines()]
        self.assertTrue(events)
        self.assertEqual(set(events[-1]), {'at', 'work_id', 'operation', 'result'})
        self.assertEqual(events[-1]['work_id'], 'work02')
        self.assertEqual(events[-1]['result'], '403')
        for secret in [search_only, self.token, 'private-query-sentinel', 'K07-PUBLICATION-001', 'SNS公開承認']:
            self.assertNotIn(secret, audit)

    def test_auth_state_failure_is_closed(self):
        (self.auth_root / 'state.json').chmod(0o644)
        self.assertEqual(self.client.get('/api/studio/memory/search', headers=self.auth).status_code, 503)

    def test_corrupt_token_and_audit_failure_are_closed(self):
        invalid = {'Authorization': 'Bearer not-base64.%%%%'}
        self.assertEqual(self.client.get('/api/studio/memory/search', headers=invalid).status_code, 401)
        (self.auth_root / 'audit.jsonl').chmod(0o644)
        self.assertEqual(self.client.get('/api/studio/memory/search', headers=self.auth).status_code, 503)


if __name__ == '__main__':
    unittest.main()
