"""Authenticate the exact registration metadata attested by a trusted verifier."""
import hashlib
import hmac
import json


def sign_registration(registration: dict, key: str) -> str:
    canonical = json.dumps(registration, sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(key.encode(), b"zero-code-asset-receipt-v1\x00" + canonical, hashlib.sha256).hexdigest()
