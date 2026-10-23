"""Offline, copy-only private Studio Memory snapshots; no real signer secrets."""
import json
import os
import secrets
import stat
from pathlib import Path

from app import memory_security, memory_workflow as workflow

LABELS = {'submission', 'drafts', 'vault', 'workflow', 'reader_auth'}
EXCLUDED = {('submission', 'key'), ('reader_auth', 'signing.key')}
MAX_FILE = 4 * 1024 * 1024


def _private_dir(path):
    root = Path(path)
    info = root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('unsafe private directory')
    return root


def _files(root):
    for path in sorted(root.rglob('*')):
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or info.st_uid != os.getuid():
            raise ValueError('unsafe snapshot source')
        if stat.S_ISREG(info.st_mode):
            if info.st_size > MAX_FILE:
                raise ValueError('oversized snapshot file')
            yield path
        elif not stat.S_ISDIR(info.st_mode):
            raise ValueError('unsupported snapshot entry')


def _anchor(root):
    path = root / 'state.json'
    if not path.exists():
        return {'version': 1, 'sequence': 0}
    value = json.loads(memory_security._private_file(path))
    if set(value) != {'version', 'sequence'} or value['version'] != 1 or type(value['sequence']) is not int or value['sequence'] < 0:
        raise ValueError('invalid backup anchor')
    return value


def _inventory(root, label):
    return {(label, path.relative_to(root).as_posix()): workflow._sha(workflow._read_file(path, MAX_FILE))
            for path in _files(root) if (label, path.relative_to(root).as_posix()) not in EXCLUDED}


def create_snapshot(roots, destination, anchor_path):
    if set(roots) != LABELS:
        raise ValueError('all private stores are required')
    anchor = _private_dir(anchor_path)
    sources = {label: _private_dir(value) for label, value in roots.items()}
    before = {label: _inventory(root, label) for label, root in sources.items()}
    destination = Path(destination)
    if destination.exists():
        raise ValueError('snapshot already exists')
    stage = destination.with_name('.snapshot-' + secrets.token_hex(16))
    stage.mkdir(mode=0o700)
    files = []
    try:
        for label, source_root in sorted(sources.items()):
            for original in _files(source_root):
                relative = original.relative_to(source_root)
                if (label, relative.as_posix()) in EXCLUDED:
                    continue
                target = stage / label / relative
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                data = workflow._read_file(original, MAX_FILE)
                workflow._new_file(target, data)
                files.append({'label': label, 'path': relative.as_posix(),
                              'sha256': workflow._sha(data), 'size': len(data)})
        if any(_inventory(root, label) != before[label] for label, root in sources.items()):
            raise ValueError('source changed during backup')
        sequence = _anchor(anchor)['sequence'] + 1
        manifest = {'version': 1, 'sequence': sequence, 'files': files,
                    'created_at': workflow._now(), 'secrets_excluded': sorted([list(x) for x in EXCLUDED])}
        workflow._new_file(stage / 'manifest.json', workflow._canonical(manifest))
        verify_snapshot(stage)
        os.replace(stage, destination)
        state = {'version': 1, 'sequence': sequence}
        path = anchor / 'state.json'
        if path.exists():
            workflow._replace_private_file(path, workflow._canonical(state))
        else:
            workflow._new_file(path, workflow._canonical(state))
        return {'sequence': sequence, 'files': len(files), 'manifest_sha256': workflow._sha(workflow._canonical(manifest))}
    except Exception:
        # An incomplete stage is never a usable snapshot and is kept for inspection.
        raise


def verify_snapshot(snapshot_path):
    root = _private_dir(snapshot_path)
    manifest = json.loads(memory_security._private_file(root / 'manifest.json', size_limit=MAX_FILE))
    if manifest.get('version') != 1 or type(manifest.get('sequence')) is not int or manifest['sequence'] < 1 or not isinstance(manifest.get('files'), list):
        raise ValueError('invalid snapshot manifest')
    expected = set()
    for item in manifest['files']:
        if set(item) != {'label', 'path', 'sha256', 'size'} or item['label'] not in LABELS:
            raise ValueError('invalid snapshot item')
        relative = Path(item['path'])
        if relative.is_absolute() or '..' in relative.parts or (item['label'], relative.as_posix()) in EXCLUDED:
            raise ValueError('unsafe snapshot path')
        path = root / item['label'] / relative
        data = workflow._read_file(path, MAX_FILE)
        if len(data) != item['size'] or workflow._sha(data) != item['sha256']:
            raise ValueError('snapshot hash mismatch')
        expected.add(path.relative_to(root).as_posix())
    actual = {path.relative_to(root).as_posix() for path in _files(root)
              if path.relative_to(root).as_posix() != 'manifest.json'}
    if actual != expected:
        raise ValueError('snapshot file inventory mismatch')
    return manifest


def restore_snapshot(snapshot_path, destination, anchor_path):
    anchor = _private_dir(anchor_path)
    manifest = verify_snapshot(snapshot_path)
    if manifest['sequence'] < _anchor(anchor)['sequence']:
        raise ValueError('backup rollback detected')
    destination = Path(destination)
    if destination.exists():
        raise ValueError('restoration destination already exists')
    stage = destination.with_name('.restore-' + secrets.token_hex(16))
    stage.mkdir(mode=0o700)
    for item in manifest['files']:
        source = Path(snapshot_path) / item['label'] / item['path']
        target = stage / item['label'] / item['path']
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        workflow._new_file(target, workflow._read_file(source, MAX_FILE))
    workflow._new_file(stage / 'manifest.json', workflow._canonical(manifest))
    verify_snapshot(stage)
    os.replace(stage, destination)
    return {'sequence': manifest['sequence'], 'files': len(manifest['files']),
            'requires_rebinding': True, 'signing_secrets_restored': False}
