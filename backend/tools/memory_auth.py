"""Offline Studio Memory credential administration. Never prints token contents."""
import argparse
import os
import stat
import sys
from pathlib import Path

from app import memory_security


def private_token(path, token):
    target = Path(path)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='ascii') as stream:
            stream.write(token + '\n')
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        target.unlink(missing_ok=True)
        raise


def read_private_token(path):
    target = Path(path)
    fd = os.open(target, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_size > 2049:
            raise ValueError('unsafe token file')
        data = os.read(fd, 2050)
        if len(data) > 2049:
            raise ValueError('oversized token file')
        return data.decode('ascii').strip()
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--auth-dir', required=True, help='private directory outside Git')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('init')
    issue = commands.add_parser('issue')
    issue.add_argument('--work', choices=sorted(memory_security.WORK_IDS), required=True)
    issue.add_argument('--access', choices=sorted(memory_security.ACCESS), required=True)
    issue.add_argument('--operations', nargs='+', choices=sorted(memory_security.OPERATIONS), default=['search', 'detail'])
    issue.add_argument('--ttl', type=int, default=300)
    issue.add_argument('--out', required=True)
    revoke_work = commands.add_parser('revoke-work')
    revoke_work.add_argument('--work', choices=sorted(memory_security.WORK_IDS), required=True)
    revoke_token = commands.add_parser('revoke-token')
    revoke_token.add_argument('--token-file', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'init':
            memory_security.initialize(args.auth_dir)
            print('Authentication directory initialized.')
        elif args.command == 'issue':
            token = memory_security.issue(args.auth_dir, args.work, args.access, args.operations, args.ttl)
            private_token(args.out, token)
            print(f'Credential written for {args.work}; expires in {args.ttl} seconds.')
        elif args.command == 'revoke-work':
            memory_security.revoke_work(args.auth_dir, args.work)
            print(f'Existing credentials revoked for {args.work}.')
        elif args.command == 'revoke-token':
            memory_security.revoke_token(args.auth_dir, read_private_token(args.token_file))
            print('Credential revoked.')
    except (OSError, ValueError) as error:
        print(f'Credential operation failed: {type(error).__name__}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
