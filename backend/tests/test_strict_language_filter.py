import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.ml.language_verifier import LanguageVerifier
from backend.ml.recommender import HybridRecommender
from backend.ml.spotify_service import SpotifyService

class TestStrictLanguageFiltering(unittest.TestCase):

    def setUp(self):
        self.recommender = HybridRecommender()
        self.verifier = LanguageVerifier()

    def test_language_verifier_rejects_english_tracks_for_telugu(self):
        english_track = {
            "title": "Weightless",
            "artist": "Marconi Union",
            "album": "Ambient Sleep",
            "language": "English"
        }
        is_telugu = self.verifier.verify_track_language(english_track, "Telugu")
        self.assertFalse(is_telugu, "LanguageVerifier MUST reject English track 'Weightless' for Telugu query")

    def test_language_verifier_accepts_authentic_telugu_track(self):
        telugu_track = {
            "title": "Samayama",
            "artist": "Hesham Abdul Wahab, Anurag Kulkarni",
            "album": "Hi Nanna",
            "language": "Telugu"
        }
        is_telugu = self.verifier.verify_track_language(telugu_track, "Telugu")
        self.assertTrue(is_telugu, "LanguageVerifier MUST accept authentic Telugu track 'Samayama'")

    def test_recommender_pipeline_telugu_no_english_leakage(self):
        survey = {
            "age": 25,
            "mood": "Anxiety",
            "stress": 8,
            "sleep_quality": "Poor",
            "anxiety": 8,
            "activity": "Meditation",
            "fav_genre": "Lo-fi",
            "language_pref": "Telugu"
        }
        res = self.recommender.get_recommendations(survey_data=survey, limit=20)
        tracks = res.get("tracks", [])
        self.assertEqual(res["selected_language"], "Telugu")

        # Verify EVERY track returned is strictly Telugu and not English
        for t in tracks:
            title = t.get("title", "").lower()
            self.assertNotIn("weightless", title)
            self.assertNotIn("twinkle twinkle", title)
            self.assertNotIn("sunflower", title)
            self.assertEqual(t.get("language"), "Telugu")

    def test_recommender_pipeline_hindi_no_english_leakage(self):
        survey = {
            "age": 28,
            "mood": "Happy",
            "stress": 4,
            "sleep_quality": "Good",
            "anxiety": 3,
            "activity": "Relaxation",
            "fav_genre": "Pop",
            "language_pref": "Hindi"
        }
        res = self.recommender.get_recommendations(survey_data=survey, limit=20)
        tracks = res.get("tracks", [])
        self.assertEqual(res["selected_language"], "Hindi")

        for t in tracks:
            title = t.get("title", "").lower()
            self.assertNotIn("weightless", title)
            self.assertEqual(t.get("language"), "Hindi")

if __name__ == "__main__":
    unittest.main()
