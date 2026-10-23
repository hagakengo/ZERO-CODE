"""DRAFT inbox tests use synthetic reports and never touch production OS or vault."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import memory_drafts, memory_security, memory_workflow
from app.studio_reader import app


class DraftInboxTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.vault = self.base / 'vault'
        self.vault.mkdir()
        self.root = self.base / 'drafts'
        memory_drafts.initialize(self.root, self.vault)
        self.work01 = self.base / 'work01.md'
        self.work02 = self.base / 'work02.md'
        self.work01.write_text('判断：投稿本文は審査対象。\n理由：公開の最終判断は別に管理する。', encoding='utf-8')
        self.work02.write_text('判断：原画TESTはREWORK。\n理由：目元の動きが不自然。', encoding='utf-8')
        self.a = {'id': 'TEST-WORK01-001', 'title': '投稿文の審査記録', 'kind': 'production_decision',
                  'characters': [], 'assets': ['X01'], 'episodes': [],
                  'decision_excerpt': '投稿本文は審査対象。',
                  'reason_excerpt': '公開の最終判断は別に管理する。',
                  'approval_scope': '文章審査の記録のみ。公開承認ではない。',
                  'related': [], 'source_id': 'test:work01', 'proposed_by': 'work01'}
        self.b = {'id': 'TEST-WORK02-001', 'title': '目元の原画TEST', 'kind': 'production_result',
                  'characters': ['ユナ'], 'assets': ['K07'], 'episodes': ['EP00'],
                  'decision_excerpt': '原画TESTはREWORK。', 'reason_excerpt': '目元の動きが不自然。',
                  'approval_scope': 'TESTのみ。MASTER採用ではない。',
                  'related': ['EXISTING-EYE-001'], 'source_id': 'test:work02',
                  'proposed_by': 'work02'}
        self.existing = self.vault / 'EXISTING-EYE-001.md'
        self.existing.write_text('''---
id: "EXISTING-EYE-001"
title: "ユナの目元"
kind: "production_decision"
approval_status: "DRAFT"
approval_scope: "既存の目元判断だけ"
source: "test:existing"
sources: ["test:existing"]
updated_at: "2026-10-23"
related: []
assets: ["K07"]
---

# テスト用の既存記憶
''', encoding='utf-8')
        self.auth = self.base / 'auth'
        memory_security.initialize(self.auth)
        self.token = memory_security.issue(self.auth, 'work02', 'all')
        self.env = patch.dict(os.environ, {'STUDIO_MEMORY_DIR': str(self.vault),
                                         'STUDIO_MEMORY_AUTH_DIR': str(self.auth)})
        self.env.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.env.stop()
        self.temp.cleanup()

    def _add_both(self):
        memory_drafts.add(self.root, self.work01, self.a)
        memory_drafts.add(self.root, self.work02, self.b, unknowns=['正式原画の判断は未確認'])

    def test_two_works_list_filter_detail_and_related_overlap(self):
        self._add_both()
        self.assertEqual(len(memory_drafts.list_candidates(self.root)), 2)
        self.assertEqual([x['id'] for x in memory_drafts.list_candidates(self.root, proposed_by='work01')],
                         [self.a['id']])
        self.assertEqual([x['id'] for x in memory_drafts.list_candidates(self.root, character='ユナ')],
                         [self.b['id']])
        self.assertEqual([x['id'] for x in memory_drafts.list_candidates(self.root, asset='K07')],
                         [self.b['id']])
        self.assertEqual([x['id'] for x in memory_drafts.list_candidates(self.root, q='目元')],
                         [self.b['id']])
        detail = memory_drafts.detail(self.root, self.b['id'])
        self.assertEqual(detail['source_state'], 'MATCH')
        self.assertEqual(detail['existing_memory_overlap'], ['EXISTING-EYE-001'])
        self.assertEqual(detail['related_memories'][0]['approval_status'], 'DRAFT')
        self.assertEqual(detail['unknowns'], ['正式原画の判断は未確認'])
        self.assertEqual(detail['review_status'], 'REVIEW_PENDING')

    def test_review_packet_and_advisory_pass_do_not_promote(self):
        self._add_both()
        packet = memory_drafts.review_packet(self.root, self.b['id'])
        self.assertFalse(packet['formal_signature'])
        self.assertEqual(packet['source_sha256'], memory_workflow._sha(self.work02.read_bytes()))
        self.assertEqual(packet['existing_memory_overlap'], ['EXISTING-EYE-001'])
        memory_drafts.record_review(self.root, self.b['id'], 'REVIEW_PASS', 'AI監督・内容評価',
                                    '出典一致。既存記憶との意味上の関係は別判断。')
        current = memory_drafts.detail(self.root, self.b['id'])
        self.assertEqual(current['review_status'], 'REVIEW_PASS')
        self.assertEqual(current['candidate']['workflow_status'], 'DRAFT')
        self.assertEqual(current['candidate']['approval_status'], 'DRAFT')
        self.assertFalse((self.vault / (self.b['id'] + '.md')).exists())
        response = self.client.get('/api/studio/memory/' + self.b['id'],
                                   headers={'Authorization': 'Bearer ' + self.token})
        self.assertEqual(response.status_code, 404)

    def test_source_change_or_missing_blocks_pass(self):
        self._add_both()
        self.work02.write_text('changed', encoding='utf-8')
        self.assertEqual(memory_drafts.detail(self.root, self.b['id'])['source_state'], 'MISMATCH_OR_MISSING')
        with self.assertRaises(ValueError):
            memory_drafts.record_review(self.root, self.b['id'], 'REVIEW_PASS', 'AI監督', '根拠不足')
        self.work02.unlink()
        self.assertEqual(memory_drafts.detail(self.root, self.b['id'])['source_state'], 'MISMATCH_OR_MISSING')
        memory_drafts.record_review(self.root, self.b['id'], 'REVIEW_HOLD', 'AI監督', '出典が消失')

    def test_missing_report_duplicate_and_scope_tamper(self):
        self._add_both()
        with self.assertRaises(OSError):
            memory_drafts.add(self.root, self.base / 'missing.md', {**self.a, 'id': 'TEST-MISSING-001'})
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            memory_drafts.add(self.root, self.work01, self.a)
        path = self.root / 'candidates' / (self.b['id'] + '.json')
        changed = json.loads(path.read_text())
        changed['approval_scope'] = 'MASTER承認'
        path.write_text(json.dumps(changed, ensure_ascii=False), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'annotations'):
            memory_drafts.detail(self.root, self.b['id'])

    def test_scope_is_always_draft_and_no_keys_or_registration(self):
        self._add_both()
        self.assertFalse((self.root / 'keys').exists())
        self.assertFalse((self.root / 'proofs').exists())
        self.assertFalse((self.root / 'events').exists())
        with self.assertRaises(ValueError):
            memory_workflow.register(self.root, self.b['id'])
        self.assertFalse((self.vault / (self.b['id'] + '.md')).exists())

    def test_private_root_rejects_open_permissions(self):
        self._add_both()
        self.root.chmod(0o755)
        with self.assertRaisesRegex(ValueError, 'unsafe'):
            memory_drafts.list_candidates(self.root)

    def test_similar_draft_is_flagged_without_merging(self):
        self._add_both()
        later = {**self.b, 'id': 'TEST-WORK02-002', 'title': '別の目元TEST'}
        memory_drafts.add(self.root, self.work02, later)
        detail = memory_drafts.detail(self.root, later['id'])
        self.assertEqual(detail['draft_overlap'], [self.b['id']])
        self.assertEqual(detail['candidate']['workflow_status'], 'DRAFT')
        self.assertEqual(len(memory_drafts.list_candidates(self.root)), 3)

    def test_cli_add_list_packet(self):
        fields = self.base / 'fields.json'
        fields.write_text(json.dumps(self.a, ensure_ascii=False), encoding='utf-8')
        command = [sys.executable, '-m', 'tools.memory_drafts', '--root', str(self.root)]
        cwd = Path(__file__).parent
        result = subprocess.run([*command, 'add', '--report', str(self.work01), '--fields', str(fields)],
                                cwd=cwd, capture_output=True, text=True, check=True)
        self.assertIn('DRAFT', result.stdout)
        listed = subprocess.run([*command, 'list', '--work', 'work01'], cwd=cwd,
                                capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(listed.stdout)[0]['id'], self.a['id'])
        packet = self.base / 'review.json'
        subprocess.run([*command, 'packet', '--id', self.a['id'], '--out', str(packet)], cwd=cwd,
                       capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(packet.read_text())['packet_type'], 'AI_DIRECTOR_CONTENT_REVIEW_ONLY')


if __name__ == '__main__':
    unittest.main()
