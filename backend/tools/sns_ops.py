#!/usr/bin/env python3
"""Operate the local SNS ledger without printing credentials."""
import argparse
import json
import os
import urllib.error
import urllib.request


def call(base_url: str, path: str, token: str, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(
        base_url.rstrip("/") + path,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json", "X-ZCS-SNS-Token": token},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            detail = json.load(error).get("detail", "request failed")
        except Exception:
            detail = "request failed"
        raise SystemExit(f"SNS operation failed ({error.code}): {detail}") from None


def main():
    parser = argparse.ArgumentParser(description="ZERO CODE OS SNS operations")
    parser.add_argument("action", choices=("detect", "apply", "refresh", "run-detect", "run-refresh"))
    parser.add_argument("--base-url", default=os.getenv("ZERO_CODE_OS_URL", "http://127.0.0.1:8000"))
    args = parser.parse_args()
    token = os.getenv("SNS_WRITE_TOKEN", "").strip()
    if not token:
        raise SystemExit("SNS_WRITE_TOKEN is required.")
    if args.action in ("detect", "apply", "run-detect"):
        result = call(args.base_url, "/api/sns/reconcile", token,
                      {"dry_run": args.action == "detect", "automation": args.action == "run-detect"})
    else:
        path = "/api/sns/refresh?automation=true" if args.action == "run-refresh" else "/api/sns/refresh"
        result = call(args.base_url, path, token)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
