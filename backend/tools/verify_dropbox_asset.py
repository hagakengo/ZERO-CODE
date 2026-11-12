"""Independently verify one registration candidate against Dropbox."""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx



def verify(candidate, verifier, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Dropbox-API-Arg": json.dumps({"path": candidate["dropbox_file_id"]}),
    }
    with httpx.stream("POST", "https://content.dropboxapi.com/2/files/download",
                      headers=headers, timeout=60) as response:
        if response.status_code == 409:
            response.read()
            if response.json().get("error_summary", "").startswith("path/not_found"):
                raise ValueError("Dropbox file ID not found")
        if response.status_code != 200:
            raise ValueError(f"Dropbox download failed (HTTP {response.status_code})")
        metadata = json.loads(response.headers["Dropbox-API-Result"])
        digest = hashlib.sha256()
        size = 0
        for chunk in response.iter_bytes():
            digest.update(chunk)
            size += len(chunk)

    if (metadata["id"] != candidate["dropbox_file_id"]
            or metadata["path_display"] != candidate["dropbox_path"]):
        raise ValueError("Dropbox ID or path mismatch")
    if metadata["size"] != size or size != candidate["size_bytes"]:
        raise ValueError("Dropbox size mismatch")
    if digest.hexdigest() != candidate["sha256"]:
        raise ValueError("Dropbox SHA-256 mismatch")

    return {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "verifier": verifier,
        "method": "Dropbox files/download by file ID; SHA-256 of downloaded bytes",
        "dropbox_rev": metadata["rev"],
        "candidate": candidate,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path, help="AssetDraft JSON before adding provenance")
    parser.add_argument("evidence", type=Path, help="New private file to store the receipt")
    parser.add_argument("--verifier", required=True)
    args = parser.parse_args()
    token = os.getenv("DROPBOX_READ_TOKEN")
    if not token:
        parser.exit(1, "DROPBOX_READ_TOKEN is required\n")
    key = os.getenv("ZERO_CODE_ASSET_RECEIPT_KEY", "")
    if key and len(key) < 32:
        parser.exit(1, "ZERO_CODE_ASSET_RECEIPT_KEY must be at least 32 characters\n")
    try:
        candidate = json.loads(args.candidate.read_text())
        # Only retain registration fields, never arbitrary supplied metadata.
        fields = ("asset_id", "version", "episode", "cut", "status", "dropbox_file_id",
                  "dropbox_path", "size_bytes", "sha256")
        receipt = verify({field: candidate[field] for field in fields}, args.verifier, token)
        contents = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode()
        fd = os.open(args.evidence, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as evidence:
            evidence.write(contents)
    except (KeyError, TypeError, ValueError, OSError, httpx.HTTPError) as exc:
        message = str(exc) if type(exc) is ValueError else type(exc).__name__
        parser.exit(1, f"Verification failed: {message}\n")
    provenance = {"verifier": args.verifier, "evidence_sha256": hashlib.sha256(contents).hexdigest()}
    if key:
        from app.asset_receipt import sign_registration
        signature = sign_registration(dict(receipt["candidate"], provenance=provenance), key)
        print(json.dumps({"provenance": provenance, "receipt_signature": signature}))
    else:
        print(json.dumps(provenance))


if __name__ == "__main__":
    main()
