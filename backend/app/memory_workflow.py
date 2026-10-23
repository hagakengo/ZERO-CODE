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
    """Publish a complete private file atomically without replacing an existing one."""
    path = Path(path)
    temporary = path.with_name('.pending-' + secrets.token_hex(16))
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path, follow_symlinks=False)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        raise
    finally:
        temporary.unlink(missing_ok=True)


def _replace_private_file(path, data):
    path = Path(path)
    temporary = path.with_name('.' + path.name + '.' + secrets.token_hex(8))
    _new_file(temporary, data)
    os.replace(temporary, path)


def _key_id(role, key):
    return role + '-' + _sha(key)[:24]


def _registry(root):
    data = json.loads(_read_file(root / 'keys' / 'registry.json', 32768))
    if data.get('version') != 1 or not isinstance(data.get('keys'), dict):
        raise ValueError('invalid key registry')
    for key_id, entry in data['keys'].items():
        if not re.fullmatch(r'(director|producer)-[a-f0-9]{24}', key_id):
            raise ValueError('invalid key ID')
        if (entry.get('role') not in ROLES or entry.get('state') not in {'active', 'revoked'}
                or entry.get('role') != key_id.split('-')[0]):
            raise ValueError('invalid key entry')
        key = _read_file(root / 'keys' / (key_id + '.pem'), 8192)
        if _key_id(entry['role'], key) != key_id or _sha(key) != entry.get('sha256'):
            raise ValueError('approval public key changed')
    for role in ROLES:
        if sum(item['role'] == role and item['state'] == 'active' for item in data['keys'].values()) > 1:
            raise ValueError('multiple active approval keys')
    return data


def _active_key(root, role):
    matches = [key_id for key_id, item in _registry(root)['keys'].items()
               if item['role'] == role and item['state'] == 'active']
    if len(matches) != 1:
        raise ValueError('active approval key unavailable')
    return matches[0]


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
    entries = {}
    for role, key in keys.items():
        key_id = _key_id(role, key)
        _new_file(root / 'keys' / (key_id + '.pem'), key)
        entries[key_id] = {'role': role, 'state': 'active', 'sha256': _sha(key)}
    _new_file(root / 'keys' / 'registry.json', _canonical({'version': 1, 'keys': entries}))
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
    _append_jsonl(path, event)


def _append_jsonl(path, event):
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


def _verify_signature(root, role, payload, signature, *, require_active=True):
    if role not in ROLES or len(signature) > 1024:
        raise ValueError('invalid approval signature')
    key_id = payload.get('key_id')
    if not isinstance(key_id, str):
        raise ValueError('invalid approval key ID')
    entry = _registry(root)['keys'].get(key_id)
    if not entry or entry['role'] != role or (require_active and entry['state'] != 'active'):
        raise ValueError('approval key unavailable or revoked')
    with tempfile.TemporaryDirectory() as temporary:
        message = Path(temporary) / 'message'
        signed = Path(temporary) / 'signature'
        message.write_bytes(_canonical(payload))
        signed.write_bytes(signature)
        result = subprocess.run([_openssl(), 'pkeyutl', '-verify', '-pubin', '-inkey',
                                 str(root / 'keys' / (key_id + '.pem')), '-rawin',
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
    candidate = build_candidate(report_path, fields)
    memory_id = candidate['id']
    if (vault / (memory_id + '.md')).exists() or (root / 'candidates' / (memory_id + '.json')).exists():
        raise ValueError('duplicate memory ID')
    _new_file(root / 'candidates' / (memory_id + '.json'), _canonical(candidate))
    return candidate


def build_candidate(report_path, fields):
    """Shared source-bound candidate construction for formal and DRAFT-only intake."""
    if not isinstance(fields, dict) or set(fields) != REQUIRED:
        raise ValueError('missing or unknown proposal fields')
    memory_id = fields['id']
    if not isinstance(memory_id, str) or not ID.fullmatch(memory_id):
        raise ValueError('invalid memory ID')
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
    return candidate


def prepare_assertion(root_path, memory_id, action, actor, *, approval_status=None,
                      reason=None, accepted_conflicts=None):
    root = _private_root(root_path)
    candidate = _candidate(root, memory_id)
    if action not in REVIEW_ACTIONS or not isinstance(actor, str) or not actor.strip():
        raise ValueError('invalid approval action')
    role = 'director' if action == 'DIRECTOR_REVIEWED' else 'producer'
    return {'candidate_id': memory_id, 'candidate_sha256': _sha(_canonical(candidate)),
            'source_sha256': candidate['source_sha256'],
            'body_sha256': _body_digest(candidate), 'key_id': _active_key(root, role),
            'nonce': secrets.token_hex(16),
            'action': action, 'actor': actor, 'at': _now(), 'reason': reason or '',
            'approval_scope': candidate['approval_scope'],
            'approval_status': approval_status or candidate['approval_status'],
            'accepted_conflicts': accepted_conflicts or []}


def _body_digest(candidate):
    """Digest the substantive text independently of registration timestamp/metadata."""
    return _sha(_canonical({name: candidate[name] for name in
                           ('title', 'decision_excerpt', 'reason_excerpt', 'characters',
                            'episodes', 'assets', 'related', 'approval_scope')}))


def _check_assertion_target(candidate, payload):
    if (payload.get('candidate_id') != candidate['id']
            or payload.get('candidate_sha256') != _sha(_canonical(candidate))
            or payload.get('source_sha256') != candidate['source_sha256']
            or payload.get('body_sha256') != _body_digest(candidate)
            or payload.get('approval_scope') != candidate['approval_scope']):
        raise ValueError('approval target mismatch')


def _check_time(value):
    if not isinstance(value, str):
        raise ValueError('approval time required')
    try:
        signed_at = datetime.fromisoformat(value)
    except ValueError:
        raise ValueError('invalid approval time') from None
    current_time = datetime.now(timezone.utc)
    if (signed_at.tzinfo is None or signed_at < current_time - timedelta(hours=24)
            or signed_at > current_time + timedelta(minutes=5)):
        raise ValueError('approval assertion expired')


def _nonce_used(root, nonce):
    if not re.fullmatch(r'[a-f0-9]{32}', nonce):
        raise ValueError('invalid assertion nonce')
    for path in (root / 'events').glob('*.jsonl'):
        for line in _read_file(path).splitlines():
            event = json.loads(line)
            if event.get('assertion', {}).get('nonce') == nonce:
                return True
    return False


def prepare_key_change(root_path, role, action, actor, *, new_public=None, reason=''):
    """Create a producer-signed management request; never handles private keys."""
    root = _private_root(root_path)
    if role not in ROLES or action not in {'ROTATE', 'REVOKE'} or not actor.strip() or not reason.strip():
        raise ValueError('invalid key management request')
    if action == 'REVOKE' and (role == 'producer' or new_public):
        raise ValueError('producer key requires replacement; revoke accepts no replacement')
    if action == 'ROTATE' and not new_public:
        raise ValueError('replacement public key required')
    key = _read_file(new_public, 8192) if new_public else None
    if key is not None and b'PUBLIC KEY' not in key:
        raise ValueError('invalid replacement public key')
    registry = _registry(root)
    old_id = _active_key(root, role)
    new_id = _key_id(role, key) if key else None
    if new_id in registry['keys']:
        raise ValueError('replacement key already registered')
    return {'action': action, 'role': role, 'old_key_id': old_id,
            'new_key_id': new_id, 'new_key_sha256': _sha(key) if key else None,
            'registry_sha256': _sha(_canonical(registry)),
            'key_id': _active_key(root, 'producer'), 'nonce': secrets.token_hex(16),
            'actor': actor, 'at': _now(), 'reason': reason}


def apply_key_change(root_path, assertion, signature, *, new_public=None):
    root = _private_root(root_path)
    if set(assertion) != {'action', 'role', 'old_key_id', 'new_key_id', 'new_key_sha256',
                          'registry_sha256', 'key_id', 'nonce', 'actor', 'at', 'reason'}:
        raise ValueError('invalid key management assertion')
    role, action = assertion['role'], assertion['action']
    if role not in ROLES or action not in {'ROTATE', 'REVOKE'} or not assertion['reason'].strip():
        raise ValueError('invalid key management action')
    if role == 'producer' and action == 'REVOKE':
        raise ValueError('producer key requires replacement')
    _check_time(assertion['at'])
    if not re.fullmatch(r'[a-f0-9]{32}', assertion['nonce']):
        raise ValueError('invalid management nonce')
    registry = _registry(root)
    if (assertion['registry_sha256'] != _sha(_canonical(registry))
            or assertion['old_key_id'] != _active_key(root, role)
            or assertion['key_id'] != _active_key(root, 'producer')):
        raise ValueError('key registry changed or signer inactive')
    key = _read_file(new_public, 8192) if new_public else None
    if action == 'ROTATE':
        if (not key or b'PUBLIC KEY' not in key or _key_id(role, key) != assertion['new_key_id']
                or _sha(key) != assertion['new_key_sha256']
                or assertion['new_key_id'] in registry['keys']):
            raise ValueError('replacement public key mismatch')
    elif key or assertion['new_key_id'] is not None or assertion['new_key_sha256'] is not None:
        raise ValueError('revocation must not add a key')
    events_path = root / 'keys' / 'events.jsonl'
    if events_path.exists():
        for line in _read_file(events_path).splitlines():
            if json.loads(line)['assertion']['nonce'] == assertion['nonce']:
                raise ValueError('management assertion already used')
    _verify_signature(root, 'producer', assertion, signature)
    if key:
        _new_file(root / 'keys' / (assertion['new_key_id'] + '.pem'), key)
        registry['keys'][assertion['new_key_id']] = {'role': role, 'state': 'active', 'sha256': _sha(key)}
    registry['keys'][assertion['old_key_id']]['state'] = 'revoked'
    registry['keys'][assertion['old_key_id']]['revoked_at'] = _now()
    registry['keys'][assertion['old_key_id']]['reason'] = assertion['reason']
    proof_name = 'key-change.' + assertion['nonce'] + '.sig'
    _new_file(root / 'proofs' / proof_name, signature)
    # An AUTHORIZED event before replacement fails closed if a crash occurs.
    _append_jsonl(root / 'keys' / 'events.jsonl', {'assertion': assertion,
                  'proof_name': proof_name, 'signature_sha256': _sha(signature), 'result': 'AUTHORIZED'})
    _replace_private_file(root / 'keys' / 'registry.json', _canonical(registry))
    return {'old_key_id': assertion['old_key_id'], 'new_key_id': assertion['new_key_id'],
            'state': 'rotated' if key else 'revoked'}


def key_audit(root_path):
    """Verify archived management proofs without returning private key material."""
    root = _private_root(root_path)
    _registry(root)
    path = root / 'keys' / 'events.jsonl'
    if not path.exists():
        return []
    output = []
    for line in _read_file(path).splitlines():
        event = json.loads(line)
        assertion = event['assertion']
        proof_name = event['proof_name']
        if not re.fullmatch(r'key-change\.[a-f0-9]{32}\.sig', proof_name):
            raise ValueError('invalid management proof reference')
        signature = _read_file(root / 'proofs' / proof_name, 1024)
        if _sha(signature) != event['signature_sha256']:
            raise ValueError('management proof changed')
        _verify_signature(root, 'producer', assertion, signature, require_active=False)
        output.append({'action': assertion['action'], 'role': assertion['role'],
                       'old_key_id': assertion['old_key_id'], 'new_key_id': assertion['new_key_id'],
                       'at': assertion['at'], 'result': event['result']})
    return output


def review_packet(root_path, memory_id, action, actor, **kwargs):
    root = _private_root(root_path)
    candidate = _candidate(root, memory_id)
    assertion = prepare_assertion(root, memory_id, action, actor, **kwargs)
    return review_details(root, candidate, assertion)


def review_details(root, candidate, assertion):
    """Display the exact canonical assertion that the signer must sign."""
    vault = _config(root)
    return {'unsigned': True, 'workflow_status': _state(_events(root, candidate['id'])),
            'id': candidate['id'], 'title': candidate['title'],
            'decision': candidate['decision_excerpt'], 'reason': candidate['reason_excerpt'],
            'source_id': candidate['source_id'], 'source_path': candidate['source_path'],
            'source_sha256': candidate['source_sha256'],
            'body_sha256': assertion['body_sha256'],
            'approval_scope': assertion['approval_scope'],
            'approval_status': assertion['approval_status'],
            'existing_memory_conflicts': _conflicts(vault, candidate),
            'assertion': assertion,
            'canonical_assertion_sha256': _sha(_canonical(assertion)),
            'notice': 'AI監督の内容判断と人間の技術的署名は別操作。署名・登録は未実施。'}


def _verify_event(root, candidate, event):
    payload = event['assertion']
    if event['action'] != payload.get('action'):
        raise ValueError('approval event changed')
    role = 'director' if payload['action'] == 'DIRECTOR_REVIEWED' else 'producer'
    if payload['action'] == 'REJECTED':
        role = event['role']
    if role != event['role']:
        raise ValueError('approval target mismatch')
    _check_assertion_target(candidate, payload)
    proof_name = event['proof_name']
    if not isinstance(proof_name, str) or not re.fullmatch(r'[A-Z0-9-]+\.[a-f0-9]{16}\.sig', proof_name):
        raise ValueError('invalid approval proof reference')
    signature = _read_file(root / 'proofs' / proof_name, 1024)
    if _sha(signature) != event['signature_sha256']:
        raise ValueError('approval proof changed')
    _verify_signature(root, role, payload, signature, require_active=False)


def apply_assertion(root_path, assertion, signature):
    root = _private_root(root_path)
    memory_id = assertion.get('candidate_id')
    candidate = _candidate(root, memory_id)
    if set(assertion) != {'candidate_id', 'candidate_sha256', 'source_sha256', 'body_sha256',
                          'key_id', 'nonce', 'action', 'actor', 'at', 'reason',
                          'approval_scope', 'approval_status', 'accepted_conflicts'}:
        raise ValueError('invalid assertion')
    action = assertion['action']
    if action not in REVIEW_ACTIONS:
        raise ValueError('invalid action')
    _check_assertion_target(candidate, assertion)
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
    _check_time(assertion['at'])
    if _nonce_used(root, assertion['nonce']):
        raise ValueError('approval assertion already used')
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


def _markdown(candidate, approval_status, updated_at=None):
    meta = {'id': candidate['id'], 'title': candidate['title'], 'kind': candidate['kind'],
            'approval_status': approval_status, 'approval_scope': candidate['approval_scope'],
            'source': candidate['source_id'], 'sources': [candidate['source_id']],
            'updated_at': updated_at or _now()[:10], 'related': candidate['related'], 'assets': candidate['assets']}
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
    lock = root / 'registration.lock'
    fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('unsafe registration lock')
        fcntl.flock(fd, fcntl.LOCK_EX)
        return _register_locked(root, memory_id)
    finally:
        os.close(fd)


def _register_locked(root, memory_id):
    vault = _config(root)
    candidate = _candidate(root, memory_id)
    events = _events(root, memory_id)
    for event in events:
        if event['action'] != 'REGISTERED':
            _verify_event(root, candidate, event)
    if _state(events) != 'PRODUCER_APPROVED':
        raise ValueError('producer approval is required')
    approval = events[-1]['assertion']
    if _registry(root)['keys'][approval['key_id']]['state'] != 'active':
        raise ValueError('producer approval key revoked before registration')
    _check_assertion_target(candidate, approval)
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
    content = _markdown(candidate, approval['approval_status'], approval['at'][:10])
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
    if diff_path.exists():
        if _read_file(diff_path, 65536) != _canonical(diff):
            raise ValueError('existing registration diff changed')
    else:
        _new_file(diff_path, _canonical(diff))
    for stale in vault.glob('.staging-' + memory_id + '-*'):
        if _read_file(stale, 32768) != content:
            raise ValueError('stale registration staging differs')
        os.replace(stale, root / 'archive' / ('unfinished-' + memory_id + '-' + secrets.token_hex(8)))
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


def recover_registration(root_path, memory_id):
    """Repair only the post-REGISTERED/pre-publish crash window of signed synthetic workflows."""
    root = _private_root(root_path)
    lock = root / 'registration.lock'
    fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        vault = _config(root)
        candidate = _candidate(root, memory_id)
        events = _events(root, memory_id)
        for event in events:
            if event['action'] != 'REGISTERED':
                _verify_event(root, candidate, event)
        if _state(events) != 'REGISTERED':
            raise ValueError('no registered event to recover')
        event = events[-1]
        diff = json.loads(_read_file(root / 'diffs' / (memory_id + '.json'), 65536))
        content = diff['after'].encode('utf-8')
        if (_sha(content) != event['memory_sha256'] or _sha(_canonical(diff)) != event['diff_sha256']):
            raise ValueError('registration evidence mismatch')
        target = vault / (memory_id + '.md')
        if target.exists():
            if _read_file(target, 32768) != content:
                raise ValueError('registered memory changed')
            return {'id': memory_id, 'state': 'ALREADY_PRESENT'}
        staging = list(vault.glob('.staging-' + memory_id + '-*'))
        if len(staging) != 1 or _read_file(staging[0], 32768) != content:
            raise ValueError('registration staging unavailable')
        with tempfile.TemporaryDirectory() as temporary:
            probe = Path(temporary) / target.name
            probe.write_bytes(content)
            _parse(probe)
        os.link(staging[0], target, follow_symlinks=False)
        staging[0].unlink()
        return {'id': memory_id, 'state': 'RECOVERED_REGISTERED'}
    finally:
        os.close(fd)


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
