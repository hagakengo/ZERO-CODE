"""Local Studio Memory credentials, revocation and metadata-only audit.

Administrative mutations are exposed only through the offline CLI. The Reader
only verifies signed, short-lived tokens and appends a minimal audit record.
"""
import base64
import binascii
import fcntl
import hashlib
import hmac
import json
import os
import secrets
import stat
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, Request

MAX_TTL = 900
OPERATIONS = {'search', 'detail'}
ACCESS = {'approved', 'all'}
WORK_IDS = {'work01', 'work02', 'web'}


def _b64(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _unb64(value):
    return base64.urlsafe_b64decode(value + '=' * (-len(value) % 4))


def _private_file(path, *, size_limit=65536):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or info.st_mode & 0o077 or info.st_size > size_limit):
            raise ValueError('unsafe private file')
        data = os.read(fd, size_limit + 1)
        if len(data) > size_limit:
            raise ValueError('private file too large')
        return data
    finally:
        os.close(fd)


def auth_root(configured=None):
    value = configured or os.environ.get('STUDIO_MEMORY_AUTH_DIR')
    if not value:
        raise ValueError('memory authentication is not configured')
    root = Path(value)
    info = root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('unsafe authentication directory')
    return root


def _state(root):
    data = json.loads(_private_file(root / 'state.json'))
    if data.get('version') != 1 or not isinstance(data.get('works'), dict) or not isinstance(data.get('revoked'), dict):
        raise ValueError('invalid authentication state')
    for work_id, work in data['works'].items():
        if work_id not in WORK_IDS or not isinstance(work, dict) or type(work.get('generation')) is not int or work['generation'] < 1:
            raise ValueError('invalid work state')
        if type(work.get('enabled')) is not bool or work.get('max_access') not in ACCESS:
            raise ValueError('invalid work policy')
        if not isinstance(work.get('operations'), list) or not set(work['operations']) <= OPERATIONS:
            raise ValueError('invalid work operations')
    if not all(isinstance(x, str) and len(x) == 32 and type(exp) is int
               for x, exp in data['revoked'].items()):
        raise ValueError('invalid revocation list')
    return data


def _key(root):
    key = _private_file(root / 'signing.key', size_limit=128)
    if len(key) != 32:
        raise ValueError('invalid signing key')
    return key


def _write_private(path, data, *, exclusive=False):
    flags = os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW
    flags |= os.O_EXCL if exclusive else os.O_TRUNC
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        if exclusive:
            path.unlink(missing_ok=True)
        raise


def initialize(directory):
    """Explicit offline setup; never called on API startup."""
    root = Path(directory)
    root.mkdir(mode=0o700)
    state = {'version': 1, 'works': {
        'work01': {'enabled': True, 'generation': 1, 'max_access': 'approved', 'operations': ['search', 'detail']},
        'work02': {'enabled': True, 'generation': 1, 'max_access': 'all', 'operations': ['search', 'detail']},
        'web': {'enabled': True, 'generation': 1, 'max_access': 'approved', 'operations': ['search', 'detail']},
    }, 'revoked': {}}
    _write_private(root / 'signing.key', secrets.token_bytes(32), exclusive=True)
    _write_private(root / 'state.json', json.dumps(state, separators=(',', ':')).encode(), exclusive=True)
    _write_private(root / 'audit.jsonl', b'', exclusive=True)
    return root


def _sign(payload, key):
    encoded = _b64(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode())
    signature = _b64(hmac.new(key, encoded.encode(), hashlib.sha256).digest())
    return encoded + '.' + signature


def issue(root, work_id, access, operations=('search', 'detail'), ttl=300, now=None):
    root = auth_root(root)
    state = _state(root)
    work = state['works'].get(work_id)
    operations = tuple(operations)
    if not work or not work['enabled'] or access not in ACCESS or not operations or not set(operations) <= OPERATIONS:
        raise ValueError('invalid credential request')
    if not set(operations) <= set(work['operations']) or (access == 'all' and work['max_access'] != 'all'):
        raise ValueError('request exceeds work permissions')
    if type(ttl) is not int or not 1 <= ttl <= MAX_TTL:
        raise ValueError('invalid token lifetime')
    issued = int(time.time() if now is None else now)
    payload = {'v': 1, 'aud': 'studio-memory', 'work': work_id, 'access': access,
               'ops': list(operations), 'generation': work['generation'], 'iat': issued,
               'exp': issued + ttl, 'jti': secrets.token_hex(16)}
    return _sign(payload, _key(root))


def _signed_payload(token, key):
    if not isinstance(token, str) or len(token) > 2048 or token.count('.') != 1:
        raise ValueError('invalid token')
    data, signature = token.split('.')
    expected = hmac.new(key, data.encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(expected, _unb64(signature)):
        raise ValueError('invalid signature')
    payload = json.loads(_unb64(data))
    if not isinstance(payload, dict) or set(payload) != {'v', 'aud', 'work', 'access', 'ops', 'generation', 'iat', 'exp', 'jti'}:
        raise ValueError('invalid claims')
    return payload


def verify(request: Request, operation, authorization, *, now=None):
    try:
        root = auth_root()
        key = _key(root)
        state = _state(root)
    except (OSError, ValueError, json.JSONDecodeError):
        raise HTTPException(503, 'Studio Memoryの認証を確認できません') from None
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401, '認証が必要です')
    try:
        claims = _signed_payload(authorization[7:], key)
    except (ValueError, UnicodeError, binascii.Error, json.JSONDecodeError):
        raise HTTPException(401, '認証が必要です') from None
    work_id = claims.get('work')
    if work_id in WORK_IDS:
        request.state.memory_work_id = work_id  # only after signature verification
    work = state['works'].get(work_id)
    current = int(time.time() if now is None else now)
    if (claims.get('v') != 1 or claims.get('aud') != 'studio-memory' or not work or not work['enabled']
            or type(claims.get('iat')) is not int or type(claims.get('exp')) is not int
            or claims['iat'] > current + 30 or claims['exp'] <= current
            or claims['exp'] - claims['iat'] > MAX_TTL or claims['exp'] <= claims['iat']
            or type(claims.get('generation')) is not int or claims['generation'] != work['generation']
            or claims.get('jti') in state['revoked'] or not isinstance(claims.get('jti'), str)
            or len(claims['jti']) != 32):
        raise HTTPException(401, '認証が必要です')
    ops = claims.get('ops')
    access = claims.get('access')
    if (not isinstance(ops, list) or not ops or not all(isinstance(x, str) for x in ops)
            or not set(ops) <= set(work['operations']) or access not in ACCESS
            or (access == 'all' and work['max_access'] != 'all')):
        raise HTTPException(401, '認証が必要です')
    if operation not in ops:
        raise HTTPException(403, '操作は許可されていません')
    return access


def _replace_state(root, state):
    temporary = root / ('.state-' + secrets.token_hex(8))
    _write_private(temporary, json.dumps(state, sort_keys=True, separators=(',', ':')).encode(), exclusive=True)
    os.replace(temporary, root / 'state.json')


def _locked_state(root, transform):
    root = auth_root(root)
    lock = root / 'state.lock'
    fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('unsafe lock')
        fcntl.flock(fd, fcntl.LOCK_EX)
        state = _state(root)
        state['revoked'] = {jti: exp for jti, exp in state['revoked'].items() if exp > int(time.time())}
        transform(state)
        _replace_state(root, state)
    finally:
        os.close(fd)


def revoke_work(root, work_id):
    def change(state):
        if work_id not in state['works']:
            raise ValueError('unknown work')
        state['works'][work_id]['generation'] += 1
    _locked_state(root, change)


def revoke_token(root, token):
    root = auth_root(root)
    claims = _signed_payload(token, _key(root))
    jti = claims.get('jti')
    if (claims.get('aud') != 'studio-memory' or not isinstance(jti, str) or len(jti) != 32
            or type(claims.get('exp')) is not int):
        raise ValueError('invalid token id')
    def change(state):
        state['revoked'][jti] = claims['exp']
    _locked_state(root, change)


def audit(work_id, operation, result):
    """Never records token, query, memory ID, body, path or IP address."""
    root = auth_root()
    event = {'at': datetime.now(timezone.utc).isoformat(),
             'work_id': work_id if work_id in WORK_IDS else 'unknown',
             'operation': operation if operation in OPERATIONS else 'unknown',
             'result': str(result) if str(result) in {'200', '401', '403', '404', '405', '422', '500', '503'} else '500'}
    path = root / 'audit.jsonl'
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('unsafe audit file')
        fcntl.flock(fd, fcntl.LOCK_EX)
        with os.fdopen(os.dup(fd), 'ab') as stream:
            stream.write((json.dumps(event, separators=(',', ':')) + '\n').encode())
            stream.flush()
        os.fsync(fd)
    finally:
        os.close(fd)
