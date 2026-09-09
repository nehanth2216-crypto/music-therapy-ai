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

import requests

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

def resolve_official_itunes_preview(title: str, artist: str) -> Optional[Dict[str, str]]:
    """Fetch official live iTunes preview URL and artwork for exact song matching."""
    try:
        query = f"{title} {artist}".strip()
        url = "https://itunes.apple.com/search"
        params = {"term": query, "media": "music", "entity": "song", "limit": 1}
        resp = requests.get(url, params=params, timeout=4)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                item = results[0]
                p_url = item.get("previewUrl")
                if p_url:
                    artwork = item.get("artworkUrl100", "").replace("100x100bb.jpg", "500x500bb.jpg")
                    return {
                        "preview_url": p_url,
                        "album_image": artwork or "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&h=300&fit=crop",
                        "play_url": item.get("trackViewUrl", "")
                    }
    except Exception:
        pass
    return None

def fetch_live_itunes_tracks(query: str, language: str = "English", limit: int = 30) -> List[Dict[str, Any]]:
    """Fetch live tracks from iTunes search API for maximum authentic song coverage."""
    try:
        search_term = f"{language} {query}" if language and language != "English" else query
        url = "https://itunes.apple.com/search"
        params = {"term": search_term, "media": "music", "entity": "song", "limit": limit}
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            tracks = []
            for item in results:
                preview_url = item.get("previewUrl")
                if not preview_url:
                    continue
                artwork = item.get("artworkUrl100", "").replace("100x100bb.jpg", "500x500bb.jpg")
                millis = item.get("trackTimeMillis", 0)
                minutes = millis // 60000
                seconds = (millis % 60000) // 1000
                duration_str = f"{minutes}:{seconds:02d}" if millis > 0 else "3:30"
                
                track_name = item.get("trackName", "")
                t_artist = item.get("artistName", "Unknown Artist")
                candidate = {
                    "title": track_name,
                    "artist": t_artist,
                    "album": item.get("collectionName", "Official Soundtrack"),
                    "language": language,
                    "genre": item.get("primaryGenreName", "Pop"),
                    "duration": duration_str,
                    "album_image": artwork,
                    "preview_url": preview_url,
                    "play_url": item.get("trackViewUrl"),
                    "is_search_result": True
                }
                if LanguageVerifier.verify_track_language(candidate, language):
                    tracks.append(candidate)
            return tracks
    except Exception as e:
        print(f"Error fetching live iTunes tracks in recommender: {e}")
    return []

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
        3. Pull candidate tracks from local catalog, Spotify API, and iTunes Live API
        4. Resolve live official audio preview URLs for exact original song matching
        5. Apply Recommendation Ranking Engine
        6. Return verified top-ranked tracks
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
        seed_query = (survey_data.get("query") or "").strip()

        candidates = []
        seen_keys = set()

        # 2b. If seed query provided, fetch exact original track first
        if seed_query:
            seed_tracks = fetch_live_itunes_tracks(seed_query, language=selected_language, limit=10)
            for st in seed_tracks:
                t_key = (st["title"].lower(), st["artist"].lower())
                if t_key not in seen_keys:
                    seen_keys.add(t_key)
                    candidates.append(st)

        # 3. Pull authentic verified tracks from local multilingual catalog
        if selected_language in self.catalog:
            cat_tracks = self.catalog[selected_language]
            for ct in cat_tracks:
                ct_copy = dict(ct)
                ct_copy["language"] = selected_language
                ct_copy["is_catalog_verified"] = True
                t_key = (ct_copy["title"].lower(), ct_copy["artist"].lower())
                if t_key not in seen_keys:
                    seen_keys.add(t_key)
                    candidates.append(ct_copy)

        # 4. Search Spotify with '<Language> + <Genre> + <Therapy>'
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

        # 5. Live iTunes Fallback to guarantee rich live catalog depth
        genre_search_term = f"{fav_genre} {user_mood}"
        if any(g in fav_genre.lower() for g in ["instrumental", "nature", "classical", "lo-fi", "meditation"]):
            genre_search_term = f"{fav_genre} flute sitar veena piano ambient relaxation"
            
        itunes_live = fetch_live_itunes_tracks(genre_search_term, language=selected_language, limit=30)
        for it in itunes_live:
            t_key = (it["title"].lower(), it["artist"].lower())
            if t_key not in seen_keys:
                seen_keys.add(t_key)
                candidates.append(it)

        # 6. Ensure every candidate track has an official live audio preview (fix Pixabay placeholders)
        for track in candidates:
            prev = track.get("preview_url") or ""
            if not prev or "pixabay" in prev.lower():
                official_meta = resolve_official_itunes_preview(track.get("title", ""), track.get("artist", ""))
                if official_meta:
                    track["preview_url"] = official_meta["preview_url"]
                    if official_meta.get("album_image"):
                        track["album_image"] = official_meta["album_image"]
                    if official_meta.get("play_url"):
                        track["play_url"] = official_meta["play_url"]

        # 7. Recommendation Ranking Engine
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
            selected_genre=fav_genre,
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

