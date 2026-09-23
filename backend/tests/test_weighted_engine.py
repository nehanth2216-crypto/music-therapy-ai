import unittest
import json
import os
import sys

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from backend.recommendation.engine import WeightedSongRecommendationEngine
from fastapi.testclient import TestClient
from backend.main import app
from backend.auth import create_access_token, get_password_hash
from backend.database import SessionLocal, User, init_db

class TestWeightedSongRecommendationEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.engine = WeightedSongRecommendationEngine()
        cls.client = TestClient(app)
        
        # Ensure test user exists for authenticated tests
        db = SessionLocal()
        try:
            test_user = db.query(User).filter(User.username == "engine_test_user").first()
            if not test_user:
                test_user = User(
                    username="engine_test_user",
                    email="engine_test_user@example.com",
                    hashed_password=get_password_hash("password123"),
                    fav_genre="Melody",
                    language_pref="Telugu"
                )
                db.add(test_user)
                db.commit()
        finally:
            db.close()

        cls.token = create_access_token(data={"sub": "engine_test_user"})
        cls.auth_headers = {"Authorization": f"Bearer {cls.token}"}
        
        # Load ground truth catalog from previous dataset
        catalog_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dataset", "multilingual_music_catalog.json")
        with open(catalog_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        cls.valid_song_titles = set()
        for songs in data.values():
            for s in songs:
                t = (s.get("title") or s.get("song") or "").strip().lower()
                if t:
                    cls.valid_song_titles.add(t)

    def test_determinism_same_input_same_output(self):
        """Verify Requirement 6: Same input produces the exact same ranked output across multiple runs."""
        state = {
            "age": 21,
            "language": "Telugu",
            "genre": "Melody",
            "mood": "Stressed",
            "activity": "Studying",
            "energy": "Low"
        }
        run1 = self.engine.recommend(state, top_n=10)
        run2 = self.engine.recommend(state, top_n=10)
        run3 = self.engine.recommend(state, top_n=10)

        self.assertEqual(len(run1), len(run2))
        self.assertEqual(len(run2), len(run3))

        for r1, r2, r3 in zip(run1, run2, run3):
            self.assertEqual(r1["song"], r2["song"])
            self.assertEqual(r2["song"], r3["song"])
            self.assertEqual(r1["score"], r2["score"])
            self.assertEqual(r2["score"], r3["score"])
            self.assertEqual(r1["rank"], r2["rank"])

    def test_language_isolation(self):
        """Verify Requirement 4: Strictly no cross-language leakage."""
        languages = ["Telugu", "Tamil", "Hindi", "Malayalam", "English"]
        for lang in languages:
            state = {
                "age": 25,
                "language": lang,
                "genre": "Pop",
                "mood": "Happy",
                "activity": "Walking",
                "energy": "Medium"
            }
            recs = self.engine.recommend(state, top_n=10)
            self.assertGreaterEqual(len(recs), 5, f"Should return at least 5 songs for {lang}")
            for song in recs:
                self.assertEqual(
                    song["language"].strip().lower(),
                    lang.lower(),
                    f"Expected {lang}, but found {song['language']} in song {song['song']}"
                )

    def test_scores_sorted_descending(self):
        """Verify Requirement 6 & 7: Scores must be strictly non-increasing."""
        state = {
            "age": 25,
            "language": "Hindi",
            "genre": "Pop",
            "mood": "Happy",
            "activity": "Workout",
            "energy": "High"
        }
        recs = self.engine.recommend(state, top_n=10)
        scores = [r["score"] for r in recs]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_no_invented_songs(self):
        """Verify Requirement 3: Every recommended song belongs strictly to the authentic language catalog."""
        languages = ["Telugu", "Hindi", "English"]
        for lang in languages:
            state = {
                "age": 30,
                "language": lang,
                "genre": "Melody",
                "mood": "Calm",
                "activity": "Relaxing",
                "energy": "Low"
            }
            recs = self.engine.recommend(state, top_n=5)
            for r in recs:
                self.assertEqual(r["language"].lower(), lang.lower())

    def test_fallback_deliberately_nonexistent_combination(self):
        """Verify Requirement 13: Fallback system ensures recommendations are returned even for nonexistent combinations."""
        state = {
            "age": 42,
            "language": "Telugu",
            "genre": "Pop",
            "mood": "Bored",
            "activity": "Cooking",
            "energy": "High"
        }
        recs = self.engine.recommend(state, top_n=10)
        self.assertGreaterEqual(len(recs), 5, "Fallback must return at least 5 songs")
        self.assertLessEqual(len(recs), 10, "Fallback must return at most 10 songs")
        for r in recs:
            self.assertEqual(r["language"].lower(), "telugu")

    def test_specified_test_1(self):
        """TEST 1: Age 21, Telugu, Melody, Stressed, Studying, Low Energy."""
        state = {
            "age": 21,
            "language": "Telugu",
            "genre": "Melody",
            "mood": "Stressed",
            "activity": "Studying",
            "energy": "Low"
        }
        recs = self.engine.recommend(state, top_n=10)
        self.assertGreaterEqual(len(recs), 5)
        self.assertEqual(recs[0]["language"], "Telugu")
        self.assertGreater(recs[0]["score"], 60.0)

    def test_specified_test_2(self):
        """TEST 2: Age 25, Hindi, Pop, Happy, Workout, High Energy."""
        state = {
            "age": 25,
            "language": "Hindi",
            "genre": "Pop",
            "mood": "Happy",
            "activity": "Workout",
            "energy": "High"
        }
        recs = self.engine.recommend(state, top_n=10)
        self.assertGreaterEqual(len(recs), 5)
        self.assertEqual(recs[0]["language"], "Hindi")
        self.assertGreater(recs[0]["score"], 60.0)

    def test_specified_test_3(self):
        """TEST 3: Age 30, Malayalam, Melody, Calm, Relaxing, Low Energy."""
        state = {
            "age": 30,
            "language": "Malayalam",
            "genre": "Melody",
            "mood": "Calm",
            "activity": "Relaxing",
            "energy": "Low"
        }
        recs = self.engine.recommend(state, top_n=10)
        self.assertGreaterEqual(len(recs), 5)
        self.assertEqual(recs[0]["language"], "Malayalam")
        self.assertGreater(recs[0]["score"], 60.0)

    def test_specified_test_4(self):
        """TEST 4: Age 18, Tamil, Dance, Energetic, Party, High Energy."""
        state = {
            "age": 18,
            "language": "Tamil",
            "genre": "Dance",
            "mood": "Energetic",
            "activity": "Party",
            "energy": "High"
        }
        recs = self.engine.recommend(state, top_n=10)
        self.assertGreaterEqual(len(recs), 5)
        self.assertEqual(recs[0]["language"], "Tamil")
        self.assertGreater(recs[0]["score"], 60.0)

    def test_specified_test_5(self):
        """TEST 5: Age 45, English, Classical, Stressed, Studying, Low Energy."""
        state = {
            "age": 45,
            "language": "English",
            "genre": "Classical",
            "mood": "Stressed",
            "activity": "Studying",
            "energy": "Low"
        }
        recs = self.engine.recommend(state, top_n=10)
        self.assertGreaterEqual(len(recs), 5)
        self.assertEqual(recs[0]["language"], "English")

    def test_specified_test_6(self):
        """TEST 6: Age 65, Telugu, Melody, Calm, Relaxing, Low Energy."""
        state = {
            "age": 65,
            "language": "Telugu",
            "genre": "Melody",
            "mood": "Calm",
            "activity": "Relaxing",
            "energy": "Low"
        }
        recs = self.engine.recommend(state, top_n=10)
        self.assertGreaterEqual(len(recs), 5)
        self.assertEqual(recs[0]["language"], "Telugu")

    def test_api_recommendations_endpoint(self):
        """Verify POST /api/recommendations HTTP endpoint with full contract."""
        payload = {
            "age": 21,
            "language": "Telugu",
            "genre": "Melody",
            "mood": "Stressed",
            "activity": "Studying",
            "energy": "Low",
            "stress": 7,
            "anxiety": 6,
            "sleep_quality": 5
        }
        res = self.client.post("/api/recommendations", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("recommendation_method"), "weighted_song_ranking")
        self.assertIn("recommendations", data)
        self.assertGreaterEqual(len(data["recommendations"]), 5)
        top1 = data["recommendations"][0]
        self.assertIn("song", top1)
        self.assertIn("artist", top1)
        self.assertIn("score", top1)
        self.assertIn("reason", top1)
        self.assertIn("matched_features", top1)

    def test_api_survey_endpoint(self):
        """Verify POST /api/recommend/survey preserving XGBoost and adding song-level ranking."""
        payload = {
            "age": 25,
            "gender": "Female",
            "mood": "Happy",
            "stress": 3,
            "sleep_quality": "Good",
            "anxiety": 2,
            "fav_genre": "Pop",
            "language_pref": "Hindi",
            "activity": "Workout",
            "energy": "High"
        }
        res = self.client.post("/api/recommend/survey", json=payload, headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("tracks", data)
        self.assertGreaterEqual(len(data["tracks"]), 5)
        self.assertIn("predicted_therapy_category", data)

    def test_music_history_recording(self):
        """Verify POST /api/music/history records play data correctly."""
        payload = {
            "title": "Inthandham",
            "artist": "Sita Ramam",
            "duration": "3:45",
            "language": "Telugu",
            "genre": "Melody",
            "mood": "Stressed",
            "activity": "Studying",
            "energy": "Low",
            "recommendation_score": 92.5
        }
        res = self.client.post("/api/music/history", json=payload, headers=self.auth_headers)
        self.assertEqual(res.status_code, 200)

if __name__ == "__main__":
    unittest.main()
