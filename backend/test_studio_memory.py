"""Studio Memory tests use only temporary, synthetic notes."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from app.studio_reader import app


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
        self.token = 'synthetic-reader-token-longer-than-32-characters'
        self.env = patch.dict(os.environ, {'STUDIO_READER_TOKEN': self.token,
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


if __name__ == '__main__':
    unittest.main()
