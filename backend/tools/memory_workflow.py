"""Offline Studio Memory proposals. Human signatures are supplied externally."""
import argparse
import json
import sys
from pathlib import Path

from app import memory_workflow as workflow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, help='private workflow directory outside Git')
    actions = parser.add_subparsers(dest='command', required=True)
    init = actions.add_parser('init')
    init.add_argument('--vault', required=True)
    init.add_argument('--director-public', required=True)
    init.add_argument('--producer-public', required=True)
    propose = actions.add_parser('propose')
    propose.add_argument('--report', required=True)
    propose.add_argument('--fields', required=True, help='JSON selectors with excerpts copied from the report')
    packet = actions.add_parser('packet')
    packet.add_argument('--id', required=True)
    packet.add_argument('--action', choices=sorted(workflow.REVIEW_ACTIONS), required=True)
    packet.add_argument('--actor', required=True)
    packet.add_argument('--approval-status', choices=sorted(workflow.STATUSES))
    packet.add_argument('--reason')
    packet.add_argument('--accepted-conflicts', nargs='*')
    packet.add_argument('--out', required=True)
    apply_action = actions.add_parser('apply')
    apply_action.add_argument('--assertion', required=True)
    apply_action.add_argument('--signature', required=True)
    register = actions.add_parser('register')
    register.add_argument('--id', required=True)
    status = actions.add_parser('status')
    status.add_argument('--id', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'init':
            workflow.initialize(args.root, args.vault, args.director_public, args.producer_public)
            print('Private workflow initialized.')
        elif args.command == 'propose':
            fields = json.loads(Path(args.fields).read_text(encoding='utf-8'))
            result = workflow.propose(args.root, args.report, fields)
            print(json.dumps({'id': result['id'], 'workflow_status': 'DRAFT',
                              'unknown_fields': result['unknown_fields']}, ensure_ascii=False))
        elif args.command == 'packet':
            payload = workflow.prepare_assertion(args.root, args.id, args.action, args.actor,
                                                 approval_status=args.approval_status,
                                                 reason=args.reason,
                                                 accepted_conflicts=args.accepted_conflicts)
            target = Path(args.out)
            workflow._new_file(target, workflow._canonical(payload))
            print('Unsigned review packet prepared. A human signature is required.')
        elif args.command == 'apply':
            assertion = json.loads(Path(args.assertion).read_text(encoding='utf-8'))
            signature = Path(args.signature).read_bytes()
            print(workflow.apply_assertion(args.root, assertion, signature))
        elif args.command == 'register':
            print(json.dumps(workflow.register(args.root, args.id)))
        elif args.command == 'status':
            print(json.dumps(workflow.status(args.root, args.id), ensure_ascii=False))
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as error:
        print(f'Workflow operation failed: {type(error).__name__}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
