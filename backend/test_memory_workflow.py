"""Entire approval workflow is exercised with synthetic notes and test keys."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import memory_security, memory_workflow
from app.studio_reader import app


class MemoryWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.vault = self.root / 'vault'
        self.vault.mkdir()
        self.workflow = self.root / 'workflow'
        self.keys = self.root / 'human-test-keys'
        self.keys.mkdir(mode=0o700)
        for role in ('director', 'producer'):
            private = self.keys / (role + '.private.pem')
            public = self.keys / (role + '.public.pem')
            subprocess.run([memory_workflow._openssl(), 'genpkey', '-algorithm', 'Ed25519', '-out', str(private)], check=True,
                           capture_output=True)
            subprocess.run([memory_workflow._openssl(), 'pkey', '-in', str(private), '-pubout', '-out', str(public)], check=True,
                           capture_output=True)
            private.chmod(0o600)
        memory_workflow.initialize(self.workflow, self.vault, self.keys / 'director.public.pem',
                                   self.keys / 'producer.public.pem')
        self.report = self.root / 'synthetic-work02-report.md'
        self.report.write_text('制作結果：合成アニメTESTの原画を比較した。\n判断：目元の形は再修正が必要。\n理由：視線が雨粒から外れて見える。', encoding='utf-8')
        self.fields = {'id': 'SYNTHETIC-EYE-001', 'title': '合成TESTの目元判断', 'kind': 'production_decision',
                       'characters': ['ユナ'], 'assets': ['SYNTHETIC-KEY-01'], 'episodes': ['EP00'],
                       'decision_excerpt': '目元の形は再修正が必要。',
                       'reason_excerpt': '視線が雨粒から外れて見える。',
                       'approval_scope': '合成TESTの作画判断のみ。本編MASTER承認ではない',
                       'related': [], 'source_id': 'test:work02-report-001', 'proposed_by': 'work02'}
        self.auth_root = self.root / 'auth'
        memory_security.initialize(self.auth_root)
        self.token = memory_security.issue(self.auth_root, 'work02', 'all')
        self.env = patch.dict(os.environ, {'STUDIO_MEMORY_DIR': str(self.vault),
                                         'STUDIO_MEMORY_AUTH_DIR': str(self.auth_root)})
        self.env.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.env.stop()
        self.temp.cleanup()

    def _sign(self, assertion, role):
        message = self.root / 'message.json'
        signature = self.root / 'message.sig'
        message.write_bytes(memory_workflow._canonical(assertion))
        subprocess.run([memory_workflow._openssl(), 'pkeyutl', '-sign', '-inkey', str(self.keys / (role + '.private.pem')),
                        '-rawin', '-in', str(message), '-out', str(signature)], check=True, capture_output=True)
        return signature.read_bytes()

    def _submit(self, action, role, **kwargs):
        assertion = memory_workflow.prepare_assertion(self.workflow, self.fields['id'], action, role,
                                                      **kwargs)
        memory_workflow.apply_assertion(self.workflow, assertion, self._sign(assertion, role))
        return assertion

    def _propose(self):
        return memory_workflow.propose(self.workflow, self.report, self.fields)

    def _new_key(self, role, suffix):
        private = self.keys / f'{role}-{suffix}.private.pem'
        public = self.keys / f'{role}-{suffix}.public.pem'
        subprocess.run([memory_workflow._openssl(), 'genpkey', '-algorithm', 'Ed25519', '-out', str(private)],
                       check=True, capture_output=True)
        subprocess.run([memory_workflow._openssl(), 'pkey', '-in', str(private), '-pubout', '-out', str(public)],
                       check=True, capture_output=True)
        private.chmod(0o600)
        return private, public

    def test_full_flow_and_reader_search(self):
        proposed = self._propose()
        self.assertEqual(proposed['workflow_status'], 'DRAFT')
        self.assertFalse((self.vault / (self.fields['id'] + '.md')).exists())
        self._submit('DIRECTOR_REVIEWED', 'director')
        self.assertEqual(memory_workflow.status(self.workflow, self.fields['id'])['workflow_status'], 'DIRECTOR_REVIEWED')
        self._submit('PRODUCER_APPROVED', 'producer', approval_status='APPROVED')
        self.assertEqual(memory_workflow.status(self.workflow, self.fields['id'])['workflow_status'], 'PRODUCER_APPROVED')
        result = memory_workflow.register(self.workflow, self.fields['id'])
        self.assertEqual(result['conflicts'], [])
        auth = {'Authorization': 'Bearer ' + self.token}
        search = self.client.get('/api/studio/memory/search?q=合成TEST', headers=auth)
        self.assertEqual([item['id'] for item in search.json()['results']], [self.fields['id']])
        detail = self.client.get('/api/studio/memory/' + self.fields['id'], headers=auth).json()
        self.assertEqual(detail['approval_scope'], self.fields['approval_scope'])
        self.assertEqual(detail['approval_status'], 'APPROVED')
        self.assertEqual(detail['sources'], [self.fields['source_id']])
        self.assertEqual(memory_workflow.status(self.workflow, self.fields['id'])['workflow_status'], 'REGISTERED')
        diff = json.loads((self.workflow / 'diffs' / (self.fields['id'] + '.json')).read_text())
        self.assertIsNone(diff['before'])
        self.assertIn(self.fields['decision_excerpt'], diff['after'])
        log = (self.workflow / 'events' / (self.fields['id'] + '.jsonl')).read_text()
        self.assertNotIn(self.fields['decision_excerpt'], log)
        self.assertNotIn(self.fields['reason_excerpt'], log)
        self.assertNotIn(self.token, log)
        self.assertNotIn('signature"', log)

    def test_offline_cli_propose_packet_apply_register(self):
        fields_path = self.root / 'fields.json'
        fields_path.write_text(json.dumps(self.fields, ensure_ascii=False), encoding='utf-8')
        def cli(*args):
            return subprocess.run([sys.executable, '-m', 'tools.memory_workflow', '--root',
                                   str(self.workflow), *args], cwd=Path(__file__).parent,
                                  check=True, capture_output=True, text=True)
        created = cli('propose', '--report', str(self.report), '--fields', str(fields_path))
        self.assertIn('DRAFT', created.stdout)
        for action, role, extra in [('DIRECTOR_REVIEWED', 'director', []),
                                    ('PRODUCER_APPROVED', 'producer', ['--approval-status', 'APPROVED'])]:
            packet = self.root / (action + '.json')
            cli('packet', '--id', self.fields['id'], '--action', action, '--actor', role,
                *extra, '--out', str(packet))
            assertion = json.loads(packet.read_text())
            review = json.loads(Path(str(packet) + '.review.json').read_text())
            self.assertEqual(review['assertion'], assertion)
            self.assertEqual(review['canonical_assertion_sha256'],
                             memory_workflow._sha(packet.read_bytes()))
            signature = self.root / (action + '.sig')
            signature.write_bytes(self._sign(assertion, role))
            cli('apply', '--assertion', str(packet), '--signature', str(signature))
        registered = cli('register', '--id', self.fields['id'])
        self.assertIn(self.fields['id'], registered.stdout)
        self.assertEqual(json.loads(cli('status', '--id', self.fields['id']).stdout)['workflow_status'], 'REGISTERED')

    def test_unsigned_or_work_token_cannot_approve(self):
        self._propose()
        assertion = memory_workflow.prepare_assertion(self.workflow, self.fields['id'], 'DIRECTOR_REVIEWED', 'director')
        with self.assertRaises(ValueError):
            memory_workflow.apply_assertion(self.workflow, assertion, self.token.encode())
        with self.assertRaises(ValueError):
            memory_workflow.register(self.workflow, self.fields['id'])

    def test_expired_signed_assertion_rejected(self):
        self._propose()
        assertion = memory_workflow.prepare_assertion(self.workflow, self.fields['id'], 'DIRECTOR_REVIEWED', 'director')
        assertion['at'] = '2020-01-01T00:00:00+00:00'
        with self.assertRaises(ValueError):
            memory_workflow.apply_assertion(self.workflow, assertion, self._sign(assertion, 'director'))

    def test_producer_cannot_skip_director(self):
        self._propose()
        assertion = memory_workflow.prepare_assertion(self.workflow, self.fields['id'], 'PRODUCER_APPROVED', 'producer',
                                                      approval_status='APPROVED')
        with self.assertRaises(ValueError):
            memory_workflow.apply_assertion(self.workflow, assertion, self._sign(assertion, 'producer'))

    def test_event_action_tampering_is_rejected(self):
        self._propose()
        self._submit('DIRECTOR_REVIEWED', 'director')
        path = self.workflow / 'events' / (self.fields['id'] + '.jsonl')
        event = json.loads(path.read_text())
        event['action'] = 'PRODUCER_APPROVED'
        path.write_text(json.dumps(event) + '\n')
        assertion = memory_workflow.prepare_assertion(self.workflow, self.fields['id'], 'PRODUCER_APPROVED', 'producer',
                                                      approval_status='APPROVED')
        with self.assertRaises(ValueError):
            memory_workflow.apply_assertion(self.workflow, assertion, self._sign(assertion, 'producer'))

    def test_duplicate_and_no_overwrite(self):
        self._propose()
        with self.assertRaises(ValueError):
            self._propose()
        self._submit('DIRECTOR_REVIEWED', 'director')
        self._submit('PRODUCER_APPROVED', 'producer', approval_status='APPROVED')
        memory_workflow.register(self.workflow, self.fields['id'])
        original = (self.vault / (self.fields['id'] + '.md')).read_bytes()
        with self.assertRaises(ValueError):
            memory_workflow.register(self.workflow, self.fields['id'])
        self.assertEqual((self.vault / (self.fields['id'] + '.md')).read_bytes(), original)

    def test_source_and_scope_tampering_denied(self):
        self._propose()
        director = memory_workflow.prepare_assertion(self.workflow, self.fields['id'], 'DIRECTOR_REVIEWED', 'director')
        director['approval_scope'] = '本編MASTER承認'
        with self.assertRaises(ValueError):
            memory_workflow.apply_assertion(self.workflow, director, self._sign(director, 'director'))
        self._submit('DIRECTOR_REVIEWED', 'director')
        producer = memory_workflow.prepare_assertion(self.workflow, self.fields['id'], 'PRODUCER_APPROVED', 'producer',
                                                     approval_status='APPROVED')
        producer['approval_scope'] = '本編MASTER承認'
        with self.assertRaises(ValueError):
            memory_workflow.apply_assertion(self.workflow, producer, self._sign(producer, 'producer'))
        self._submit('PRODUCER_APPROVED', 'producer', approval_status='APPROVED')
        self.report.write_text('changed', encoding='utf-8')
        with self.assertRaises(ValueError):
            memory_workflow.register(self.workflow, self.fields['id'])

    def test_unverified_excerpt_and_unknown_fields(self):
        fields = {**self.fields, 'decision_excerpt': '報告書にない作り話'}
        with self.assertRaises(ValueError):
            memory_workflow.propose(self.workflow, self.report, fields)
        fields['decision_excerpt'] = memory_workflow.UNKNOWN
        fields['reason_excerpt'] = memory_workflow.UNKNOWN
        memory_workflow.propose(self.workflow, self.report, fields)
        self._submit('DIRECTOR_REVIEWED', 'director')
        assertion = memory_workflow.prepare_assertion(self.workflow, self.fields['id'], 'PRODUCER_APPROVED', 'producer',
                                                      approval_status='APPROVED')
        with self.assertRaises(ValueError):
            memory_workflow.apply_assertion(self.workflow, assertion, self._sign(assertion, 'producer'))

    def test_missing_related_memory_rejected_at_registration(self):
        self.fields['related'] = ['MISSING-MEMORY-001']
        self._propose()
        self._submit('DIRECTOR_REVIEWED', 'director')
        self._submit('PRODUCER_APPROVED', 'producer', approval_status='APPROVED')
        with self.assertRaises(ValueError):
            memory_workflow.register(self.workflow, self.fields['id'])

    def test_overlap_requires_signed_resolution(self):
        self._propose()
        existing = self.vault / 'EXISTING-KEY-001.md'
        existing.write_text('''---\nid: "EXISTING-KEY-001"\ntitle: "別の判断"\nkind: "test"\napproval_status: "APPROVED"\napproval_scope: "合成TESTのみ"\nsource: "test:old"\nsources: ["test:old"]\nupdated_at: "2026-10-23"\nrelated: []\nassets: ["SYNTHETIC-KEY-01"]\n---\n\n# old\n''', encoding='utf-8')
        self._submit('DIRECTOR_REVIEWED', 'director')
        self._submit('PRODUCER_APPROVED', 'producer', approval_status='APPROVED')
        with self.assertRaises(ValueError):
            memory_workflow.register(self.workflow, self.fields['id'])

    def test_signed_conflict_acknowledgement_allows_registration(self):
        self._propose()
        existing = self.vault / 'EXISTING-KEY-001.md'
        existing.write_text('''---\nid: "EXISTING-KEY-001"\ntitle: "別の判断"\nkind: "test"\napproval_status: "APPROVED"\napproval_scope: "合成TESTのみ"\nsource: "test:old"\nsources: ["test:old"]\nupdated_at: "2026-10-23"\nrelated: []\nassets: ["SYNTHETIC-KEY-01"]\n---\n\n# old\n''', encoding='utf-8')
        self._submit('DIRECTOR_REVIEWED', 'director')
        self._submit('PRODUCER_APPROVED', 'producer', approval_status='APPROVED',
                     accepted_conflicts=['EXISTING-KEY-001'])
        result = memory_workflow.register(self.workflow, self.fields['id'])
        self.assertEqual(result['conflicts'], ['EXISTING-KEY-001'])
        self.assertEqual(existing.read_text().splitlines()[1], 'id: "EXISTING-KEY-001"')

    def test_rejection_has_reason_and_no_registration(self):
        self._propose()
        self._submit('REJECTED', 'producer', reason='出典の解釈が不十分')
        self.assertEqual(memory_workflow.status(self.workflow, self.fields['id'])['workflow_status'], 'REJECTED')
        with self.assertRaises(ValueError):
            memory_workflow.register(self.workflow, self.fields['id'])

    def test_signed_revocation_archives_without_deleting_history(self):
        self._propose()
        self._submit('DIRECTOR_REVIEWED', 'director')
        self._submit('PRODUCER_APPROVED', 'producer', approval_status='APPROVED')
        memory_workflow.register(self.workflow, self.fields['id'])
        before = (self.workflow / 'events' / (self.fields['id'] + '.jsonl')).read_text()
        self._submit('REVOKED', 'producer', reason='合成TESTの判断を撤回')
        self.assertEqual(memory_workflow.status(self.workflow, self.fields['id'])['workflow_status'], 'REVOKED')
        self.assertFalse((self.vault / (self.fields['id'] + '.md')).exists())
        self.assertEqual(len(list((self.workflow / 'archive').glob(self.fields['id'] + '.*.md'))), 1)
        self.assertTrue((self.workflow / 'events' / (self.fields['id'] + '.jsonl')).read_text().startswith(before))
        auth = {'Authorization': 'Bearer ' + self.token}
        self.assertEqual(self.client.get('/api/studio/memory/' + self.fields['id'], headers=auth).status_code, 404)

    def test_review_packet_binds_source_body_and_scope(self):
        self._propose()
        review = memory_workflow.review_packet(self.workflow, self.fields['id'], 'DIRECTOR_REVIEWED', 'human-reviewer')
        self.assertTrue(review['unsigned'])
        self.assertEqual(review['source_sha256'], memory_workflow._sha(self.report.read_bytes()))
        self.assertEqual(review['approval_scope'], self.fields['approval_scope'])
        self.assertEqual(review['body_sha256'], review['assertion']['body_sha256'])
        self.assertEqual(memory_workflow.status(self.workflow, self.fields['id'])['workflow_status'], 'DRAFT')

    def test_signed_body_change_and_wrong_key_rejected(self):
        self._propose()
        assertion = memory_workflow.prepare_assertion(self.workflow, self.fields['id'], 'DIRECTOR_REVIEWED', 'reviewer')
        assertion['body_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            memory_workflow.apply_assertion(self.workflow, assertion, self._sign(assertion, 'director'))
        assertion = memory_workflow.prepare_assertion(self.workflow, self.fields['id'], 'DIRECTOR_REVIEWED', 'reviewer')
        with self.assertRaises(ValueError):
            memory_workflow.apply_assertion(self.workflow, assertion, self._sign(assertion, 'producer'))

    def test_reused_signature_and_nonce_rejected(self):
        self._propose()
        assertion = self._submit('DIRECTOR_REVIEWED', 'director')
        with self.assertRaisesRegex(ValueError, 'already used'):
            memory_workflow.apply_assertion(self.workflow, assertion, self._sign(assertion, 'director'))

    def test_director_rotation_preserves_history_and_rejects_old_key(self):
        self._propose()
        self._submit('DIRECTOR_REVIEWED', 'director')
        private, public = self._new_key('director', 'new')
        packet = memory_workflow.prepare_key_change(self.workflow, 'director', 'ROTATE', 'producer-human',
                                                    new_public=public, reason='planned rotation')
        result = memory_workflow.apply_key_change(self.workflow, packet, self._sign(packet, 'producer'),
                                                  new_public=public)
        self.assertEqual(result['state'], 'rotated')
        self.assertEqual(memory_workflow.key_audit(self.workflow)[0]['action'], 'ROTATE')
        self.assertEqual(memory_workflow.status(self.workflow, self.fields['id'])['workflow_status'], 'DIRECTOR_REVIEWED')
        with self.assertRaises(ValueError):
            memory_workflow.apply_key_change(self.workflow, packet, self._sign(packet, 'producer'), new_public=public)
        new_packet = memory_workflow.prepare_assertion(self.workflow, self.fields['id'], 'PRODUCER_APPROVED', 'producer',
                                                       approval_status='APPROVED')
        memory_workflow.apply_assertion(self.workflow, new_packet, self._sign(new_packet, 'producer'))
        memory_workflow.register(self.workflow, self.fields['id'])
        self.assertTrue(private.exists())  # only synthetic test key outside workflow root
        self.assertFalse(list(self.workflow.rglob('*.private.pem')))

    def test_revoked_producer_key_blocks_pending_registration(self):
        self._propose()
        self._submit('DIRECTOR_REVIEWED', 'director')
        self._submit('PRODUCER_APPROVED', 'producer', approval_status='APPROVED')
        _, public = self._new_key('producer', 'new')
        packet = memory_workflow.prepare_key_change(self.workflow, 'producer', 'ROTATE', 'producer-human',
                                                    new_public=public, reason='planned rotation')
        memory_workflow.apply_key_change(self.workflow, packet, self._sign(packet, 'producer'), new_public=public)
        with self.assertRaisesRegex(ValueError, 'revoked'):
            memory_workflow.register(self.workflow, self.fields['id'])
        self.assertFalse((self.vault / (self.fields['id'] + '.md')).exists())

    def test_key_management_requires_current_producer_signature(self):
        _, public = self._new_key('director', 'new')
        packet = memory_workflow.prepare_key_change(self.workflow, 'director', 'ROTATE', 'producer-human',
                                                    new_public=public, reason='planned rotation')
        with self.assertRaises(ValueError):
            memory_workflow.apply_key_change(self.workflow, packet, self._sign(packet, 'director'), new_public=public)
        public.write_text('changed', encoding='utf-8')
        with self.assertRaises(ValueError):
            memory_workflow.apply_key_change(self.workflow, packet, self._sign(packet, 'producer'), new_public=public)

    def test_work_reader_token_cannot_manage_keys(self):
        _, public = self._new_key('director', 'new')
        packet = memory_workflow.prepare_key_change(self.workflow, 'director', 'ROTATE', 'producer-human',
                                                    new_public=public, reason='planned rotation')
        with self.assertRaises(ValueError):
            memory_workflow.apply_key_change(self.workflow, packet, self.token.encode(), new_public=public)

    def test_director_revocation_blocks_new_reviews_and_preserves_audit(self):
        self._propose()
        packet = memory_workflow.prepare_key_change(self.workflow, 'director', 'REVOKE', 'producer-human',
                                                    reason='synthetic compromise')
        memory_workflow.apply_key_change(self.workflow, packet, self._sign(packet, 'producer'))
        self.assertEqual(memory_workflow.key_audit(self.workflow)[0]['action'], 'REVOKE')
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            memory_workflow.prepare_assertion(self.workflow, self.fields['id'], 'DIRECTOR_REVIEWED', 'reviewer')

    def test_management_proof_tampering_detected(self):
        _, public = self._new_key('director', 'new')
        packet = memory_workflow.prepare_key_change(self.workflow, 'director', 'ROTATE', 'producer-human',
                                                    new_public=public, reason='planned rotation')
        memory_workflow.apply_key_change(self.workflow, packet, self._sign(packet, 'producer'), new_public=public)
        proof = next((self.workflow / 'proofs').glob('key-change.*.sig'))
        proof.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'proof changed'):
            memory_workflow.key_audit(self.workflow)


if __name__ == '__main__':
    unittest.main()
