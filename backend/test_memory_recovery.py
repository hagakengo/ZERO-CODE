"""Fault injection uses only synthetic reports and isolated private stores."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from unittest.mock import patch

from app import memory_backup, memory_drafts, memory_security, memory_submission, memory_workflow as workflow
from test_memory_submission import setup


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def _case(self, name):
        directory = self.base / name
        directory.mkdir()
        return setup(directory)

    def _crash_and_recover(self, stage):
        root, inbox, client, envelope = self._case(stage)
        if stage == 'after_source':
            with patch.object(workflow, 'build_candidate', side_effect=SystemExit(67)):
                with self.assertRaises(SystemExit):
                    memory_submission.accept(root, envelope)
        elif stage == 'after_candidate':
            original = memory_drafts.add
            def stop_after_add(*args, **kwargs):
                original(*args, **kwargs)
                raise SystemExit(67)
            with patch.object(memory_drafts, 'add', side_effect=stop_after_add):
                with self.assertRaises(SystemExit):
                    memory_submission.accept(root, envelope)
        elif stage == 'before_receipt':
            original = workflow._new_file
            def stop_at_receipt(path, data):
                if Path(path).parent.name == 'receipts':
                    raise SystemExit(67)
                return original(path, data)
            with patch.object(workflow, '_new_file', side_effect=stop_at_receipt):
                with self.assertRaises(SystemExit):
                    memory_submission.accept(root, envelope)
        elif stage == 'after_receipt':
            original = memory_submission._audit
            def stop_after_receipt(root, work, result, receipt_id=None):
                if result == 'READY_FOR_REVIEW':
                    raise SystemExit(67)
                return original(root, work, result, receipt_id)
            with patch.object(memory_submission, '_audit', side_effect=stop_after_receipt):
                with self.assertRaises(SystemExit):
                    memory_submission.accept(root, envelope)
        self.assertTrue(list((root / 'transactions').glob('*.json')))
        recovered = memory_submission.recover(root)
        self.assertEqual(len(recovered), 1)
        self.assertEqual(memory_submission.integrity_check(root)['state'], 'MATCH')
        self.assertEqual(len(memory_drafts.list_candidates(inbox)), 1)
        self.assertFalse(list((root / 'transactions').glob('*.json')))
        self.assertEqual(memory_submission.accept(root, envelope)['approval_status'], 'DRAFT')

    def test_recovery_after_source_copy(self):
        self._crash_and_recover('after_source')

    def test_recovery_after_candidate_commit(self):
        self._crash_and_recover('after_candidate')

    def test_recovery_before_receipt(self):
        self._crash_and_recover('before_receipt')

    def test_recovery_after_receipt(self):
        self._crash_and_recover('after_receipt')

    def test_real_process_exit_and_restart(self):
        root, inbox, client, envelope = self._case('process-exit')
        payload = self.base / 'payload.json'
        payload.write_text(json.dumps(envelope), encoding='utf-8')
        program = '''import json, os, sys
from pathlib import Path
from app import memory_submission, memory_workflow
def die(*args, **kwargs):
    os._exit(67)
memory_workflow.build_candidate = die
memory_submission.accept(Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text()))
'''
        result = subprocess.run([sys.executable, '-c', program, str(root), str(payload)],
                                cwd=Path(__file__).parent, capture_output=True)
        self.assertEqual(result.returncode, 67)
        self.assertFalse(list((root / 'receipts').glob('*.json')))
        self.assertEqual(memory_submission.recover(root)[0]['state'], 'READY_FOR_REVIEW')
        self.assertEqual(memory_submission.integrity_check(root)['state'], 'MATCH')
        self.assertEqual(memory_drafts.detail(inbox, envelope['fields']['id'])['candidate']['approval_status'], 'DRAFT')

    def test_audit_failure_keeps_unfinished_transaction(self):
        root, inbox, client, envelope = self._case('audit-failure')
        original = memory_submission._audit
        def fail_validated(root_path, work, result, receipt_id=None):
            if result == 'VALIDATED':
                raise OSError('synthetic audit disk failure')
            return original(root_path, work, result, receipt_id)
        with patch.object(memory_submission, '_audit', side_effect=fail_validated):
            with self.assertRaises(OSError):
                memory_submission.accept(root, envelope)
        self.assertFalse(list((root / 'receipts').glob('*.json')))
        self.assertEqual(len(list((root / 'transactions').glob('*.json'))), 1)
        self.assertEqual(memory_submission.recover(root)[0]['state'], 'READY_FOR_REVIEW')
        self.assertEqual(memory_submission.integrity_check(root)['state'], 'MATCH')

    def test_candidate_not_visible_before_annotation(self):
        root, inbox, client, envelope = self._case('list-race')
        original = workflow._new_file
        paused, release = Event(), Event()
        def pause_candidate(path, data):
            if Path(path).parent.name == 'candidates':
                paused.set()
                if not release.wait(5):
                    raise TimeoutError('candidate pause timed out')
            return original(path, data)
        with ThreadPoolExecutor(max_workers=2) as pool:
            with patch.object(workflow, '_new_file', side_effect=pause_candidate):
                future = pool.submit(memory_submission.accept, root, envelope)
                self.assertTrue(paused.wait(5))
                self.assertEqual(memory_drafts.list_candidates(inbox), [])
                release.set()
                self.assertEqual(future.result()['approval_status'], 'DRAFT')
        self.assertEqual(len(memory_drafts.list_candidates(inbox)), 1)

    def test_concurrent_same_receipt_and_candidate(self):
        root, inbox, client, envelope = self._case('concurrent')
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: memory_submission.accept(root, envelope), range(8)))
        self.assertEqual({x['receipt_id'] for x in results}, {envelope['receipt_id']})
        self.assertEqual(len(memory_drafts.list_candidates(inbox)), 1)
        second = {**envelope, 'receipt_id': 'a' * 32}
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda item: memory_submission.accept(root, item), (envelope, second)))
        self.assertEqual(len(memory_drafts.list_candidates(inbox)), 1)
        self.assertEqual(len(memory_submission.list_receipts(root)), 2)
        self.assertIn('MATCHED_EXISTING_DRAFT', [x['disposition'] for x in results])

    def test_corrupt_receipt_blocks_restart(self):
        root, inbox, client, envelope = self._case('corrupt')
        memory_submission.accept(root, envelope)
        path = root / 'receipts' / (envelope['receipt_id'] + '.json')
        changed = json.loads(path.read_text())
        changed['source_sha256'] = '0' * 64
        path.write_text(json.dumps(changed))
        with self.assertRaises(ValueError):
            memory_submission.create_app(root)
        self.assertEqual(memory_drafts.list_candidates(inbox)[0]['approval_status'], 'DRAFT')

    def test_backup_restore_rollback_and_corruption(self):
        root, inbox, client, envelope = self._case('backup')
        memory_submission.accept(root, envelope)
        reader = self.base / 'reader'
        memory_security.initialize(reader)
        workflow_root = self.base / 'workflow'
        workflow_root.mkdir(mode=0o700)
        workflow._new_file(workflow_root / 'synthetic-public-registry.json', b'{"synthetic":true}')
        vault = self.base / 'backup' / 'vault'
        vault.chmod(0o700)
        synthetic_note = vault / 'SYNTHETIC-001.md'
        workflow._new_file(synthetic_note, b'---\nid: SYNTHETIC-001\napproval_status: DRAFT\n---\n\nSynthetic only.\n')
        anchor = self.base / 'anchor'
        anchor.mkdir(mode=0o700)
        roots = {'submission': root, 'drafts': inbox, 'vault': vault,
                 'workflow': workflow_root, 'reader_auth': reader}
        first = self.base / 'snapshot-1'
        second = self.base / 'snapshot-2'
        self.assertEqual(memory_backup.create_snapshot(roots, first, anchor)['sequence'], 1)
        workflow._new_file(workflow_root / 'audit.jsonl', b'{"event":"synthetic"}\n')
        self.assertEqual(memory_backup.create_snapshot(roots, second, anchor)['sequence'], 2)
        with self.assertRaisesRegex(ValueError, 'rollback'):
            memory_backup.restore_snapshot(first, self.base / 'old-restored', anchor)
        restored = self.base / 'restored'
        result = memory_backup.restore_snapshot(second, restored, anchor)
        self.assertFalse(result['signing_secrets_restored'])
        self.assertFalse((restored / 'submission' / 'key').exists())
        self.assertFalse((restored / 'reader_auth' / 'signing.key').exists())
        self.assertEqual((restored / 'drafts' / 'candidates' / (envelope['fields']['id'] + '.json')).read_bytes(),
                         (inbox / 'candidates' / (envelope['fields']['id'] + '.json')).read_bytes())
        self.assertEqual((restored / 'vault' / synthetic_note.name).read_bytes(), synthetic_note.read_bytes())
        self.assertEqual(memory_backup.verify_snapshot(restored)['sequence'], 2)
        corrupt = second / 'submission' / 'receipts' / (envelope['receipt_id'] + '.json')
        corrupt.write_text('damaged')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            memory_backup.restore_snapshot(second, self.base / 'corrupt-restored', anchor)
