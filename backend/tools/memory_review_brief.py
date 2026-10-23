"""Build a private advisory director brief from verified pilot packet files."""
import argparse
import json
import sys
from pathlib import Path

from app import memory_brief, memory_security, memory_workflow as workflow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start-json', required=True)
    parser.add_argument('--start-sha256', required=True)
    parser.add_argument('--review-packet', required=True)
    parser.add_argument('--packet-sha256', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        start_data = memory_security._private_file(args.start_json, size_limit=100_000)
        packet_data = memory_security._private_file(args.review_packet, size_limit=100_000)
        if workflow._sha(start_data) != args.start_sha256 or workflow._sha(packet_data) != args.packet_sha256:
            raise ValueError('source brief or review packet changed')
        brief = memory_brief.review_brief(json.loads(start_data), json.loads(packet_data))
        out = Path(args.out)
        workflow._private_root(out.parent)
        workflow._new_file(Path(str(out) + '.json'), workflow._canonical(brief))
        workflow._new_file(out, memory_brief.render_markdown(brief).encode('utf-8'))
        print(json.dumps({'brief': str(out), 'candidate_id': brief['candidate_id'],
                          'approval_status': 'ADVISORY_ONLY'}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, json.JSONDecodeError) as error:
        print('review brief generation failed: ' + type(error).__name__, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
