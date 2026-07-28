from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.ml.feature_engineering import FeatureEngineer
from backend.ml.predictor import TherapyPredictor
from backend.ml.spotify_service import SpotifyService
from backend.ml.ranking import RecommendationRankingEngine
from backend.ml.feedback import UserFeedbackManager
from backend.ml.history import HistoryManager

class HybridRecommender:
    """Production-Grade Hybrid Recommendation Pipeline Orchestrator."""

    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.predictor = TherapyPredictor()
        self.spotify_service = SpotifyService()
        self.ranking_engine = RecommendationRankingEngine()
        self.feedback_manager = UserFeedbackManager()
        self.history_manager = HistoryManager()

    def get_recommendations(
        self,
        survey_data: Dict[str, Any],
        user_id: Optional[int] = None,
        db: Optional[Session] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Execute Hybrid Recommendation Pipeline:
        1. User Survey & Context
        2. Feature Engineering
        3. XGBoost Therapy Category Prediction
        4. Spotify Search ('Language + Therapy + Genre')
        5. Content & Audio Feature Filtering
        6. History & Feedback Matching
        7. Recommendation Ranking Engine (Weighted scoring)
        8. Return Top 20 Songs
        """
        # 1. Gather User Feedback & Listening History Signals
        feedback_summary = self.feedback_manager.get_user_feedback_summary(user_id, db) if (user_id and db) else {}
        history_summary = self.history_manager.get_history_summary(user_id, db) if (user_id and db) else {}

        # 2. Feature Engineering Pipeline
        features = self.feature_engineer.extract_features(survey_data, history_summary)

        # 3. XGBoost Therapy Category Prediction
        therapy_category, confidence = self.predictor.predict_therapy_category(features)

        # 4. Extract Query Attributes
        selected_language = survey_data.get("language_pref", "English")
        fav_genre = survey_data.get("fav_genre", "Lo-fi")
        user_mood = survey_data.get("mood", "Tired")
        user_activity = survey_data.get("activity", "Relaxation")

        # 5. Spotify Search using 'Language + Therapy + Genre' format
        candidates = self.spotify_service.search_tracks(
            language=selected_language,
            therapy_category=therapy_category,
            genre=fav_genre,
            limit=60
        )

        # 6. Recommendation Ranking Engine
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
