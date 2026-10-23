"""Offline administration and client for the isolated Studio Memory DRAFT channel."""
import argparse
import json
import secrets
import sys
import urllib.error
import urllib.request
from pathlib import Path

from app import memory_security, memory_submission, memory_workflow as workflow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    init = commands.add_parser('init')
    init.add_argument('--root', required=True)
    init.add_argument('--inbox', required=True)
    issue = commands.add_parser('issue')
    issue.add_argument('--root', required=True)
    issue.add_argument('--out', required=True)
    issue.add_argument('--ttl', type=int, default=900)
    revoke = commands.add_parser('revoke-work02')
    revoke.add_argument('--root', required=True)
    receipts = commands.add_parser('receipts')
    receipts.add_argument('--root', required=True)
    receipt = commands.add_parser('receipt')
    receipt.add_argument('--root', required=True)
    receipt.add_argument('--id', required=True)
    recover = commands.add_parser('recover')
    recover.add_argument('--root', required=True)
    check = commands.add_parser('check')
    check.add_argument('--root', required=True)
    packet = commands.add_parser('packet')
    packet.add_argument('--root', required=True)
    packet.add_argument('--id', required=True)
    packet.add_argument('--out', required=True)
    serve = commands.add_parser('serve')
    serve.add_argument('--root', required=True)
    serve.add_argument('--port', type=int, required=True)
    submit = commands.add_parser('submit')
    submit.add_argument('--url', required=True)
    submit.add_argument('--token-file', required=True)
    submit.add_argument('--report', required=True)
    submit.add_argument('--candidate', required=True)
    submit.add_argument('--receipt-id', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'init':
            memory_submission.initialize(args.root, args.inbox)
            result = {'state': 'DRAFT_SUBMISSION_ONLY', 'root': args.root}
        elif args.command == 'issue':
            token = memory_submission.issue(args.root, ttl=args.ttl)
            workflow._new_file(args.out, token.encode())
            result = {'credential_file': args.out, 'lifetime_seconds': args.ttl}
        elif args.command == 'revoke-work02':
            memory_submission.revoke_work(args.root)
            result = {'work': 'work02', 'state': 'REVOKED'}
        elif args.command == 'receipts':
            result = memory_submission.list_receipts(args.root)
        elif args.command == 'receipt':
            result = memory_submission.receipt_detail(args.root, args.id)
        elif args.command == 'recover':
            result = memory_submission.recover(args.root)
        elif args.command == 'check':
            result = memory_submission.integrity_check(args.root)
        elif args.command == 'packet':
            packet_data = memory_submission.review_packet(args.root, args.id)
            workflow._new_file(args.out, json.dumps(packet_data, ensure_ascii=False, indent=2).encode())
            result = {'packet': args.out, 'formal_signature': False}
        elif args.command == 'serve':
            import uvicorn
            uvicorn.run(memory_submission.create_app(args.root), host='127.0.0.1', port=args.port,
                        access_log=False, log_level='warning')
            return 0
        else:
            if not args.url.startswith('http://127.0.0.1:'):
                raise ValueError('only loopback submission is allowed')
            source = workflow._read_file(args.report)
            fields = json.loads(workflow._read_file(args.candidate))
            fields = {key: fields[key] for key in workflow.REQUIRED}
            fields['proposed_by'] = 'work02'
            envelope = {'receipt_id': args.receipt_id, 'source_text': source.decode('utf-8'),
                'source_sha256': workflow._sha(source), 'fields': fields, 'project': 'ZERO CODE',
                'unknowns': [], 'workflow_status': 'DRAFT', 'approval_status': 'DRAFT'}
            token = memory_security._private_file(args.token_file, size_limit=2048).decode()
            request = urllib.request.Request(args.url.rstrip('/') + '/submit',
                data=workflow._canonical(envelope), headers={'Authorization': 'Bearer ' + token,
                    'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(request, timeout=15) as response:
                result = json.load(response)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, UnicodeError, KeyError, json.JSONDecodeError, urllib.error.URLError) as error:
        print('DRAFT submission failed: ' + type(error).__name__, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
