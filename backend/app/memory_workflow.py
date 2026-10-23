"""Offline, human-signed Studio Memory proposal and registration workflow.

This module is deliberately absent from the FastAPI reader. It never accepts a
Reader token as authority to review, approve, reject, or register a memory.
"""
import fcntl
import hashlib
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.studio_memory import ID, STATUSES, _parse

ROLES = {'director', 'producer'}
REVIEW_ACTIONS = {'DIRECTOR_REVIEWED', 'PRODUCER_APPROVED', 'REJECTED', 'REVOKED'}
SOURCE_ID = re.compile(r'^[A-Za-z0-9:_-]{3,120}$')
REQUIRED = {'id', 'title', 'kind', 'characters', 'assets', 'episodes', 'decision_excerpt',
            'reason_excerpt', 'approval_scope', 'related', 'source_id', 'proposed_by'}
UNKNOWN = '未確認'


def _now():
    return datetime.now(timezone.utc).isoformat()


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _private_root(path):
    root = Path(path)
    info = root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('unsafe workflow directory')
    return root


def _read_file(path, limit=262144):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            raise ValueError('unsafe source file')
        data = os.read(fd, limit + 1)
        if len(data) > limit:
            raise ValueError('source file too large')
        return data
    finally:
        os.close(fd)


def _new_file(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        Path(path).unlink(missing_ok=True)
        raise


def initialize(root_path, vault_path, director_public, producer_public):
    root = Path(root_path)
    vault = Path(vault_path).resolve(strict=True)
    if not vault.is_dir() or root.exists():
        raise ValueError('workflow root exists or vault is unavailable')
    keys = {role: _read_file(path, 8192) for role, path in
            [('director', director_public), ('producer', producer_public)]}
    if any(b'PUBLIC KEY' not in key for key in keys.values()):
        raise ValueError('public approval key required')
    root.mkdir(mode=0o700)
    for name in ('candidates', 'events', 'diffs', 'archive', 'proofs', 'keys'):
        (root / name).mkdir(mode=0o700)
    for role, key in keys.items():
        _new_file(root / 'keys' / (role + '.pem'), key)
    _new_file(root / 'config.json', _canonical({'version': 1, 'vault': str(vault)}))
    return root


def _config(root):
    data = json.loads(_read_file(root / 'config.json', 8192))
    if set(data) != {'version', 'vault'} or data['version'] != 1:
        raise ValueError('invalid workflow configuration')
    vault = Path(data['vault'])
    if not vault.is_dir() or vault.is_symlink():
        raise ValueError('vault unavailable')
    return vault


def _candidate(root, memory_id):
    if not ID.fullmatch(memory_id):
        raise ValueError('invalid memory ID')
    data = json.loads(_read_file(root / 'candidates' / (memory_id + '.json')))
    if data.get('id') != memory_id or data.get('workflow_status') != 'DRAFT':
        raise ValueError('invalid candidate')
    return data


def _events(root, memory_id):
    path = root / 'events' / (memory_id + '.jsonl')
    if not path.exists():
        return []
    data = _read_file(path)
    return [json.loads(line) for line in data.splitlines() if line]


def _append_event(root, memory_id, event):
    path = root / 'events' / (memory_id + '.jsonl')
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('unsafe event file')
        fcntl.flock(fd, fcntl.LOCK_EX)
        os.write(fd, _canonical(event) + b'\n')
        os.fsync(fd)
    finally:
        os.close(fd)


def _verify_signature(root, role, payload, signature):
    if role not in ROLES or len(signature) > 1024:
        raise ValueError('invalid approval signature')
    with tempfile.TemporaryDirectory() as temporary:
        message = Path(temporary) / 'message'
        signed = Path(temporary) / 'signature'
        message.write_bytes(_canonical(payload))
        signed.write_bytes(signature)
        result = subprocess.run([_openssl(), 'pkeyutl', '-verify', '-pubin', '-inkey',
                                 str(root / 'keys' / (role + '.pem')), '-rawin',
                                 '-in', str(message), '-sigfile', str(signed)],
                                capture_output=True, timeout=10, check=False)
        if result.returncode != 0:
            raise ValueError('approval signature invalid')


def _openssl():
    preferred = os.environ.get('STUDIO_MEMORY_OPENSSL')
    if preferred:
        return preferred
    homebrew = Path('/opt/homebrew/opt/openssl@3/bin/openssl')
    return str(homebrew) if homebrew.is_file() else (shutil.which('openssl') or 'openssl')


def _state(events):
    state = 'DRAFT'
    for event in events:
        action = event['action']
        allowed = {
            'DRAFT': {'DIRECTOR_REVIEWED', 'REJECTED'},
            'DIRECTOR_REVIEWED': {'PRODUCER_APPROVED', 'REJECTED'},
            'PRODUCER_APPROVED': {'REGISTERED', 'REJECTED'},
            'REGISTERED': {'REVOKED'},
            'REJECTED': set(), 'REVOKED': set(),
        }
        if action not in allowed[state]:
            raise ValueError('invalid workflow history')
        state = action
    return state


def propose(root_path, report_path, fields):
    root = _private_root(root_path)
    vault = _config(root)
    if not isinstance(fields, dict) or set(fields) != REQUIRED:
        raise ValueError('missing or unknown proposal fields')
    memory_id = fields['id']
    if not isinstance(memory_id, str) or not ID.fullmatch(memory_id):
        raise ValueError('invalid memory ID')
    if (vault / (memory_id + '.md')).exists() or (root / 'candidates' / (memory_id + '.json')).exists():
        raise ValueError('duplicate memory ID')
    if fields['proposed_by'] not in {'work01', 'work02'}:
        raise ValueError('invalid proposing Work')
    if not SOURCE_ID.fullmatch(fields['source_id']):
        raise ValueError('invalid source ID')
    if not isinstance(fields['related'], list) or not all(isinstance(x, str) and ID.fullmatch(x) for x in fields['related']):
        raise ValueError('invalid related IDs')
    for name in ('characters', 'assets', 'episodes'):
        if not isinstance(fields[name], list) or not all(isinstance(x, str) and 0 < len(x) <= 120 for x in fields[name]):
            raise ValueError('invalid targets')
    for name in ('title', 'kind', 'approval_scope', 'decision_excerpt', 'reason_excerpt'):
        if not isinstance(fields[name], str) or not 0 < len(fields[name]) <= 2000:
            raise ValueError('invalid proposal text')
    report = _read_file(report_path)
    report_text = report.decode('utf-8')
    for name in ('decision_excerpt', 'reason_excerpt'):
        if fields[name] != UNKNOWN and fields[name] not in report_text:
            raise ValueError('excerpt is absent from source report')
    candidate = {**fields, 'workflow_status': 'DRAFT', 'approval_status': 'DRAFT',
                 'created_at': _now(), 'source_path': str(Path(report_path).resolve(strict=True)),
                 'source_sha256': _sha(report),
                 'unknown_fields': [name for name in ('decision_excerpt', 'reason_excerpt', 'approval_scope')
                                    if fields[name] == UNKNOWN]}
    _new_file(root / 'candidates' / (memory_id + '.json'), _canonical(candidate))
    return candidate


def prepare_assertion(root_path, memory_id, action, actor, *, approval_status=None,
                      reason=None, accepted_conflicts=None):
    root = _private_root(root_path)
    candidate = _candidate(root, memory_id)
    if action not in REVIEW_ACTIONS or not isinstance(actor, str) or not actor.strip():
        raise ValueError('invalid approval action')
    return {'candidate_id': memory_id, 'candidate_sha256': _sha(_canonical(candidate)),
            'action': action, 'actor': actor, 'at': _now(), 'reason': reason or '',
            'approval_scope': candidate['approval_scope'],
            'approval_status': approval_status or candidate['approval_status'],
            'accepted_conflicts': accepted_conflicts or []}


def _verify_event(root, candidate, event):
    payload = event['assertion']
    role = 'director' if payload['action'] == 'DIRECTOR_REVIEWED' else 'producer'
    if payload['action'] == 'REJECTED':
        role = event['role']
    if role != event['role'] or payload['candidate_sha256'] != _sha(_canonical(candidate)):
        raise ValueError('approval target mismatch')
    proof_name = event['proof_name']
    if not isinstance(proof_name, str) or not re.fullmatch(r'[A-Z0-9-]+\.[a-f0-9]{16}\.sig', proof_name):
        raise ValueError('invalid approval proof reference')
    signature = _read_file(root / 'proofs' / proof_name, 1024)
    if _sha(signature) != event['signature_sha256']:
        raise ValueError('approval proof changed')
    _verify_signature(root, role, payload, signature)


def apply_assertion(root_path, assertion, signature):
    root = _private_root(root_path)
    memory_id = assertion.get('candidate_id')
    candidate = _candidate(root, memory_id)
    if set(assertion) != {'candidate_id', 'candidate_sha256', 'action', 'actor', 'at', 'reason',
                          'approval_scope', 'approval_status', 'accepted_conflicts'}:
        raise ValueError('invalid assertion')
    action = assertion['action']
    if action not in REVIEW_ACTIONS or assertion['candidate_sha256'] != _sha(_canonical(candidate)):
        raise ValueError('approval target mismatch')
    if action in {'REJECTED', 'REVOKED'} and not isinstance(assertion['reason'], str):
        raise ValueError('rejection reason required')
    if action in {'REJECTED', 'REVOKED'} and not assertion['reason'].strip():
        raise ValueError('rejection reason required')
    if assertion['approval_scope'] != candidate['approval_scope'] or assertion['approval_status'] not in STATUSES:
        raise ValueError('approval scope or status invalid')
    if action == 'PRODUCER_APPROVED' and (candidate['unknown_fields'] or assertion['approval_scope'] == UNKNOWN):
        raise ValueError('unresolved fields cannot be approved')
    if not isinstance(assertion['accepted_conflicts'], list) or not all(isinstance(x, str) and ID.fullmatch(x) for x in assertion['accepted_conflicts']):
        raise ValueError('invalid conflict acknowledgement')
    if not isinstance(assertion['actor'], str) or not assertion['actor'].strip():
        raise ValueError('actor required')
    if not isinstance(assertion['at'], str):
        raise ValueError('approval time required')
    try:
        signed_at = datetime.fromisoformat(assertion['at'])
    except ValueError:
        raise ValueError('invalid approval time') from None
    current_time = datetime.now(timezone.utc)
    if (signed_at.tzinfo is None or signed_at < current_time - timedelta(hours=24)
            or signed_at > current_time + timedelta(minutes=5)):
        raise ValueError('approval assertion expired')
    role = 'director' if action == 'DIRECTOR_REVIEWED' else 'producer'
    _verify_signature(root, role, assertion, signature)
    events = _events(root, memory_id)
    for event in events:
        if event['action'] != 'REGISTERED':
            _verify_event(root, candidate, event)
    previous = _state(events)
    if action == 'DIRECTOR_REVIEWED' and previous != 'DRAFT':
        raise ValueError('director review out of order')
    if action == 'PRODUCER_APPROVED' and previous != 'DIRECTOR_REVIEWED':
        raise ValueError('producer approval out of order')
    if action == 'REVOKED' and previous != 'REGISTERED':
        raise ValueError('revocation out of order')
    if action == 'REJECTED' and previous not in {'DRAFT', 'DIRECTOR_REVIEWED', 'PRODUCER_APPROVED'}:
        raise ValueError('rejection out of order')
    if action == 'REVOKED':
        vault = _config(root)
        current = vault / (memory_id + '.md')
        last_registration = events[-1]
        if not current.is_file() or current.is_symlink() or _sha(_read_file(current, 32768)) != last_registration['memory_sha256']:
            raise ValueError('registered memory changed or unavailable')
        archived = root / 'archive' / (memory_id + '.' + last_registration['memory_sha256'] + '.md')
        _new_file(archived, _read_file(current, 32768))
        current.unlink()
    proof_name = memory_id + '.' + secrets.token_hex(8) + '.sig'
    _new_file(root / 'proofs' / proof_name, signature)
    event = {'action': action, 'role': role, 'assertion': assertion,
             'proof_name': proof_name, 'signature_sha256': _sha(signature)}
    try:
        _append_event(root, memory_id, event)
    except Exception:
        if action == 'REVOKED':
            _new_file(current, _read_file(archived, 32768))
        raise
    return action


def _source_check(candidate):
    source = _read_file(candidate['source_path'])
    if _sha(source) != candidate['source_sha256']:
        raise ValueError('source changed since proposal')
    text = source.decode('utf-8')
    for name in ('decision_excerpt', 'reason_excerpt'):
        if candidate[name] not in text:
            raise ValueError('source excerpt missing')


def _conflicts(vault, candidate):
    found = []
    for path in vault.glob('*.md'):
        note = _parse(path)
        same_character = any(len(name) >= 2 and name in note['title'] for name in candidate['characters'])
        if (note['title'] == candidate['title'] or set(note['assets']) & set(candidate['assets'])
                or same_character):
            found.append(note['id'])
    return sorted(found)


def _markdown(candidate, approval_status):
    meta = {'id': candidate['id'], 'title': candidate['title'], 'kind': candidate['kind'],
            'approval_status': approval_status, 'approval_scope': candidate['approval_scope'],
            'source': candidate['source_id'], 'sources': [candidate['source_id']],
            'updated_at': _now()[:10], 'related': candidate['related'], 'assets': candidate['assets']}
    front = '\n'.join(f'{key}: {json.dumps(value, ensure_ascii=False)}' for key, value in meta.items())
    targets = []
    if candidate['characters']:
        targets.append('対象キャラクター：' + '、'.join(candidate['characters']))
    if candidate['episodes']:
        targets.append('対象話数：' + '、'.join(candidate['episodes']))
    if candidate['related']:
        targets.append('関連記憶：' + '、'.join('[[' + item + ']]' for item in candidate['related']))
    body = (f"# {candidate['title']}\n\n{candidate['decision_excerpt']}\n\n"
            f"判断理由：{candidate['reason_excerpt']}" + ('\n\n' + '\n'.join(targets) if targets else ''))
    return f'---\n{front}\n---\n\n{body}\n'.encode('utf-8')


def register(root_path, memory_id):
    root = _private_root(root_path)
    vault = _config(root)
    candidate = _candidate(root, memory_id)
    events = _events(root, memory_id)
    for event in events:
        if event['action'] != 'REGISTERED':
            _verify_event(root, candidate, event)
    if _state(events) != 'PRODUCER_APPROVED':
        raise ValueError('producer approval is required')
    approval = events[-1]['assertion']
    _source_check(candidate)
    for related_id in candidate['related']:
        if not (vault / (related_id + '.md')).is_file():
            raise ValueError('related memory is unavailable')
    conflicts = _conflicts(vault, candidate)
    if set(conflicts) != set(approval['accepted_conflicts']):
        raise ValueError('unresolved existing-memory conflict')
    target = vault / (memory_id + '.md')
    if target.exists():
        raise ValueError('existing memory cannot be overwritten')
    content = _markdown(candidate, approval['approval_status'])
    if len(content) > 32768:
        raise ValueError('memory exceeds Reader limit')
    # Validate exactly the same parser used by the Reader before publishing.
    with tempfile.TemporaryDirectory() as temporary:
        probe = Path(temporary) / target.name
        probe.write_bytes(content)
        _parse(probe)
    diff = {'before_sha256': None, 'after_sha256': _sha(content),
            'before': None, 'after': content.decode('utf-8')}
    diff_path = root / 'diffs' / (memory_id + '.json')
    _new_file(diff_path, _canonical(diff))
    staging = vault / ('.staging-' + memory_id + '-' + secrets.token_hex(8))
    try:
        _new_file(staging, content)
        _append_event(root, memory_id, {'action': 'REGISTERED', 'at': _now(),
                                         'actor': approval['actor'], 'memory_sha256': _sha(content),
                                         'diff_sha256': _sha(_canonical(diff))})
        os.link(staging, target, follow_symlinks=False)
        staging.unlink()
    except Exception:
        # A failed final rename leaves a hidden staging file for manual recovery;
        # the Reader never treats it as a registered Markdown note.
        if staging.exists() and _state(_events(root, memory_id)) == 'PRODUCER_APPROVED':
            staging.unlink()
        raise
    return {'id': memory_id, 'memory_sha256': _sha(content), 'conflicts': conflicts}


def status(root_path, memory_id):
    root = _private_root(root_path)
    candidate = _candidate(root, memory_id)
    events = _events(root, memory_id)
    for event in events:
        if event['action'] != 'REGISTERED':
            _verify_event(root, candidate, event)
    approved = next((event['assertion']['approval_status'] for event in reversed(events)
                     if event['action'] == 'PRODUCER_APPROVED'), candidate['approval_status'])
    return {'id': memory_id, 'workflow_status': _state(events),
            'approval_status': approved,
            'approval_scope': candidate['approval_scope'], 'unknown_fields': candidate['unknown_fields'],
            'source_id': candidate['source_id'], 'related': candidate['related']}
