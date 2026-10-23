"""Synthetic Gate 1 protocol check; this is not a protected production witness."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from app import memory_backup, memory_workflow as workflow


class Gate1WitnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.roots = {}
        for label in memory_backup.LABELS:
            root = self.base / label
            root.mkdir(mode=0o700)
            self.roots[label] = root
        workflow._new_file(self.roots['vault'] / 'SYNTHETIC-001.md', b'approval_status: DRAFT\n')
        self.anchor = self.base / 'working-anchor'
        self.anchor.mkdir(mode=0o700)
        self.first = self.base / 'snapshot-1'
        self.second = self.base / 'snapshot-2'
        memory_backup.create_snapshot(self.roots, self.first, self.anchor)
        workflow._new_file(self.roots['vault'] / 'SYNTHETIC-002.md', b'approval_status: DRAFT\n')
        memory_backup.create_snapshot(self.roots, self.second, self.anchor)

    def _receipt(self, snapshot):
        manifest = memory_backup.verify_snapshot(snapshot)
        return {'version': 1, 'snapshot_id': snapshot.name,
                'sequence': manifest['sequence'],
                'manifest_sha256': hashlib.sha256((snapshot / 'manifest.json').read_bytes()).hexdigest()}

    def _admit(self, snapshot, protected_receipt):
        if protected_receipt is None:
            raise ValueError('no independent receipt')
        if set(protected_receipt) != {'version', 'snapshot_id', 'sequence', 'manifest_sha256'} or protected_receipt['version'] != 1:
            raise ValueError('invalid independent receipt')
        manifest = memory_backup.verify_snapshot(snapshot)
        if snapshot.name != protected_receipt['snapshot_id'] or manifest['sequence'] != protected_receipt['sequence']:
            raise ValueError('old or unreceived snapshot')
        actual_sha = hashlib.sha256((snapshot / 'manifest.json').read_bytes()).hexdigest()
        if actual_sha != protected_receipt['manifest_sha256']:
            raise ValueError('manifest does not match receipt')
        return True

    def test_latest_received_snapshot_accepted(self):
        self.assertTrue(self._admit(self.second, self._receipt(self.second)))

    def test_old_snapshot_rejected_even_if_working_anchor_rolled_back(self):
        (self.anchor / 'state.json').write_text(json.dumps({'version': 1, 'sequence': 1}))
        with self.assertRaisesRegex(ValueError, 'old or unreceived'):
            self._admit(self.first, self._receipt(self.second))

    def test_modified_snapshot_rejected(self):
        receipt = self._receipt(self.second)
        (self.second / 'vault' / 'SYNTHETIC-002.md').write_text('approval_status: APPROVED\n')
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            self._admit(self.second, receipt)

    def test_missing_or_unreceived_receipt_rejected(self):
        with self.assertRaisesRegex(ValueError, 'no independent receipt'):
            self._admit(self.second, None)
        with self.assertRaisesRegex(ValueError, 'old or unreceived'):
            self._admit(self.second, self._receipt(self.first))


if __name__ == '__main__':
    unittest.main()
