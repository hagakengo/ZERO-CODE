"""Alembic safety smoke tests; never connect to a database."""
import os
from pathlib import Path
import subprocess
import sys
import unittest

BACKEND = Path(__file__).resolve().parent


class AlembicSafetyTests(unittest.TestCase):
    def run_alembic(self, *args):
        env = os.environ.copy()
        env["ZERO_CODE_SKIP_SEED"] = "1"
        env.pop("DATABASE_URL", None)
        return subprocess.run(
            [sys.executable, "-m", "alembic", "-c", "alembic.ini", *args],
            cwd=BACKEND,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=40,
        )

    def test_offline_sql_succeeds(self):
        result = self.run_alembic("upgrade", "head", "--sql")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("20261008_0001", result.stdout)

    def test_online_upgrade_is_blocked(self):
        result = self.run_alembic("upgrade", "head")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Online migrations disabled", result.stderr)


if __name__ == "__main__":
    unittest.main()
