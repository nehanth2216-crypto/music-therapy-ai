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

    def test_09_profile_and_password_features(self):
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # GET /api/auth/me
        resp = self.client.get("/api/auth/me", headers=headers)
        self.assertEqual(resp.status_code, 200)
        user_info = resp.json()
        self.assertEqual(user_info["username"], "testuser")
        self.assertEqual(user_info["email"], "testuser@example.com")
        
        # PUT /api/auth/profile
        update_payload = {
            "full_name": "Test User Pro",
            "fav_genre": "Classical",
            "default_activity": "Studying"
        }
        resp = self.client.put("/api/auth/profile", json=update_payload, headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["full_name"], "Test User Pro")
        self.assertEqual(data["fav_genre"], "Classical")
        
        # POST /api/auth/change-password
        change_pwd_payload = {
            "current_password": "securepassword123",
            "new_password": "newsecurepassword456"
        }
        resp = self.client.post("/api/auth/change-password", json=change_pwd_payload, headers=headers)
        self.assertEqual(resp.status_code, 200)
        
        # Verify login with new password
        login_resp = self.client.post("/api/auth/login", json={"username": "testuser", "password": "newsecurepassword456"})
        self.assertEqual(login_resp.status_code, 200)
        type(self).auth_token = login_resp.json()["access_token"]
        
    def test_10_forgot_and_reset_password(self):
        # Request forgot password
        resp = self.client.post("/api/auth/forgot-password", json={"email_or_username": "testuser@example.com"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("reset_token", data)
        reset_tok = data["reset_token"]
        
        # Reset password
        reset_payload = {
            "reset_token": reset_tok,
            "new_password": "resetpassword789"
        }
        resp = self.client.post("/api/auth/reset-password", json=reset_payload)
        self.assertEqual(resp.status_code, 200)
        
        # Login with reset password
        login_resp = self.client.post("/api/auth/login", json={"username": "testuser", "password": "resetpassword789"})
        self.assertEqual(login_resp.status_code, 200)
        type(self).auth_token = login_resp.json()["access_token"]

    def test_11_listening_history_and_playlists(self):
        headers = {"Authorization": f"Bearer {self.auth_token}"}

        # 1. Test Listening History Record
        history_item = {
            "title": "Weightless Lofi",
            "artist": "Lofi Dreamer",
            "duration": "3:20",
            "album_image": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=150&h=150&fit=crop",
            "play_url": "https://open.spotify.com/track/6UaR2v567dGg36329",
            "preview_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
        }
        resp = self.client.post("/api/music/history", json=history_item, headers=headers)
        self.assertEqual(resp.status_code, 200)

        # 2. Get Listening History
        resp = self.client.get("/api/music/history", headers=headers)
        self.assertEqual(resp.status_code, 200)
        records = resp.json()
        self.assertTrue(len(records) > 0)
        self.assertEqual(records[0]["title"], "Weightless Lofi")

        # 3. Create Custom Playlist
        resp = self.client.post("/api/playlists", json={"name": "My Chill Vibes", "description": "Relaxing beats"}, headers=headers)
        self.assertEqual(resp.status_code, 200)
        playlist_id = resp.json()["id"]

        # 4. Add Track to Playlist
        track_data = {
            "title": "Raindrop Lounge",
            "artist": "Cloudy Day",
            "duration": "4:10"
        }
        resp = self.client.post(f"/api/playlists/{playlist_id}/tracks", json=track_data, headers=headers)
        self.assertEqual(resp.status_code, 200)

        # 5. Get Playlist Details
        resp = self.client.get(f"/api/playlists/{playlist_id}", headers=headers)
        self.assertEqual(resp.status_code, 200)
        details = resp.json()
        self.assertEqual(details["name"], "My Chill Vibes")
        self.assertEqual(len(details["tracks"]), 1)

    def test_12_mood_timeline(self):
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        resp = self.client.get("/api/mood/history", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("timeline", data)
        self.assertTrue(len(data["timeline"]) > 0)

if __name__ == "__main__":
    unittest.main()
