#!/usr/bin/env python3
"""Create a consistent SQLite backup before an SNS schema rollout."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from datetime import datetime, timezone


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    url = os.getenv("DATABASE_URL", "")
    if not url.startswith("sqlite:///"):
        raise SystemExit("This helper only supports an explicitly configured sqlite:/// DATABASE_URL.")
    source = Path(url.removeprefix("sqlite:///")).resolve()
    if not source.is_file():
        raise SystemExit("Configured SQLite database does not exist.")
    destination = args.destination.resolve()
    destination.mkdir(mode=0o700, parents=True, exist_ok=True)
    if destination.stat().st_mode & 0o077:
        raise SystemExit("Backup directory must not be group/world accessible.")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = destination / f"zero_code_before_sns_{stamp}.db"
    if backup.exists():
        raise SystemExit("Refusing to overwrite an existing backup.")
    with sqlite3.connect(source) as src, sqlite3.connect(backup) as dst:
        src.backup(dst)
    digest = hashlib.sha256(backup.read_bytes()).hexdigest()
    manifest = backup.with_suffix(".json")
    manifest.write_text(json.dumps({
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_name": source.name,
        "backup_name": backup.name,
        "size": backup.stat().st_size,
        "sha256": digest,
    }, indent=2) + "\n")
    os.chmod(backup, 0o600)
    os.chmod(manifest, 0o600)
    print(json.dumps({"backup": str(backup), "manifest": str(manifest), "sha256": digest}))


if __name__ == "__main__":
    main()
