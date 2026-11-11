import hashlib
import json
import unittest
from unittest.mock import patch

import httpx

from tools.verify_dropbox_asset import verify


class DropboxVerificationTests(unittest.TestCase):
    def setUp(self):
        self.content = b"test asset"
        self.candidate = {
            "dropbox_file_id": "id:test",
            "dropbox_path": "/test/file",
            "size_bytes": len(self.content),
            "sha256": hashlib.sha256(self.content).hexdigest(),
        }

    def test_matches_bytes_and_metadata(self):
        with patch("tools.verify_dropbox_asset.httpx.stream") as stream:
            stream.return_value.__enter__.return_value = self.download()
            receipt = verify(self.candidate, "test-verifier", "test-token")
        self.assertEqual(receipt["dropbox_rev"], "test-rev")
        self.assertEqual(receipt["candidate"], self.candidate)
        self.assertNotIn("test-token", json.dumps(receipt))

    def test_rejects_missing_id_and_mismatched_hash(self):
        cases = [
            (httpx.Response(409, json={"error_summary": "path/not_found/..."}), "ID not found"),
            (self.download(content=b"x" * len(self.content)), "SHA-256 mismatch"),
        ]
        for response, error in cases:
            with self.subTest(error=error), patch("tools.verify_dropbox_asset.httpx.stream") as stream:
                stream.return_value.__enter__.return_value = response
                with self.assertRaisesRegex(ValueError, error):
                    verify(self.candidate, "test-verifier", "test-token")

    def download(self, content=None):
        metadata = {
            "id": self.candidate["dropbox_file_id"],
            "path_display": self.candidate["dropbox_path"],
            "size": self.candidate["size_bytes"],
            "rev": "test-rev",
        }
        return httpx.Response(
            200, content=self.content if content is None else content,
            headers={"Dropbox-API-Result": json.dumps(metadata)},
        )
