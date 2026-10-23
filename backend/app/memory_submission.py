"""Separate, loopback-only DRAFT submission service. Never mounted on Reader."""
import hashlib
import hmac
import json
import os
import re
import secrets
import time
import binascii
import fcntl
import stat
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request

from app import memory_drafts, memory_security, memory_workflow as workflow

MAX_BODY = 300_000
MAX_SOURCE = 262_144
MAX_TRANSACTION = 400_000
RECEIPT_ID = re.compile(r'^[a-f0-9]{32}$')
AUDIENCE = 'studio-memory-draft-submit'


def _private_root(path):
    return workflow._private_root(path)


def initialize(root_path, inbox_path):
    root = Path(root_path)
    if root.exists():
        raise ValueError('submission root already exists')
    memory_drafts._root(inbox_path)
    root.mkdir(mode=0o700)
    for name in ('sources', 'receipts', 'transactions'):
        (root / name).mkdir(mode=0o700)
    workflow._new_file(root / 'key', secrets.token_bytes(32))
    workflow._new_file(root / 'state.json', workflow._canonical({'version': 1, 'work02_generation': 1}))
    workflow._new_file(root / 'config.json', workflow._canonical({'version': 1, 'inbox': str(Path(inbox_path).resolve())}))
    workflow._new_file(root / 'audit.jsonl', b'')
    return root


def _state(root):
    state = json.loads(memory_security._private_file(root / 'state.json'))
    if set(state) != {'version', 'work02_generation'} or state['version'] != 1 or type(state['work02_generation']) is not int or state['work02_generation'] < 1:
        raise ValueError('invalid submission state')
    return state


def _key(root):
    key = memory_security._private_file(root / 'key', size_limit=128)
    if len(key) != 32:
        raise ValueError('invalid submission key')
    return key


def _inbox(root):
    config = json.loads(memory_security._private_file(root / 'config.json'))
    if set(config) != {'version', 'inbox'} or config['version'] != 1:
        raise ValueError('invalid submission configuration')
    return memory_drafts._root(config['inbox'])


def issue(root_path, *, ttl=300, now=None):
    root = _private_root(root_path)
    if type(ttl) is not int or not 1 <= ttl <= 900:
        raise ValueError('invalid lifetime')
    current = int(time.time() if now is None else now)
    return memory_security._sign({'v': 1, 'aud': AUDIENCE, 'work': 'work02',
        'op': 'submit', 'generation': _state(root)['work02_generation'],
        'iat': current, 'exp': current + ttl, 'jti': secrets.token_hex(16)}, _key(root))


def revoke_work(root_path):
    root = _private_root(root_path)
    state = _state(root)
    state['work02_generation'] += 1
    workflow._replace_private_file(root / 'state.json', workflow._canonical(state))


def _verify(root, authorization, *, now=None):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401, 'submission credential required')
    try:
        token = authorization[7:]
        if len(token) > 2048 or token.count('.') != 1:
            raise ValueError('invalid token')
        encoded, signature = token.split('.')
        expected = hmac.new(_key(root), encoded.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, memory_security._unb64(signature)):
            raise ValueError('invalid signature')
        claims = json.loads(memory_security._unb64(encoded))
        current = int(time.time() if now is None else now)
        if (set(claims) != {'v', 'aud', 'work', 'op', 'generation', 'iat', 'exp', 'jti'}
                or claims['v'] != 1 or claims['aud'] != AUDIENCE or claims['work'] != 'work02'
                or claims['op'] != 'submit' or type(claims['generation']) is not int
                or claims['generation'] != _state(root)['work02_generation']
                or type(claims['iat']) is not int or type(claims['exp']) is not int
                or claims['iat'] > current + 30 or claims['exp'] <= current
                or not 0 < claims['exp'] - claims['iat'] <= 900
                or not isinstance(claims['jti'], str) or not RECEIPT_ID.fullmatch(claims['jti'])):
            raise ValueError('invalid claims')
        return 'work02'
    except (ValueError, KeyError, TypeError, UnicodeError, binascii.Error, json.JSONDecodeError):
        raise HTTPException(401, 'submission credential required') from None
    except OSError:
        raise HTTPException(503, 'submission authentication unavailable') from None


def _audit(root, work, result, receipt_id=None):
    workflow._append_jsonl(root / 'audit.jsonl', {'at': workflow._now(), 'work': work,
        'operation': 'submit', 'result': result, 'receipt_id': receipt_id})


def _substance(candidate):
    return {key: candidate[key] for key in workflow.REQUIRED if key != 'proposed_by'}


def accept(root_path, payload, *, work='work02'):
    root = _private_root(root_path)
    lock = root / 'accept.lock'
    fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('unsafe submission lock')
        fcntl.flock(fd, fcntl.LOCK_EX)
        return _accept_locked(root, payload, work)
    finally:
        os.close(fd)


def _accept_locked(root, payload, work):
    inbox = _inbox(root)
    if not isinstance(payload, dict) or set(payload) != {'receipt_id', 'source_text', 'source_sha256', 'fields', 'project', 'unknowns', 'workflow_status', 'approval_status'}:
        raise ValueError('invalid submission envelope')
    receipt_id = payload['receipt_id']
    if not isinstance(receipt_id, str) or not RECEIPT_ID.fullmatch(receipt_id):
        raise ValueError('invalid receipt ID')
    if payload['workflow_status'] != 'DRAFT' or payload['approval_status'] != 'DRAFT':
        raise ValueError('DRAFT only')
    if not isinstance(payload['source_text'], str):
        raise ValueError('invalid source')
    source = payload['source_text'].encode('utf-8')
    if not source or len(source) > MAX_SOURCE or workflow._sha(source) != payload['source_sha256']:
        raise ValueError('source hash or size mismatch')
    fields = payload['fields']
    if not isinstance(fields, dict) or fields.get('proposed_by') != work:
        raise ValueError('proposer mismatch')
    # Validate every source-bound field before writing any candidate or receipt.
    source_path = root / 'sources' / (receipt_id + '.md')
    receipt_path = root / 'receipts' / (receipt_id + '.json')
    transaction_path = root / 'transactions' / (receipt_id + '.json')
    payload_hash = workflow._sha(workflow._canonical(payload))
    if receipt_path.exists():
        receipt = json.loads(memory_security._private_file(receipt_path))
        if receipt['payload_sha256'] != payload_hash or receipt['work'] != work:
            raise ValueError('receipt ID reused with different content')
        _verified_receipt(root, receipt_id)
        _audit(root, work, 'IDEMPOTENT_RETRY', receipt_id)
        return receipt
    if transaction_path.exists():
        transaction = json.loads(workflow._read_file(transaction_path, MAX_TRANSACTION))
        if transaction.get('payload_sha256') != payload_hash or transaction.get('work') != work:
            raise ValueError('unfinished receipt ID reused with different content')
    else:
        workflow._new_file(transaction_path, workflow._canonical({'work': work,
            'payload_sha256': payload_hash, 'payload': payload, 'state': 'SUBMITTED'}))
    _audit(root, work, 'SUBMITTED', receipt_id)
    if source_path.exists():
        # Interrupted attempts are never treated as completed receipts.
        if workflow._read_file(source_path) != source:
            raise ValueError('source ID reused with different content')
    else:
        workflow._new_file(source_path, source)
    created_candidate = False
    try:
        incoming = workflow.build_candidate(source_path, fields)
        if incoming['source_sha256'] != payload['source_sha256']:
            raise ValueError('source changed during intake')
        candidate_path = inbox / 'candidates' / (incoming['id'] + '.json')
        if candidate_path.exists():
            existing = workflow._candidate(inbox, incoming['id'])
            if _substance(existing) != _substance(incoming) or existing['source_sha256'] != incoming['source_sha256']:
                raise ValueError('candidate ID conflict')
            annotations = memory_drafts._annotations(inbox, existing)
            if annotations['project'] != payload['project'] or annotations['unknowns'] != payload['unknowns']:
                raise ValueError('candidate annotations conflict')
            candidate = existing
            disposition = 'MATCHED_EXISTING_DRAFT'
        else:
            candidate = memory_drafts.add(inbox, source_path, fields,
                project=payload['project'], unknowns=payload['unknowns'])
            created_candidate = True
            disposition = 'NEW_DRAFT'
        detail = memory_drafts.detail(inbox, candidate['id'])
        if detail['source_state'] != 'MATCH':
            raise ValueError('source verification failed')
        _audit(root, work, 'VALIDATED', receipt_id)
        receipt = {'receipt_id': receipt_id, 'payload_sha256': payload_hash,
            'candidate_id': candidate['id'], 'work': work,
            'received_at': workflow._now(), 'submission_status': 'READY_FOR_REVIEW',
            'workflow_status': 'DRAFT', 'approval_status': 'DRAFT',
            'source_sha256': payload['source_sha256'], 'source_state': 'MATCH',
            'disposition': disposition, 'review_status': detail['review_status']}
        workflow._new_file(receipt_path, workflow._canonical(receipt))
        _audit(root, work, 'READY_FOR_REVIEW', receipt_id)
        transaction_path.unlink(missing_ok=True)
        return receipt
    except Exception:
        # Roll back a newly created DRAFT when receipt persistence fails.
        if created_candidate and not receipt_path.exists():
            (inbox / 'annotations' / (incoming['id'] + '.json')).unlink(missing_ok=True)
            (inbox / 'candidates' / (incoming['id'] + '.json')).unlink(missing_ok=True)
        if not receipt_path.exists():
            memory_id = fields.get('id')
            candidate_path = (inbox / 'candidates' / (memory_id + '.json')) if isinstance(memory_id, str) and workflow.ID.fullmatch(memory_id) else None
            if candidate_path is None or not candidate_path.exists():
                source_path.unlink(missing_ok=True)
        _audit(root, work, 'NEEDS_CORRECTION', receipt_id)
        raise


def receipt_detail(root_path, receipt_id):
    root = _private_root(root_path)
    if not RECEIPT_ID.fullmatch(receipt_id):
        raise ValueError('invalid receipt ID')
    receipt = json.loads(memory_security._private_file(root / 'receipts' / (receipt_id + '.json')))
    detail = memory_drafts.detail(_inbox(root), receipt['candidate_id'])
    if (receipt.get('receipt_id') != receipt_id or receipt.get('source_sha256') != detail['candidate']['source_sha256']
            or receipt.get('candidate_id') != detail['candidate']['id']):
        raise ValueError('receipt and candidate disagree')
    return {**receipt, 'submission_status': 'REVIEWED' if detail['review_status'] != 'REVIEW_PENDING' else receipt['submission_status'],
            'review_status': detail['review_status'], 'candidate_source_state': detail['source_state']}


def _verified_receipt(root_path, receipt_id):
    receipt = receipt_detail(root_path, receipt_id)
    if (receipt['approval_status'] != 'DRAFT' or receipt['workflow_status'] != 'DRAFT'
            or receipt['source_state'] != 'MATCH' or receipt['candidate_source_state'] != 'MATCH'):
        raise ValueError('receipt or candidate integrity mismatch')
    return receipt


def list_receipts(root_path):
    root = _private_root(root_path)
    return [receipt_detail(root, path.stem) for path in sorted((root / 'receipts').glob('*.json'))]


def integrity_check(root_path):
    root = _private_root(root_path)
    checked = 0
    for path in sorted((root / 'receipts').glob('*.json')):
        if not RECEIPT_ID.fullmatch(path.stem):
            raise ValueError('invalid receipt name')
        _verified_receipt(root, path.stem)
        checked += 1
    return {'receipts_verified': checked, 'state': 'MATCH'}


def recover(root_path):
    """Resume private unfinished submissions; a conflict stops startup closed."""
    root = _private_root(root_path)
    lock = root / 'accept.lock'
    fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        output = []
        for path in sorted((root / 'transactions').glob('*.json')):
            if not RECEIPT_ID.fullmatch(path.stem):
                raise ValueError('invalid recovery transaction')
            transaction = json.loads(workflow._read_file(path, MAX_TRANSACTION))
            if transaction.get('state') != 'SUBMITTED' or transaction.get('work') != 'work02':
                raise ValueError('invalid recovery state')
            payload = transaction.get('payload')
            if not isinstance(payload, dict) or payload.get('receipt_id') != path.stem:
                raise ValueError('invalid recovery payload')
            if workflow._sha(workflow._canonical(payload)) != transaction.get('payload_sha256'):
                raise ValueError('recovery transaction hash mismatch')
            if (root / 'receipts' / (path.stem + '.json')).exists():
                receipt = _verified_receipt(root, path.stem)
                if receipt['payload_sha256'] != transaction['payload_sha256']:
                    raise ValueError('receipt and transaction disagree')
                path.unlink()
                output.append({'receipt_id': path.stem, 'state': 'VERIFIED_EXISTING'})
            else:
                receipt = _accept_locked(root, payload, 'work02')
                output.append({'receipt_id': path.stem, 'state': receipt['submission_status']})
        return output
    finally:
        os.close(fd)


def review_packet(root_path, receipt_id):
    root = _private_root(root_path)
    receipt = receipt_detail(root, receipt_id)
    packet = memory_drafts.review_packet(_inbox(root), receipt['candidate_id'])
    decision = packet['decision_excerpt']
    packet['submission'] = {key: receipt[key] for key in
        ('receipt_id', 'work', 'received_at', 'submission_status', 'source_state', 'disposition')}
    packet['qc_distinction'] = {
        'technical_qc': 'PASS' if '技術PASS' in decision else 'UNVERIFIED',
        'direction_and_drawing_qc': 'REWORK' if '演出・作画REWORK' in decision else 'UNVERIFIED',
        'basis': 'decision_excerpt exact text; no new QC judgment',
        'master_approval': 'NOT_APPROVED', 'publication_approval': 'NOT_APPROVED'}
    return packet


def create_app(root_path):
    root = _private_root(root_path)
    recover(root)
    integrity_check(root)
    app = FastAPI(title='Studio Memory private DRAFT submission')

    @app.post('/submit')
    async def submit(request: Request, authorization: str | None = Header(default=None)):
        try:
            work = _verify(root, authorization)
        except HTTPException:
            _audit(root, 'unverified', 'DENIED')
            raise
        try:
            declared_length = int(request.headers['content-length']) if request.headers.get('content-length') else 0
        except ValueError:
            raise HTTPException(400, 'invalid content length') from None
        if declared_length > MAX_BODY:
            _audit(root, work, 'TOO_LARGE')
            raise HTTPException(413, 'submission too large')
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > MAX_BODY:
                _audit(root, work, 'TOO_LARGE')
                raise HTTPException(413, 'submission too large')
        try:
            receipt = accept(root, json.loads(body), work=work)
        except (ValueError, TypeError, KeyError, OSError, UnicodeError, json.JSONDecodeError):
            raise HTTPException(422, 'submission failed validation') from None
        return receipt

    return app
