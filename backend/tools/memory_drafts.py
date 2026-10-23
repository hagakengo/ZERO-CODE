"""Private, offline DRAFT inbox. No signing, registration, or Reader write routes."""
import argparse
import json
import sys
from pathlib import Path

from app import memory_drafts as drafts
from app import memory_workflow as workflow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, help='private DRAFT inbox outside Git')
    commands = parser.add_subparsers(dest='command', required=True)
    init = commands.add_parser('init')
    init.add_argument('--vault', required=True)
    add = commands.add_parser('add')
    add.add_argument('--report', required=True)
    add.add_argument('--fields', required=True)
    add.add_argument('--project', default='ZERO CODE')
    add.add_argument('--unknowns', help='optional JSON array of unresolved questions')
    listed = commands.add_parser('list')
    listed.add_argument('--work', choices=['work01', 'work02'])
    listed.add_argument('--character')
    listed.add_argument('--asset')
    listed.add_argument('--q')
    detail = commands.add_parser('detail')
    detail.add_argument('--id', required=True)
    packet = commands.add_parser('packet')
    packet.add_argument('--id', required=True)
    packet.add_argument('--out', required=True)
    review = commands.add_parser('record-review')
    review.add_argument('--id', required=True)
    review.add_argument('--result', choices=sorted(drafts.REVIEWS), required=True)
    review.add_argument('--reviewer', required=True)
    review.add_argument('--note', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'init':
            drafts.initialize(args.root, args.vault)
            result = {'state': 'DRAFT_ONLY', 'count': 0}
        elif args.command == 'add':
            fields = json.loads(Path(args.fields).read_text(encoding='utf-8'))
            unknowns = json.loads(Path(args.unknowns).read_text(encoding='utf-8')) if args.unknowns else []
            result = drafts.add(args.root, args.report, fields, project=args.project, unknowns=unknowns)
            result = {'id': result['id'], 'workflow_status': 'DRAFT', 'approval_status': 'DRAFT'}
        elif args.command == 'list':
            result = drafts.list_candidates(args.root, proposed_by=args.work,
                                            character=args.character, asset=args.asset, q=args.q)
        elif args.command == 'detail':
            result = drafts.detail(args.root, args.id)
        elif args.command == 'packet':
            result = drafts.review_packet(args.root, args.id)
            workflow._new_file(args.out, json.dumps(result, ensure_ascii=False, indent=2).encode())
            result = {'packet': str(Path(args.out).resolve()), 'formal_signature': False}
        elif args.command == 'record-review':
            result = drafts.record_review(args.root, args.id, args.result, args.reviewer, args.note)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as error:
        print(f'DRAFT inbox operation failed: {type(error).__name__}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
