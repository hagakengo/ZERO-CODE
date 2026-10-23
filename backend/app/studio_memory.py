"""Strict, read-only access to a curated Obsidian-compatible Markdown vault.

The accepted frontmatter is a deliberately small YAML 1.2 subset: JSON-quoted
scalars and JSON flow arrays. Unreviewed OS documents are never imported here.
"""
import json
import os
import re
import unicodedata
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from app.memory_security import verify

router = APIRouter(prefix='/api/studio/memory', tags=['studio-memory-readonly'])
ID = re.compile(r'^[A-Z][A-Z0-9-]{2,79}$')
FIELDS = {'id', 'title', 'kind', 'approval_status', 'source', 'updated_at',
          'related', 'assets', 'sources', 'approval_scope'}
STATUSES = {'APPROVED', 'DRAFT', 'CANDIDATE', 'REWORK', 'UNVERIFIED'}


def _vault():
    configured = os.environ.get('STUDIO_MEMORY_DIR')
    if not configured:
        raise HTTPException(503, 'Studio Memoryは未接続です')
    root = Path(configured).resolve()
    if not root.is_dir():
        raise HTTPException(503, 'Studio Memoryを確認できません')
    return root


def _parse(path):
    if path.is_symlink() or path.stat().st_size > 32_768:
        raise ValueError('unsafe memory file')
    raw = path.read_text(encoding='utf-8')
    if not raw.startswith('---\n'):
        raise ValueError('missing frontmatter')
    parts = raw.split('\n---\n', 1)
    if len(parts) != 2:
        raise ValueError('unterminated frontmatter')
    meta = {}
    for line in parts[0][4:].splitlines():
        key, sep, value = line.partition(':')
        if not sep or key not in FIELDS or key in meta:
            raise ValueError('invalid frontmatter field')
        meta[key] = json.loads(value.strip())
    if set(meta) != FIELDS or not all(isinstance(meta[k], str) and meta[k]
                                      for k in FIELDS - {'related', 'assets', 'sources'}):
        raise ValueError('incomplete frontmatter')
    if not ID.fullmatch(meta['id']) or meta['id'] != path.stem:
        raise ValueError('invalid memory id')
    if meta['approval_status'] not in STATUSES:
        raise ValueError('invalid approval status')
    if not isinstance(meta['related'], list) or not all(isinstance(x, str) and ID.fullmatch(x)
                                                        for x in meta['related']):
        raise ValueError('invalid related ids')
    if not isinstance(meta['assets'], list) or not all(isinstance(x, str) and len(x) <= 120
                                                       for x in meta['assets']):
        raise ValueError('invalid assets')
    if not isinstance(meta['sources'], list) or not all(isinstance(x, str) and 0 < len(x) <= 200
                                                        for x in meta['sources']):
        raise ValueError('invalid sources')
    body = parts[1].strip()
    return {**meta, 'body': body}


def _load_all():
    root = _vault()
    try:
        notes = {}
        for path in sorted(root.iterdir()):
            if path.suffix != '.md':
                continue
            note = _parse(path)
            if note['id'] in notes:
                raise ValueError('duplicate memory id')
            notes[note['id']] = note
        return notes
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError):
        raise HTTPException(503, 'Studio Memoryの形式を確認できません') from None


def _normal(text):
    return unicodedata.normalize('NFKC', text).casefold()


def _terms(query):
    normalized = _normal(query)
    # Separate Japanese script runs and Latin IDs; particles stay out of an
    # otherwise meaningful mixed-script query. This is keyword search, not NLP.
    pieces = re.findall(r'[a-z0-9]+|[一-龯々〆ヵヶ]+|[ァ-ヴー]+|[ぁ-ん]+', normalized)
    content = [p for p in pieces if not re.fullmatch(r'[ぁ-ん]+', p)]
    return content or normalized.split()


def _response(data):
    return JSONResponse(data, headers={'Cache-Control': 'private, no-store'})


@router.get('/search')
def search(request: Request, q: str = Query(default='', max_length=120), approved_only: bool = False,
           authorization: str | None = Header(default=None)):
    access = verify(request, 'search', authorization)
    approved_only = approved_only or access == 'approved'
    words = _terms(q)
    result = []
    for note in _load_all().values():
        if approved_only and note['approval_status'] != 'APPROVED':
            continue
        haystack = _normal(' '.join([note['title'], note['kind'], note['source'],
                                     note['body'], *note['assets']]))
        if all(word in haystack for word in words):
            result.append({k: v for k, v in note.items() if k != 'body'})
    return _response({'results': result, 'count': len(result), 'approved_only': approved_only})


@router.get('/{memory_id}')
def detail(request: Request, memory_id: str, approved_only: bool = False,
           authorization: str | None = Header(default=None)):
    access = verify(request, 'detail', authorization)
    approved_only = approved_only or access == 'approved'
    if not ID.fullmatch(memory_id):
        raise HTTPException(404, '記憶が見つかりません')
    note = _load_all().get(memory_id)
    if note is None or (approved_only and note['approval_status'] != 'APPROVED'):
        raise HTTPException(404, '記憶が見つかりません')
    return _response(note)
