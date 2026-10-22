"""Private, read-only production snapshots. No DB connection or startup writes."""
import hashlib
import hmac
import json
import os
import re
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter(prefix='/api/studio', tags=['studio-readonly'])
ID = re.compile(r'^[a-zA-Z0-9_-]{1,120}$')
TYPES = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.mp4': 'video/mp4',
         '.md': 'text/plain; charset=utf-8', '.txt': 'text/plain; charset=utf-8',
         '.csv': 'text/plain; charset=utf-8', '.json': 'text/plain; charset=utf-8'}


def require_reader(authorization: str | None = Header(default=None)):
    token = os.environ.get('STUDIO_READER_TOKEN', '')
    if len(token) < 32:
        raise HTTPException(503, '閲覧サービスの認証が未設定です')
    supplied = authorization or ''
    if not hmac.compare_digest(supplied.encode(), ('Bearer ' + token).encode()):
        raise HTTPException(401, '認証が必要です')


def load_snapshot():
    configured = os.environ.get('STUDIO_SNAPSHOT_DIR')
    if not configured:
        raise HTTPException(503, '制作データは未接続です')
    root = Path(configured).resolve()
    try:
        manifest_path = root / 'manifest.json'
        if manifest_path.is_symlink():
            raise ValueError('symlink manifest')
        data = json.loads(manifest_path.read_text())
        if data.get('schema_version') != 1 or not isinstance(data.get('index'), dict):
            raise ValueError('schema')
        if not isinstance(data.get('files'), dict):
            raise ValueError('files')
    except (OSError, ValueError, TypeError):
        raise HTTPException(503, '閲覧用データを確認できません') from None
    return root, data


@router.get('/index', dependencies=[Depends(require_reader)])
def index():
    _, data = load_snapshot()
    # Explicit DTO only: original absolute paths and operator configuration stay private.
    return JSONResponse(data['index'], headers={'Cache-Control': 'private, no-store'})


@router.api_route('/media/{asset_id}', methods=['GET', 'HEAD'], dependencies=[Depends(require_reader)])
def media(asset_id: str):
    if not ID.fullmatch(asset_id):
        raise HTTPException(404, '素材が見つかりません')
    root, data = load_snapshot()
    record = data['files'].get(asset_id)
    if not record:
        raise HTTPException(404, '素材は未取得です')
    try:
        relative = Path(record['copy'])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('path')
        path = root / relative
        if any(p.is_symlink() for p in [path, *path.parents] if p != root.parent):
            raise ValueError('symlink')
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
        if resolved.suffix.lower() not in TYPES or not resolved.is_file():
            raise ValueError('type')
        with resolved.open('rb') as f:
            digest = hashlib.file_digest(f, 'sha256').hexdigest()
        if not hmac.compare_digest(digest, record['sha256']):
            raise ValueError('integrity')
    except (OSError, ValueError, KeyError, TypeError):
        raise HTTPException(409, '素材の整合性を確認できません') from None
    return FileResponse(resolved, media_type=TYPES[resolved.suffix.lower()], headers={
        'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff',
        'Content-Security-Policy': "default-src 'none'; frame-ancestors 'self'",
        'Content-Disposition': 'inline', 'X-Asset-SHA256': digest,
    })


# Dedicated loopback reader excludes all legacy write/metrics/integration endpoints.
app = FastAPI(title='ZERO CODE Studio read-only viewer', docs_url=None, redoc_url=None,
              openapi_url=None)


@app.middleware('http')
async def private_responses(request: Request, call_next):
    response = await call_next(request)
    response.headers['Cache-Control'] = 'private, no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


app.include_router(router)
