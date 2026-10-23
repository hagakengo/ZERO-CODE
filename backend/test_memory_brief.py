"""Production briefs preserve source, status and approval scope in isolation."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from app import memory_brief
from tools.memory_brief import _NoRedirect


def note(memory_id, status, scope, body):
    return {'id': memory_id, 'title': memory_id, 'approval_status': status,
            'approval_scope': scope, 'sources': ['source:' + memory_id],
            'related': [], 'updated_at': '2026-10-23', 'body': body}


class BriefTests(unittest.TestCase):
    def setUp(self):
        self.eye = note('YUNA-EYE-001', 'DRAFT', '目元判断のみ。MASTER未承認', 'r03目元は再検討。')
        self.k07 = note('K07-PUBLICATION-001', 'APPROVED', 'X02公開のみ。本編MASTER含まない', 'K07のSNS公開。')

    def fetch(self, path):
        if path.endswith('approved_only=true'):
            return {'results': [{k: v for k, v in self.k07.items() if k != 'body'}],
                    'approved_only': True}
        if '/search?' in path:
            return {'results': [{k: v for k, v in item.items() if k != 'body'}
                                for item in (self.eye, self.k07)], 'approved_only': False}
        return {self.eye['id']: self.eye, self.k07['id']: self.k07}[path.rsplit('/', 1)[-1]]

    def test_start_brief_does_not_promote_publication_or_draft(self):
        notes = memory_brief.collect(self.fetch, 'ユナ')
        brief = memory_brief.start_brief('EP00 ユナ雨粒', 'ユナ', notes)
        self.assertEqual(len(brief['approved_memories']), 1)
        self.assertEqual(brief['approved_memories'][0]['approval_scope'], 'X02公開のみ。本編MASTER含まない')
        self.assertEqual(brief['unapproved_reference'][0]['approval_status'], 'DRAFT')
        self.assertEqual(brief['applicable_production_settings'], [])
        text = memory_brief.render_markdown(brief)
        self.assertIn('DRAFT', text)
        self.assertIn('X02公開のみ', text)

    def test_no_approved_memory_is_explicit(self):
        brief = memory_brief.start_brief('EP00', '目元', [self.eye])
        self.assertTrue(brief['no_approved_memory_for_query'])
        self.assertIn('該当なし', memory_brief.render_markdown(brief))

    def test_search_failure_is_not_empty_result(self):
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            memory_brief.collect(lambda path: {'results': [], 'approved_only': True}, 'ユナ')

    def test_approved_only_access_cannot_masquerade_as_all(self):
        def approved_only(path):
            return {'results': [], 'approved_only': True}
        with self.assertRaisesRegex(ValueError, 'approved-only'):
            memory_brief.collect(approved_only, 'ユナ')

    def test_search_and_detail_disagreement_rejected(self):
        def changed(path):
            value = self.fetch(path)
            if path.endswith('/YUNA-EYE-001'):
                return {**value, 'approval_status': 'APPROVED'}
            return value
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            memory_brief.collect(changed, 'ユナ')

    def test_review_brief_keeps_qc_and_approval_separate(self):
        start = memory_brief.start_brief('EP00', 'ユナ', [self.eye, self.k07])
        packet = {'packet_type': 'AI_DIRECTOR_CONTENT_REVIEW_ONLY',
                  'workflow_status': 'DRAFT', 'approval_status': 'DRAFT',
                  'formal_signature': False, 'source_state': 'MATCH',
                  'candidate_id': 'WORK02-EP00-R03-001', 'approval_scope': 'TESTのみ',
                  'source_sha256': 'a' * 64, 'related_memories': [{'id': 'YUNA-EYE-001'}],
                  'os016_qc': {'technical': 'PASS', 'direction_and_drawing': 'REWORK'},
                  'os016_review_proposal': {'recommended_result': 'REVIEW_HOLD'}}
        brief = memory_brief.review_brief(start, packet)
        self.assertEqual((brief['technical_qc'], brief['direction_and_drawing_qc']), ('PASS', 'REWORK'))
        self.assertFalse(brief['formal_director_signature'])
        self.assertEqual(brief['master_approval'], 'NOT_APPROVED')
        self.assertIn('未記録・未署名', memory_brief.render_markdown(brief))
        with self.assertRaisesRegex(ValueError, 'unverified'):
            memory_brief.review_brief(start, {**packet, 'approval_status': 'APPROVED'})

    def test_review_cli_refuses_world_readable_output_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            start = root / 'start.json'
            packet = root / 'packet.json'
            start.write_text(json.dumps(memory_brief.start_brief('EP00', 'ユナ', [self.eye])))
            packet.write_text(json.dumps({'packet_type': 'AI_DIRECTOR_CONTENT_REVIEW_ONLY',
                'workflow_status': 'DRAFT', 'approval_status': 'DRAFT', 'formal_signature': False,
                'source_state': 'MATCH', 'candidate_id': 'WORK02-EP00-R03-001',
                'approval_scope': 'TESTのみ'}))
            start.chmod(0o600)
            packet.chmod(0o600)
            root.chmod(0o755)
            output = root / 'public.md'
            result = subprocess.run([sys.executable, '-m', 'tools.memory_review_brief',
                '--start-json', str(start), '--start-sha256', hashlib.sha256(start.read_bytes()).hexdigest(),
                '--review-packet', str(packet), '--packet-sha256', hashlib.sha256(packet.read_bytes()).hexdigest(),
                '--out', str(output)], cwd=Path(__file__).parent, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(output.exists())

    def test_reader_redirect_is_refused(self):
        with self.assertRaisesRegex(ValueError, 'redirect refused'):
            _NoRedirect().redirect_request(None, None, 302, 'redirect', {}, 'https://example.org')


if __name__ == '__main__':
    unittest.main()
