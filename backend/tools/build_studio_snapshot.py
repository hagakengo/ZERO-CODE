"""Explicit operator import to a NEW private directory; never writes source data.
Config is private, untracked JSON: production_file, packages [{version,path}],
media_roots [paths], optional max_file_bytes. No application startup import.
"""
import argparse
import datetime
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path

ALLOWED = {'.png', '.jpg', '.jpeg', '.mp4', '.md', '.txt', '.csv', '.json'}


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


# Free text is withheld unless its exact digest was explicitly reviewed by an
# operator. Pattern checks are a second barrier, never the disclosure policy.
SENSITIVE = re.compile(r"(?:/Users/|/home/|/etc/|/var/|[A-Za-z]:[\\/]|\\\\|https?://[^\s/]+:[^\s/]+@|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|(?:password|passwd|secret|token|api[_-]?key|authorization)\s*[:=]|-----BEGIN .*PRIVATE KEY|\b(?:\+?\d[ -]?){10,15}\b)", re.I)
SAFE_STATES = {'TEST', 'MASTER', 'INVENTORY', 'CANDIDATE', 'ARCHIVE', 'DRAFT',
               'PASS', 'REWORK', 'FAIL', 'UNVERIFIED'}


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,120}', value):
        raise ValueError('unsafe identifier; import stopped')
    return value


def public_text(value, approved=frozenset()):
    if not isinstance(value, str) or not value:
        return '未確認'
    if value in SAFE_STATES or re.fullmatch(r'r\d{2}', value):
        return value
    digest = hashlib.sha256(value.encode()).hexdigest()
    if digest in approved and len(value) <= 4000 and not SENSITIVE.search(value):
        return value
    return '機密確認待ち／原本は非公開で保持'


def build(config, destination):
    """Publish atomically only after every copy and receipt has succeeded."""
    destination = Path(destination)
    if destination.exists():
        raise ValueError('destination must be new; preserve prior snapshots')
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.studio-import-', dir=destination.parent))
    try:
        result = _build(config, staging)
        # Completion detects partial/corrupt writes; it is not a digital signature.
        (staging / 'COMPLETE').write_text(sha(staging / 'manifest.json'))
        (staging / 'COMPLETE').chmod(0o600)
        if destination.exists():
            raise ValueError('destination appeared during import')
        staging.rename(destination)
        return result
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def _build(config, destination):
    destination = Path(destination)
    source = Path(config['production_file']).resolve(strict=True)
    before = sha(source)
    data = json.loads(source.read_text())
    if not isinstance(data.get('revision'), int) or not all(isinstance(data.get(k), list)
            for k in ['assets', 'history', 'projects']):
        raise ValueError('unsupported production schema')
    if len({a['id'] for a in data['assets']}) != len(data['assets']):
        raise ValueError('duplicate IDs')
    roots = [Path(p).resolve(strict=True) for p in config['media_roots']]
    limit = int(config.get('max_file_bytes', 30_000_000))
    approved = frozenset(config.get('approved_text_sha256', []))
    text = lambda value: public_text(value, approved)
    (destination / 'media').mkdir(mode=0o700)
    files, imports = {}, []
    total_bytes = 0
    total_limit = int(config.get('max_total_bytes', 1_000_000_000))

    def attach(path):
        nonlocal total_bytes
        if not path:
            return None
        p = Path(path)
        if not p.exists():
            return None
        try:
            if p.is_symlink():
                return None
            resolved = p.resolve(strict=True)
            if not any(resolved.is_relative_to(root) for root in roots):
                return None
            if resolved.suffix.lower() not in ALLOWED or not resolved.is_file() or resolved.stat().st_size > limit:
                return None
            # Text documents are projected separately; raw notes never enter media.
            if resolved.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.mp4'}:
                return None
            initial_stat = resolved.stat()
            digest = sha(resolved)
            ident = digest
            target = destination / 'media' / (digest + resolved.suffix.lower())
            if not target.exists():
                if total_bytes + initial_stat.st_size > total_limit:
                    raise ValueError('snapshot capacity exceeded; not published')
                total_bytes += initial_stat.st_size
                shutil.copyfile(resolved, target)
                target.chmod(0o600)
            current_stat = resolved.stat()
            changed = (current_stat.st_ino, current_stat.st_size, current_stat.st_mtime_ns) != (initial_stat.st_ino, initial_stat.st_size, initial_stat.st_mtime_ns)
            if target.stat().st_size > limit or changed or sha(target) != digest or sha(resolved) != digest:
                raise ValueError('source changed during copy')
            files[ident] = {'copy': str(target.relative_to(destination)), 'sha256': digest}
            imports.append({'id': ident, 'source_path': str(resolved), 'source_sha256': digest,
                            'copy': str(target.relative_to(destination))})
            return {'media_id': ident, 'sha256': digest, 'bytes': target.stat().st_size,
                    'format': resolved.suffix[1:].upper(), 'storage': 'private-copy://' + target.name}
        except (OSError, RuntimeError) as exc:
            raise ValueError('copy failed; snapshot not published') from exc

    assets = []
    for a in data['assets']:
        meta = a.get('metadata', {})
        linked = attach(a.get('original_path'))
        assets.append({'id': identifier(a['id']), 'title': text(a.get('title')), 'project': identifier(a['project']) if a.get('project') else '',
            'version': text(meta.get('version', '未登録')), 'state': text(a.get('status')),
            'approval': '表情作画の参考候補／完成原画・MASTER未承認' if meta.get('reference_candidate') else '原台帳の状態は別記／本画面での採用判定なし',
            'source': '原本の非公開台帳で保持', 'review': text(meta.get('director_review', '未確認')),
            'media': linked, 'availability': '取得済み' if linked else '未取得／閲覧コピー未作成'})
    versions = []
    for package in config.get('packages', []):
        version = package['version']
        if not re.fullmatch(r'r\d{2}', version):
            raise ValueError('invalid version')
        package_root = Path(package['path']).resolve(strict=True)
        drawings = []
        for p in sorted((package_root / 'rough_keys').glob('*.png')):
            if not re.match(r'^K\d{2}', p.name):
                continue
            linked = attach(p)
            drawings.append({'id': p.name[:3], 'title': p.name[:3], 'media': linked})
        if len({d['id'] for d in drawings}) != len(drawings):
            raise ValueError('duplicate drawing IDs')
        videos = [p for p in package_root.glob('*.mp4') if version in p.name]
        video = attach(videos[0]) if len(videos) == 1 else None
        # Arbitrary Markdown may contain secrets/PII. Do not publish original text.
        docs = []
        qc_text = '\n'.join(p.read_text() for p in package_root.glob('*.md') if 'QC' in p.name)
        match = re.search(r'\*\*(PASS|REWORK|FAIL|UNVERIFIED)(?=[\s／｜。継])', qc_text)
        verdict = match.group(1) if match else 'UNVERIFIED'
        versions.append({'version': version, 'state': 'TEST', 'verdict': verdict,
                         'drawings': drawings, 'video': video, 'documents': docs})
    reviews = []
    packages = config.get('packages', [])
    review_sources = [Path(p['path']) / '監督レビュー_r02_受領記録.json' for p in packages]
    for p in review_sources:
        if p.is_file():
            r = json.loads(p.read_text())
            reviews.append({'id': 'director-r02', 'version': 'r02', 'verdict': 'REWORK' if 'REWORK' in str(r.get('overall', '')) else 'UNVERIFIED',
                'scope': '監督の静止画レビュー受領／原文は機密確認待ち', 'video_scope': '動画の監督合格は未確認',
                'date': None, 'actor': '監督AI', 'reason': '受領資料の判定／完成原画・MASTER承認とは別',
                'keys': {}, 'next_actions': []})
            break
    # Work self-QC is a separate source; never forge a director pass.
    for v in versions:
        reviews.append({'id': 'work-' + v['version'], 'version': v['version'], 'verdict': v['verdict'],
            'scope': 'Work自己QC／監督評価とは別', 'video_scope': '監督合格未確認', 'date': None,
            'actor': 'Work', 'reason': '第一原画TEST。次工程への移行は保留。', 'keys': {}, 'next_actions': []})
    latest = max(versions, key=lambda v: v['version'])['version'] if versions else None
    index = {'schema_version': 2, 'revision': data['revision'], 'source_sha256': before,
        'imported_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'disclosure': '未確認の自由記述・原文資料は非配信。画像・動画内の機密情報は別途目視審査が必要。',
        'mode': '読み取り専用・閲覧用スナップショット／本番同期ではない',
        'projects': [{'id': identifier(p['id']), 'title': text(p.get('title')), 'state': text(p.get('state'))} for p in data['projects']],
        'assets': assets, 'history': [{'date': None, 'note': text(h.get('note'))} for h in data['history'][-12:]],
        'cuts': [{'id': 'ep00-yuna-rain', 'episode': 'EP00', 'title': 'ユナの雨粒シーン',
            'purpose': '雨粒の発見→追視→感情変化→小さな微笑み。同じユナが自然に演技しているか。',
            'stage': '第一原画・演技設計TEST', 'verdict': next((v['verdict'] for v in versions if v['version'] == latest), 'UNVERIFIED'),
            'latest': latest, 'next_stage_allowed': False, 'producer_approval': '未確認／完成素材未承認',
            'versions': versions}], 'reviews': reviews}
    if sha(source) != before:
        raise ValueError('production changed during import')
    manifest = {'schema_version': 2, 'index': index, 'files': files}
    (destination / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    (destination / 'manifest.json').chmod(0o600)
    (destination / 'import_receipt.private.json').write_text(json.dumps({'production_path': str(source),
        'production_sha256_before': before, 'production_sha256_after': sha(source),
        'source_revision': data['revision'], 'asset_ids': [a['id'] for a in data['assets']],
        'files': imports}, ensure_ascii=False, indent=2))
    (destination / 'import_receipt.private.json').chmod(0o600)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    result = build(json.loads(args.config.read_text()), args.destination)
    print(json.dumps({'revision': result['index']['revision'], 'assets': len(result['index']['assets']),
                      'private_files': len(result['files'])}))
