"""
CivicAI Bangladesh - Automated QA & Test Suite
Covers AI Model Pipeline, Auth, Guest Submission, Anti-Spam Honeypots,
Tracking, Feed, and Administrative Verification.
"""

import sys
import os
import unittest
from fastapi.testclient import TestClient

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from backend.main import app
from ai.pipeline import ComplaintIntelligenceEngine

class CivicAITestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.ai_engine = ComplaintIntelligenceEngine.get_instance()

    def test_01_health_check(self):
        """Verify API health check endpoint returns 200 and operational status."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["ai_engine"], "operational")

    def test_02_ai_multilingual_inference(self):
        """Test AI model inference across Bangla, English, and Banglish."""
        # Bangla
        res_bn = self.ai_engine.analyze_complaint(
            "মিরপুর ১০ নম্বরে প্রধান সড়কে কালভার্ট ধসে পড়েছে",
            "জরুরি ভিত্তিতে মেরামত প্রয়োজন, প্রতিদিন যানবাহন উল্টে মারাত্মক দুর্ঘটনা ঘটছে।"
        )
        self.assertEqual(res_bn["category"], "Infrastructure")
        self.assertEqual(res_bn["severity"], "Critical")
        self.assertGreater(res_bn["priority_score"], 60.0)

        # English
        res_en = self.ai_engine.analyze_complaint(
            "Live 11kV high voltage wire snapped on road",
            "Dangerous live wire dangling over water, imminent hazard of electrocution."
        )
        self.assertEqual(res_en["category"], "Electricity & Power")
        self.assertEqual(res_en["severity"], "Critical")

        # Banglish
        res_bnen = self.ai_engine.analyze_complaint(
            "Dhanmondi road 27 e rasta bhenge boro gorto hoye ache",
            "Daily accident hocche, gari cholte parche na, repair dorkar."
        )
        self.assertEqual(res_bnen["category"], "Infrastructure")

    def test_03_guest_submission_and_tracking(self):
        """Verify guest can submit complaint without login and track using tracking ID."""
        payload = {
            "title": "বৃষ্টির পানিতে ড্রেন উপচে পুরো রাস্তা ডুবে গেছে",
            "description": "ড্রেনেজ লাইন সম্পূর্ণ বন্ধ হয়ে রাস্তা ও মানুষের বাড়িঘরে পানি ঢুকে গেছে। অবিলম্বে পরিষ্কার করা প্রয়োজন।",
            "division": "Dhaka",
            "district": "Dhaka",
            "upazila": "Mirpur",
            "area_name": "Block D, Section 11",
            "latitude": 23.8150,
            "longitude": 90.3650,
            "website_url_hp": ""  # Clean honeypot
        }
        res = self.client.post("/api/complaints/guest", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertTrue("tracking_id" in data)
        self.assertTrue("access_pin" in data)

        tracking_id = data["tracking_id"]

        # Track the newly submitted complaint
        track_res = self.client.get(f"/api/complaints/track/{tracking_id}")
        self.assertEqual(track_res.status_code, 200)
        track_data = track_res.json()
        self.assertEqual(track_data["tracking_id"], tracking_id)
        self.assertTrue(len(track_data["timeline"]) >= 2)

    def test_04_honeypot_bot_rejection(self):
        """Verify automated spam bots triggering honeypot field are blocked with 400 Bad Request."""
        payload = {
            "title": "Spam bot advertising cheap medicines online",
            "description": "Buy products at our website cheap prices fast delivery.",
            "division": "Dhaka",
            "district": "Dhaka",
            "upazila": "Gulshan",
            "website_url_hp": "http://spam-link-filled-by-bot.com"  # Trapped honeypot
        }
        res = self.client.post("/api/complaints/guest", json=payload)
        self.assertEqual(res.status_code, 400)

    def test_05_admin_login_and_stats(self):
        """Verify administrator can log in and view executive KPI analytics."""
        login_res = self.client.post("/api/auth/login", json={
            "email": "admin@civicai.gov.bd",
            "password": "Admin@CivicAI2026!"
        })
        self.assertEqual(login_res.status_code, 200)
        token = login_res.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        stats_res = self.client.get("/api/admin/stats", headers=headers)
        self.assertEqual(stats_res.status_code, 200)
        stats = stats_res.json()
        self.assertGreater(stats["total_complaints"], 0)
        self.assertTrue("category_distribution" in stats)

    def test_06_complaint_upvoting(self):
        """Verify citizen upvote toggles and increments vote count with IP tracking."""
        import uuid
        feed_res = self.client.get("/api/complaints/feed?limit=1")
        self.assertEqual(feed_res.status_code, 200)
        feed = feed_res.json()
        self.assertTrue(len(feed) > 0)
        comp_id = feed[0]["id"]
        initial_upvotes = feed[0]["upvotes_count"]

        # Use unique client IP to ensure predictable toggle
        unique_ip = f"10.0.{uuid.uuid4().hex[:4]}.1"
        headers = {"X-Forwarded-For": unique_ip}

        # 1. First upvote (should increment)
        up_res1 = self.client.post(f"/api/complaints/{comp_id}/upvote", headers=headers)
        self.assertEqual(up_res1.status_code, 200)
        up_data1 = up_res1.json()
        self.assertTrue(up_data1["has_upvoted"])
        self.assertEqual(up_data1["upvotes_count"], initial_upvotes + 1)

        # 2. Second upvote from same IP (should toggle off)
        up_res2 = self.client.post(f"/api/complaints/{comp_id}/upvote", headers=headers)
        self.assertEqual(up_res2.status_code, 200)
        up_data2 = up_res2.json()
        self.assertFalse(up_data2["has_upvoted"])
        self.assertEqual(up_data2["upvotes_count"], initial_upvotes)

if __name__ == "__main__":
    unittest.main()
