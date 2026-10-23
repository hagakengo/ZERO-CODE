"""Generate private production briefs from an authenticated loopback Reader."""
import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from app import memory_brief, memory_security, memory_workflow as workflow
from tools.memory_auth import read_private_token


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise ValueError('Reader redirect refused')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--token-file', required=True)
    parser.add_argument('--target', required=True)
    parser.add_argument('--query', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--review-packet')
    parser.add_argument('--packet-sha256')
    args = parser.parse_args()
    try:
        parsed = urllib.parse.urlsplit(args.url)
        if (parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or not parsed.port
                or parsed.username or parsed.password or parsed.path not in ('', '/')
                or parsed.query or parsed.fragment):
            raise ValueError('loopback Reader required')
        token = read_private_token(args.token_file)
        opener = urllib.request.build_opener(_NoRedirect)
        def fetch(path):
            request = urllib.request.Request(args.url.rstrip('/') + path,
                                             headers={'Authorization': 'Bearer ' + token})
            with opener.open(request, timeout=10) as response:
                data = response.read(100_001)
                if len(data) > 100_000:
                    raise ValueError('Reader response too large')
                return json.loads(data)
        notes = memory_brief.collect(fetch, args.query)
        start = memory_brief.start_brief(args.target, args.query, notes)
        brief = start
        if args.review_packet:
            if not args.packet_sha256:
                raise ValueError('review packet digest required')
            packet_data = memory_security._private_file(args.review_packet, size_limit=100_000)
            if workflow._sha(packet_data) != args.packet_sha256:
                raise ValueError('review packet changed')
            packet = json.loads(packet_data)
            brief = memory_brief.review_brief(start, packet)
        out = Path(args.out)
        workflow._private_root(out.parent)
        workflow._new_file(Path(str(out) + '.json'), workflow._canonical(brief))
        workflow._new_file(out, memory_brief.render_markdown(brief).encode('utf-8'))
        print(json.dumps({'brief': str(out), 'kind': brief['kind'], 'memory_count': len(notes),
                          'approval_status': 'REFERENCE_ONLY'}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, UnicodeError, json.JSONDecodeError, urllib.error.URLError) as error:
        print('brief generation failed: ' + type(error).__name__, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
