"""Loopback-only integration checks against an explicitly started pilot.
Requires STUDIO_TEST_URL and server-side STUDIO_* credentials in the environment.
Never logs secrets, IDs, source paths or returned media. Does not change OS data.
"""
import hashlib
import hmac
import json
import os
import time
import uuid
from urllib.parse import urlsplit

import httpx


def run():
    base = os.environ['STUDIO_TEST_URL'].rstrip('/')
    url = urlsplit(base)
    if url.scheme != 'http' or url.hostname not in {'127.0.0.1', 'localhost', '::1'}:
        raise ValueError('integration tests require an explicit loopback URL')
    results = []

    def check(name, ok):
        if not ok:
            raise AssertionError(name)
        results.append({'test': name, 'pass': True})

    with httpx.Client(base_url=base, follow_redirects=False, timeout=30) as client:
        check('anonymous index denied', client.get('/api/studio/index').status_code == 401)
        login = client.post('/api/studio/session', headers={'Origin': base}, data={
            'username': os.environ['STUDIO_VIEWER_USER'], 'password': os.environ['STUDIO_VIEWER_PASSWORD']})
        check('local pilot login succeeds', login.status_code == 303)
        data = client.get('/api/studio/index').json()
        version = data['cuts'][0]['versions'][-1]
        ids = {'image': version['drawings'][0]['media']['media_id'], 'video': version['video']['media_id']}
        check('snapshot provenance visible in DTO', isinstance(data['revision'], int) and bool(data['imported_at']))
        check('raw documents withheld', all(not v['documents'] for c in data['cuts'] for v in c['versions']))
        # A correctly signed short session must work BEFORE it expires; this
        # distinguishes expiry rejection from an invalid-signature rejection.
        payload = f'v1.{int(time.time()) + 3}.{uuid.uuid4()}'
        signature = hmac.new(os.environ['STUDIO_SESSION_SECRET'].encode(), payload.encode(), hashlib.sha256).hexdigest()
        client.cookies.clear()
        headers = {'Cookie': 'zcs_reader=' + payload + '.' + signature}
        for kind, ident in ids.items():
            response = client.get('/api/studio/media/' + ident, headers={**headers, 'Range': 'bytes=0-15'})
            check(kind + ' short session works before expiry', response.status_code == 206 and len(response.content) == 16)
        time.sleep(3.1)
        check('expired index denied', client.get('/api/studio/index', headers=headers).status_code == 401)
        for kind, ident in ids.items():
            for method in ['GET', 'HEAD']:
                response = client.request(method, '/api/studio/media/' + ident, headers={**headers, 'Range': 'bytes=0-15'})
                check(kind + ' expired ' + method + ' denied', response.status_code == 401)
                check(kind + ' expired ' + method + ' no-store', 'no-store' in response.headers.get('cache-control', ''))
                check(kind + ' expired ' + method + ' no media header', 'x-asset-sha256' not in response.headers and 'content-range' not in response.headers)
    return results


if __name__ == '__main__':
    print(json.dumps(run(), ensure_ascii=False, indent=2))
