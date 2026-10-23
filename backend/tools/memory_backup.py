"""Offline copy-only snapshots. Stop writers first; never back up real signer secrets."""
import argparse
import json
import sys

from app import memory_backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    backup = commands.add_parser('backup')
    for label in sorted(memory_backup.LABELS):
        backup.add_argument('--' + label.replace('_', '-'), required=True)
    backup.add_argument('--out', required=True)
    backup.add_argument('--anchor', required=True)
    verify = commands.add_parser('verify')
    verify.add_argument('--snapshot', required=True)
    restore = commands.add_parser('restore')
    restore.add_argument('--snapshot', required=True)
    restore.add_argument('--out', required=True)
    restore.add_argument('--anchor', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'backup':
            roots = {label: getattr(args, label) for label in memory_backup.LABELS}
            result = memory_backup.create_snapshot(roots, args.out, args.anchor)
        elif args.command == 'verify':
            manifest = memory_backup.verify_snapshot(args.snapshot)
            result = {'sequence': manifest['sequence'], 'files': len(manifest['files']), 'integrity': 'MATCH'}
        else:
            result = memory_backup.restore_snapshot(args.snapshot, args.out, args.anchor)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, json.JSONDecodeError) as error:
        print('snapshot operation failed: ' + type(error).__name__, file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
