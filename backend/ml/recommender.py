import os
import json
import time
import requests
from typing import Dict, Any, List, Optional
from urllib.parse import quote_plus
from sqlalchemy.orm import Session

from backend.ml.feature_engineering import FeatureEngineer
from backend.ml.predictor import TherapyPredictor
from backend.ml.spotify_service import SpotifyService
from backend.ml.ranking import RecommendationRankingEngine
from backend.ml.feedback import UserFeedbackManager
from backend.ml.history import HistoryManager
from backend.ml.language_verifier import LanguageVerifier

CATALOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dataset", "multilingual_music_catalog.json")

# In-memory preview cache to avoid redundant network calls (Requirement 13)
_preview_cache: Dict[str, Dict[str, str]] = {}

def load_multilingual_catalog() -> Dict[str, List[Dict[str, Any]]]:
    """Load authentic local multilingual music catalog across all 18 languages."""
    if os.path.exists(CATALOG_PATH):
        try:
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Note reading multilingual catalog: {e}")
    return {}

def resolve_official_itunes_preview(title: str, artist: str) -> Optional[Dict[str, str]]:
    """Fetch official live iTunes preview URL and artwork with memory caching."""
    q_key = f"{title.lower()}::{artist.lower()}".strip()
    if q_key in _preview_cache:
        return _preview_cache[q_key]

    try:
        query = f"{title} {artist}".strip()
        url = "https://itunes.apple.com/search"
        params = {"term": query, "media": "music", "entity": "song", "limit": 1}
        resp = requests.get(url, params=params, timeout=3)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                item = results[0]
                p_url = item.get("previewUrl")
                if p_url:
                    artwork = item.get("artworkUrl100", "").replace("100x100bb.jpg", "500x500bb.jpg")
                    meta = {
                        "preview_url": p_url,
                        "album_image": artwork or "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&h=300&fit=crop",
                        "play_url": item.get("trackViewUrl", "")
                    }
                    _preview_cache[q_key] = meta
                    return meta
    except Exception:
        pass
    return None

class HybridRecommender:
    """
    Production-Level Hybrid Recommendation System (Requirement 9).
    Pipeline:
    1. User Survey
    2. Feature Engineering Pipeline
    3. XGBoost Primary Model Prediction
    4. Therapy Category Prediction
    5. Spotify & Multi-Source Search (Language + Therapy + Genre)
    6. Content-Based Audio Features Filtering
    7. Listening History & Feedback Matching
    8. 6-Factor Recommendation Ranking Engine
    9. Top 20 Therapeutic Songs
    10. Save User Feedback & Survey Assessment
    """

    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.predictor = TherapyPredictor(default_model="XGBoost")
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
        Execute the Complete 10-Step Production Recommendation Pipeline.
        """
        # Step 1: User Survey & Interaction Context Gathering
        feedback_summary = self.feedback_manager.get_user_feedback_summary(user_id, db) if (user_id and db) else {}
        history_summary = self.history_manager.get_history_summary(user_id, db) if (user_id and db) else {}

        selected_language = (survey_data.get("language_pref") or survey_data.get("language") or "English").strip().title()
        fav_genre = (survey_data.get("fav_genre") or survey_data.get("genre") or "").strip()
        user_mood = (survey_data.get("mood") or "Calm").strip()
        user_activity = (survey_data.get("activity") or "Relaxation").strip()
        seed_query = (survey_data.get("query") or "").strip()

        # Step 2: Feature Engineering Pipeline (Requirement 3)
        features = self.feature_engineer.extract_features(survey_data, history_summary)
        target_audio = features.get("target_audio_features", {})

        # Step 3 & 4: XGBoost Prediction for Therapy Category (Requirement 1 & 2)
        # Default model is strictly XGBoost unless another model is explicitly selected in Model Comparison
        selected_model = survey_data.get("model_name") or "XGBoost"
        therapy_category, confidence = self.predictor.predict_therapy_category(features, model_name=selected_model)

        # Refresh catalog to ensure all 18 languages are present
        if not self.catalog:
            self.catalog = load_multilingual_catalog()

        candidates: List[Dict[str, Any]] = []
        seen_keys = set()

        # Step 5: Multi-Source Search (Language + Therapy + Genre) (Requirement 4 & 5)
        # 5a. Authentic Local Catalog tracks for selected_language
        if selected_language in self.catalog:
            u_m_low = user_mood.lower()
            t_cat_low = therapy_category.lower()

            def mood_sort_priority(track_item):
                tm = str(track_item.get("mood") or "").lower()
                tc = str(track_item.get("therapy_category") or "").lower()
                if tm == u_m_low:
                    return 0
                if any(k in u_m_low for k in ["sleep", "relax"]) and any(k in tm for k in ["sleep", "relax"]):
                    return 1
                if any(k in u_m_low for k in ["anxi", "stress"]) and any(k in tm for k in ["anxi", "stress"]):
                    return 1
                if any(k in u_m_low for k in ["motivat", "dheera"]) and any(k in tm for k in ["motivat", "energet"]):
                    return 1
                if any(k in u_m_low for k in ["romant", "love"]) and any(k in tm for k in ["romant", "love"]):
                    return 1
                if any(k in u_m_low for k in ["sad", "depress"]) and any(k in tm for k in ["sad", "emotional"]):
                    return 1
                if any(k in u_m_low for k in ["calm", "peace"]) and any(k in tm for k in ["calm", "peace", "relax"]):
                    return 1
                if any(k in u_m_low for k in ["happ", "joy"]) and any(k in tm for k in ["happ", "joy"]):
                    return 1
                if tc == t_cat_low:
                    return 2
                return 3

            sorted_catalog = sorted(self.catalog[selected_language], key=mood_sort_priority)
            for ct in sorted_catalog:
                ct_copy = dict(ct)
                ct_copy["language"] = selected_language
                ct_copy["is_catalog_verified"] = True
                t_key = (ct_copy["title"].lower().strip(), ct_copy["artist"].lower().strip())
                if t_key not in seen_keys:
                    seen_keys.add(t_key)
                    candidates.append(ct_copy)

        # 5b. Spotify Search using structured 'Language + Therapy + Genre' queries
        sp_tracks = self.spotify_service.search_tracks(
            language=selected_language,
            therapy_category=therapy_category,
            genre=fav_genre,
            limit=30
        )
        for st in sp_tracks:
            if LanguageVerifier.verify_track_language(st, selected_language):
                t_key = (st["title"].lower().strip(), st["artist"].lower().strip())
                if t_key not in seen_keys:
                    seen_keys.add(t_key)
                    candidates.append(st)

        # 5c. Seed Query if provided by user (direct song/artist search)
        if seed_query:
            direct_search = self.spotify_service.search_tracks(
                language=selected_language,
                therapy_category=seed_query,
                genre=fav_genre,
                limit=15
            )
            for dt in direct_search:
                t_key = (dt["title"].lower().strip(), dt["artist"].lower().strip())
                if t_key not in seen_keys and LanguageVerifier.verify_track_language(dt, selected_language):
                    seen_keys.add(t_key)
                    candidates.insert(0, dt) # Boost direct seed query match

        # Step 6 & 7: Content-Based Filtering & Listening History Matching
        favorite_artists = set(feedback_summary.get("favorite_artists", set())).union(history_summary.get("recent_artists", set()))
        recent_artists = set(history_summary.get("recent_artists", set()))
        liked_titles = set(feedback_summary.get("liked_titles", set()))
        skipped_titles = set(feedback_summary.get("skipped_titles", set()))

        # Step 8: Recommendation Ranking Engine (Requirement 7)
        # 35% Mood + 25% Therapy + 15% Activity + 10% Language + 10% History + 5% Popularity
        ranked_tracks = self.ranking_engine.rank_tracks(
            tracks=candidates,
            user_mood=user_mood,
            predicted_therapy=therapy_category,
            target_activity=user_activity,
            selected_language=selected_language,
            selected_genre=fav_genre,
            favorite_artists=favorite_artists,
            recent_artists=recent_artists,
            liked_titles=liked_titles,
            skipped_titles=skipped_titles,
            target_audio_features=target_audio,
            top_n=limit
        )

        # Step 9: Top 20 Songs - Ensure valid audio preview and strict language gatekeeper
        final_tracks: List[Dict[str, Any]] = []
        for track in ranked_tracks:
            # Strict language gatekeeper
            if not LanguageVerifier.verify_track_language(track, selected_language):
                continue
            if track.get("language", "").strip().lower() != selected_language.lower():
                continue

            # Ensure valid playable preview URL
            prev = track.get("preview_url") or ""
            if not prev or "pixabay" in prev.lower():
                meta = resolve_official_itunes_preview(track.get("title", ""), track.get("artist", ""))
                if meta:
                    track["preview_url"] = meta["preview_url"]
                    if meta.get("album_image"):
                        track["album_image"] = meta["album_image"]
                        track["cover_image"] = meta["album_image"]
                    if meta.get("play_url"):
                        track["play_url"] = meta["play_url"]
                        track["spotify_url"] = meta["play_url"]

            final_tracks.append(track)
            if len(final_tracks) >= limit:
                break

        # Fallback guarantee: if candidates were insufficient, pull from verified catalog for this language
        if len(final_tracks) < 5 and selected_language in self.catalog:
            existing_keys = {(t["title"].lower(), t["artist"].lower()) for t in final_tracks}
            for cat_t in self.catalog[selected_language]:
                t_k = (cat_t["title"].lower(), cat_t["artist"].lower())
                if t_k not in existing_keys:
                    existing_keys.add(t_k)
                    c_copy = dict(cat_t)
                    c_copy["language"] = selected_language
                    c_copy["recommendation_score"] = 85.0
                    c_copy["score"] = 85.0
                    c_copy["match_score"] = 85.0
                    c_copy["rank"] = len(final_tracks) + 1
                    c_copy["matched_features"] = [f"✓ {selected_language}", f"✓ {therapy_category}", "✓ Curated Therapeutic Sound"]
                    c_copy["reason"] = f"Curated therapeutic soundscape for {selected_language} music therapy and {therapy_category}."
                    final_tracks.append(c_copy)
                    if len(final_tracks) >= limit:
                        break

        # Step 10: Package and Return Result
        return {
            "predicted_therapy_category": therapy_category,
            "prediction_confidence": confidence,
            "model_used": selected_model,
            "selected_language": selected_language,
            "fav_genre": fav_genre,
            "target_audio_features": target_audio,
            "tracks": final_tracks
        }

hybrid_recommender = HybridRecommender()

