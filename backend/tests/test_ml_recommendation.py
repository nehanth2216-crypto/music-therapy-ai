import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.ml.feature_engineering import FeatureEngineer
from backend.ml.predictor import TherapyPredictor
from backend.ml.spotify_service import SpotifyService
from backend.ml.ranking import RecommendationRankingEngine
from backend.ml.recommender import HybridRecommender

class TestMLRecommendationEngine(unittest.TestCase):

    def setUp(self):
        self.recommender = HybridRecommender()

    def test_feature_engineering(self):
        fe = FeatureEngineer()
        survey = {
            "age": 28,
            "mood": "Anxiety",
            "stress": 8,
            "sleep_quality": "Poor",
            "anxiety": 9,
            "activity": "Meditation",
            "fav_genre": "Lo-fi",
            "language_pref": "Telugu"
        }
        extracted = fe.extract_features(survey)
        self.assertEqual(extracted["language_pref"], "Telugu")
        self.assertEqual(len(extracted["feature_vector"]), 11)

    def test_therapy_prediction(self):
        predictor = TherapyPredictor()
        fe = FeatureEngineer()
        survey = {
            "age": 30,
            "mood": "Tired",
            "stress": 9,
            "sleep_quality": "Poor",
            "anxiety": 4,
            "activity": "Sleeping",
            "fav_genre": "Classical",
            "language_pref": "Hindi"
        }
        features = fe.extract_features(survey)
        category, conf = predictor.predict_therapy_category(features)
        self.assertIsInstance(category, str)
        self.assertGreaterEqual(conf, 0.0)

    def test_spotify_multi_language_search(self):
        spotify = SpotifyService()
        # Test Telugu query
        telugu_tracks = spotify.search_tracks(language="Telugu", therapy_category="Relaxation", genre="Lo-fi", limit=10)
        self.assertTrue(len(telugu_tracks) > 0)
        for t in telugu_tracks:
            self.assertEqual(t["language"], "Telugu")

        # Test Hindi query
        hindi_tracks = spotify.search_tracks(language="Hindi", therapy_category="Meditation", genre="Classical", limit=10)
        self.assertTrue(len(hindi_tracks) > 0)
        for t in hindi_tracks:
            self.assertEqual(t["language"], "Hindi")

    def test_ranking_engine_strict_language_filter(self):
        ranking = RecommendationRankingEngine()
        tracks = [
            {"title": "Track A", "artist": "Artist 1", "language": "Telugu", "popularity": 80},
            {"title": "Track B", "artist": "Artist 2", "language": "English", "popularity": 90}
        ]
        ranked = ranking.rank_tracks(
            tracks=tracks,
            user_mood="Anxiety",
            predicted_therapy="Anxiety Relief",
            target_activity="Meditation",
            selected_language="Telugu",
            top_n=10
        )
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0]["language"], "Telugu")

    def test_hybrid_recommender_pipeline(self):
        survey = {
            "age": 25,
            "mood": "Sad",
            "stress": 7,
            "sleep_quality": "Fair",
            "anxiety": 6,
            "activity": "Relaxation",
            "fav_genre": "Instrumental",
            "language_pref": "Tamil"
        }
        result = self.recommender.get_recommendations(survey_data=survey, limit=10)
        self.assertIn("predicted_therapy_category", result)
        self.assertEqual(result["selected_language"], "Tamil")
        self.assertTrue(len(result["tracks"]) > 0)

if __name__ == "__main__":
    unittest.main()
