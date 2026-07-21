import os
import sys
import unittest
import json

# Ensure backend folder is in path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup test database configuration to avoid cluttering production database
from backend.database import Base, get_db
from backend.main import app

TEST_DATABASE_URL = "sqlite:///./test_harmonyrec.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override database dependency in FastAPI
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

class TestHarmonyRecBackend(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Create test database tables
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        
        # Test accounts data
        cls.user_signup = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "securepassword123"
        }
        cls.user_login = {
            "username": "testuser",
            "password": "securepassword123"
        }
        cls.survey_payload = {
            "age": 30,
            "gender": "Male",
            "mood": "Anxiety",
            "stress": 8,
            "sleep_quality": "Fair",
            "anxiety": 8,
            "fav_genre": "Lo-fi",
            "language_pref": "English",
            "activity": "Meditation"
        }
        cls.auth_token = ""

    @classmethod
    def tearDownClass(cls):
        # Drop test tables and clean up database file
        Base.metadata.drop_all(bind=engine)
        if os.path.exists("./test_harmonyrec.db"):
            try:
                os.remove("./test_harmonyrec.db")
            except PermissionError:
                pass # SQLite might keep file lock temporarily

    def test_01_signup(self):
        # Test signup endpoint
        response = self.client.post("/api/auth/signup", json=self.user_signup)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["username"], "testuser")
        self.assertEqual(data["token_type"], "bearer")

    def test_02_login(self):
        # Test login endpoint
        response = self.client.post("/api/auth/login", json=self.user_login)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["username"], "testuser")
        
        # Save token for subsequent tests
        type(self).auth_token = data["access_token"]

    def test_03_submit_survey(self):
        # Verify unauthorized block on survey submit
        response = self.client.post("/api/recommend/survey", json=self.survey_payload)
        self.assertEqual(response.status_code, 401)
        
        # Submit with proper authorization header
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = self.client.post("/api/recommend/survey", json=self.survey_payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("survey_id", data)
        self.assertIn("result_state", data)
        self.assertIn("tracks", data)
        # With high anxiety and meditation, target should classify as Nature Sounds
        self.assertEqual(data["result_state"], "Meditation Nature Sounds")
        self.assertTrue(len(data["tracks"]) > 0)

    def test_04_get_history(self):
        # Submit request to history
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = self.client.get("/api/recommend/history", headers=headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["result_state"], "Meditation Nature Sounds")
        self.assertEqual(data[0]["fav_genre"], "Lo-fi")
        self.assertEqual(data[0]["anxiety"], 8)

    def test_05_model_comparison(self):
        # Request analytics comparison details
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        response = self.client.get("/api/analytics/model-comparison", headers=headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("XGBoost", data)
        self.assertIn("Decision Tree", data)
        self.assertIsInstance(data["XGBoost"]["accuracy"], float)

    def test_06_feedback(self):
        # Submit ratings feedback
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        payload = {
            "survey_id": 1,
            "rating": 5,
            "helped": True
        }
        response = self.client.post("/api/recommend/feedback", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")

    def test_07_journal(self):
        # Submit daily mood journal entry
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        payload = {
            "mood": "Happy",
            "stress": 3,
            "journal_text": "Had a fantastic day testing endpoints!"
        }
        response = self.client.post("/api/journal", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        
        # Get journals
        response = self.client.get("/api/journal", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data) > 0)
        self.assertEqual(data[0]["mood"], "Happy")

    def test_08_chatbot(self):
        # Test AI chatbot tip retrieval
        payload = {
            "message": "I feel very stressed and anxious today",
            "current_mood": "Anxiety"
        }
        response = self.client.post("/api/chatbot", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("reply", data)
        self.assertTrue("breathing" in data["reply"].lower() or "anxiety" in data["reply"].lower() or "stress" in data["reply"].lower())

if __name__ == "__main__":
    unittest.main()
