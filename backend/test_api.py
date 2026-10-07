import os
import tempfile
import unittest
from datetime import date, timedelta

temporary_db = tempfile.TemporaryDirectory()
os.environ["DATABASE_URL"] = f"sqlite:///{temporary_db.name}/test.db"

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from app.main import Base, DailyMetrics, Mission, SessionLocal, app, engine, seed


class ApiTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.drop_all(engine)
        seed()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_initial_status_and_idempotent_seed(self):
        seed()
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "day": 0, "level": 0,
            "youtube": {"subscribers": 0, "views": 0},
            "tiktok": {"followers": 0, "views": 0},
            "total_revenue_yen": 0,
            "mission": {"code": "MISSION 01", "title": "最初の1円を生み出せ。", "status": "active", "progress": 0},
        })
        with SessionLocal() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(DailyMetrics)), 1)
            self.assertEqual(db.scalar(select(func.count()).select_from(Mission)), 1)
            row = db.scalar(select(DailyMetrics))
            for field in ("youtube_watch_minutes", "youtube_likes", "youtube_comments"):
                self.assertEqual(getattr(row, field), 0)

    def test_latest_persisted_metrics_not_placeholders(self):
        with SessionLocal() as db:
            db.add(DailyMetrics(date=date.today() + timedelta(days=1), day=3, level=2,
                               youtube_subscribers=12, youtube_views=34, tiktok_followers=56,
                               tiktok_views=78, total_revenue_yen=100))
            db.commit()
        seed()  # Restart must preserve existing measurements.
        data = self.client.get("/api/status").json()
        self.assertEqual((data["day"], data["level"]), (3, 2))
        self.assertEqual(data["youtube"], {"subscribers": 12, "views": 34})
        self.assertEqual(data["tiktok"], {"followers": 56, "views": 78})
        self.assertEqual(data["total_revenue_yen"], 100)
        self.assertEqual(data["mission"]["progress"], 100)


if __name__ == "__main__":
    unittest.main()
