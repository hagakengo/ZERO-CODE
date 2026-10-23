import hashlib
import json
import os
import secrets
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import memory_drafts, memory_security, memory_submission, memory_workflow as workflow


def setup(tmp_path):
    vault = tmp_path / 'vault'
    vault.mkdir(mode=0o700)
    inbox = tmp_path / 'inbox'
    memory_drafts.initialize(inbox, vault)
    root = tmp_path / 'submission'
    memory_submission.initialize(root, inbox)
    source = '技術PASS／演出・作画REWORK。\n追視は保持原画の切替段差と眼軸の精密な対応が残る。\n'
    fields = {'id': 'WORK02-EP00-R03-001', 'title': 'r03 test', 'kind': 'production_result',
        'characters': ['ユナ'], 'assets': ['r03.mp4'], 'episodes': ['EP00'],
        'decision_excerpt': '技術PASS／演出・作画REWORK。',
        'reason_excerpt': '追視は保持原画の切替段差と眼軸の精密な対応が残る。',
        'approval_scope': 'TEST制作結果のみ。MASTER・公開承認を含まない。',
        'related': [], 'source_id': 'WORK02-R03-REPORT', 'proposed_by': 'work02'}
    envelope = {'receipt_id': secrets.token_hex(16), 'source_text': source,
        'source_sha256': hashlib.sha256(source.encode()).hexdigest(), 'fields': fields,
        'project': 'ZERO CODE', 'unknowns': [], 'workflow_status': 'DRAFT', 'approval_status': 'DRAFT'}
    client = TestClient(memory_submission.create_app(root))
    return root, inbox, client, envelope


def send(client, token, envelope):
    return client.post('/submit', json=envelope, headers={'Authorization': 'Bearer ' + token})


def check_submit_retry_and_candidate_conflict(tmp_path):
    root, inbox, client, envelope = setup(tmp_path)
    token = memory_submission.issue(root)
    first = send(client, token, envelope)
    assert first.status_code == 200
    assert first.json()['submission_status'] == 'READY_FOR_REVIEW'
    assert first.json()['approval_status'] == 'DRAFT'
    assert send(client, token, envelope).json() == first.json()
    assert len(memory_drafts.list_candidates(inbox)) == 1
    assert memory_drafts.review_packet(inbox, envelope['fields']['id'])['formal_signature'] is False
    conflict = {**envelope, 'receipt_id': secrets.token_hex(16),
                'fields': {**envelope['fields'], 'approval_scope': 'MASTER承認'}}
    assert send(client, token, conflict).status_code == 422
    assert len(memory_drafts.list_candidates(inbox)) == 1


def check_existing_draft_same_source_matches_without_overwrite(tmp_path):
    root, inbox, client, envelope = setup(tmp_path)
    original = tmp_path / 'original.md'
    original.write_text(envelope['source_text'])
    fields = {**envelope['fields'], 'proposed_by': 'work01'}
    memory_drafts.add(inbox, original, fields)
    before = (inbox / 'candidates' / (fields['id'] + '.json')).read_bytes()
    result = send(client, memory_submission.issue(root), envelope)
    assert result.status_code == 200
    assert result.json()['disposition'] == 'MATCHED_EXISTING_DRAFT'
    assert (inbox / 'candidates' / (fields['id'] + '.json')).read_bytes() == before


def check_auth_expiry_revocation_and_reader_token_rejected(tmp_path):
    root, inbox, client, envelope = setup(tmp_path)
    assert client.post('/submit', json=envelope).status_code == 401
    assert send(client, 'wrong', envelope).status_code == 401
    expired = memory_submission.issue(root, ttl=1, now=1)
    assert send(client, expired, envelope).status_code == 401
    reader = tmp_path / 'reader'
    memory_security.initialize(reader)
    assert send(client, memory_security.issue(reader, 'work02', 'all'), envelope).status_code == 401
    token = memory_submission.issue(root)
    memory_submission.revoke_work(root)
    assert send(client, token, envelope).status_code == 401
    assert memory_drafts.list_candidates(inbox) == []


INVALID_CHANGES = [
    lambda x: x.update(source_sha256='0' * 64),
    lambda x: x['fields'].update(reason_excerpt='未出典の理由'),
    lambda x: x.update(approval_status='APPROVED'),
    lambda x: x['fields'].update(proposed_by='work01'),
    lambda x: x['fields'].update(source_id=['invalid']),
    lambda x: x.update(source_text='x' * 262145),
    lambda x: x.update(source_path='/private/unauthorized'),
]
def check_invalid_submissions_are_not_accepted(tmp_path, change):
    root, inbox, client, envelope = setup(tmp_path)
    change(envelope)
    assert send(client, memory_submission.issue(root), envelope).status_code == 422
    assert memory_drafts.list_candidates(inbox) == []
    assert list((root / 'receipts').iterdir()) == []


def check_symlink_source_and_audit_redaction(tmp_path):
    root, inbox, client, envelope = setup(tmp_path)
    source = root / 'sources' / (envelope['receipt_id'] + '.md')
    source.symlink_to(tmp_path / 'missing')
    assert send(client, memory_submission.issue(root), envelope).status_code == 422
    assert not list((root / 'receipts').iterdir())
    audit = (root / 'audit.jsonl').read_text()
    assert envelope['source_text'] not in audit
    assert envelope['fields']['decision_excerpt'] not in audit


class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_submit_retry_and_conflict(self):
        check_submit_retry_and_candidate_conflict(self.root)

    def test_existing_candidate_preserved(self):
        check_existing_draft_same_source_matches_without_overwrite(self.root)

    def test_auth_boundaries(self):
        check_auth_expiry_revocation_and_reader_token_rejected(self.root)

    def test_invalid_submissions(self):
        for index, change in enumerate(INVALID_CHANGES):
            with self.subTest(index=index):
                case = self.root / str(index)
                case.mkdir()
                check_invalid_submissions_are_not_accepted(case, change)

    def test_symlink_and_audit(self):
        check_symlink_source_and_audit_redaction(self.root)

    def test_review_packet_separates_qc(self):
        root, inbox, client, envelope = setup(self.root)
        result = send(client, memory_submission.issue(root), envelope)
        self.assertEqual(result.status_code, 200)
        packet = memory_submission.review_packet(root, envelope['receipt_id'])
        self.assertEqual(packet['qc_distinction']['technical_qc'], 'PASS')
        self.assertEqual(packet['qc_distinction']['direction_and_drawing_qc'], 'REWORK')
        self.assertFalse(packet['formal_signature'])

    def test_incomplete_receipt_rolls_back_new_candidate(self):
        root, inbox, client, envelope = setup(self.root)
        original = workflow._new_file
        def fail_receipt(path, data):
            if Path(path).parent.name == 'receipts':
                raise OSError('simulated storage interruption')
            return original(path, data)
        with patch.object(workflow, '_new_file', side_effect=fail_receipt):
            self.assertEqual(send(client, memory_submission.issue(root), envelope).status_code, 422)
        self.assertEqual(memory_drafts.list_candidates(inbox), [])
        self.assertEqual(list((root / 'receipts').iterdir()), [])
