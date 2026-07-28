import os
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.ml.feature_engineering import FeatureEngineer
from backend.ml.predictor import TherapyPredictor
from backend.ml.spotify_service import SpotifyService
from backend.ml.ranking import RecommendationRankingEngine
from backend.ml.feedback import UserFeedbackManager
from backend.ml.history import HistoryManager
from backend.ml.language_verifier import LanguageVerifier

CATALOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dataset", "multilingual_music_catalog.json")

def load_multilingual_catalog() -> Dict[str, List[Dict[str, Any]]]:
    """Load authentic local multilingual music catalog."""
    if os.path.exists(CATALOG_PATH):
        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading multilingual catalog: {e}")
    return {}

class HybridRecommender:
    """Production-Grade Hybrid Recommendation Engine with Strict Authentic Language Filtering."""

    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.predictor = TherapyPredictor()
        self.spotify_service = SpotifyService()
        self.ranking_engine = RecommendationRankingEngine()
        self.feedback_manager = UserFeedbackManager()
        self.history_manager = HistoryManager()
        self.catalog = load_multilingual_catalog()

    def get_recommendations(
        self,
        survey_data: Dict[str, Any],
        user_id: Optional[int] = None,
        db: Optional[Session] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Strict Authentic Hybrid Recommendation Pipeline:
        1. Extract User Metrics & History
        2. XGBoost Therapy Category Prediction
        3. Retrieve Verified Native Songs from Local Multilingual Catalog matching selected language
        4. Query Spotify Search API using '<Language> + <Genre> + <Therapy>' and verify language
        5. Filter out non-matching language tracks (Zero English fallback for non-English queries)
        6. Apply Recommendation Ranking Engine
        7. Return verified top-ranked tracks
        """
        # 1. Gather Context & History
        feedback_summary = self.feedback_manager.get_user_feedback_summary(user_id, db) if (user_id and db) else {}
        history_summary = self.history_manager.get_history_summary(user_id, db) if (user_id and db) else {}

        # 2. Feature Engineering & XGBoost Therapy Category Prediction
        features = self.feature_engineer.extract_features(survey_data, history_summary)
        therapy_category, confidence = self.predictor.predict_therapy_category(features)

        selected_language = (survey_data.get("language_pref") or "English").strip()
        fav_genre = (survey_data.get("fav_genre") or "Lo-fi").strip()
        user_mood = (survey_data.get("mood") or "Tired").strip()
        user_activity = (survey_data.get("activity") or "Relaxation").strip()

        candidates = []
        seen_keys = set()

        # 3. Pull authentic verified tracks from local multilingual catalog
        if selected_language in self.catalog:
            cat_tracks = self.catalog[selected_language]
            for ct in cat_tracks:
                # Ensure local catalog tracks match selected language verified check
                if LanguageVerifier.verify_track_language(ct, selected_language):
                    t_key = (ct["title"].lower(), ct["artist"].lower())
                    if t_key not in seen_keys:
                        seen_keys.add(t_key)
                        ct_copy = dict(ct)
                        ct_copy["language"] = selected_language
                        candidates.append(ct_copy)

        # 4. Search Spotify with '<Language> + <Genre> + <Therapy>' & verify language
        sp_tracks = self.spotify_service.search_tracks(
            language=selected_language,
            therapy_category=therapy_category,
            genre=fav_genre,
            limit=40
        )
        for st in sp_tracks:
            if LanguageVerifier.verify_track_language(st, selected_language):
                t_key = (st["title"].lower(), st["artist"].lower())
                if t_key not in seen_keys:
                    seen_keys.add(t_key)
                    candidates.append(st)

        # 5. Recommendation Ranking Engine
        favorite_artists = feedback_summary.get("favorite_artists", set()).union(history_summary.get("recent_artists", set()))
        recent_artists = history_summary.get("recent_artists", set())
        liked_titles = feedback_summary.get("liked_titles", set())
        skipped_titles = feedback_summary.get("skipped_titles", set())

        ranked_tracks = self.ranking_engine.rank_tracks(
            tracks=candidates,
            user_mood=user_mood,
            predicted_therapy=therapy_category,
            target_activity=user_activity,
            selected_language=selected_language,
            favorite_artists=favorite_artists,
            recent_artists=recent_artists,
            liked_titles=liked_titles,
            skipped_titles=skipped_titles,
            top_n=limit
        )

        return {
            "predicted_therapy_category": therapy_category,
            "prediction_confidence": confidence,
            "selected_language": selected_language,
            "fav_genre": fav_genre,
            "tracks": ranked_tracks
        }
