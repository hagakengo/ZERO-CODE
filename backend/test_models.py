"""Regression checks for extracted ORM models."""
import unittest

from app import models
from app import main


class ModelImportTests(unittest.TestCase):
    def test_main_reexports_same_model_classes(self):
        for name in ("Base", "Mission", "DailyMetrics", "YouTubeIntegration"):
            self.assertIs(getattr(main, name), getattr(models, name))

    def test_expected_table_names(self):
        self.assertEqual(
            set(models.Base.metadata.tables),
            {"missions", "daily_metrics", "youtube_integration"},
        )


if __name__ == "__main__":
    unittest.main()
