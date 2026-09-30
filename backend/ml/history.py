from typing import Dict, Any, List, Set
from sqlalchemy.orm import Session
from backend.database import ListeningHistory, SurveyResponse

class HistoryManager:
    """Manages user listening history and survey assessment history (Requirement 8)."""

    def get_history_summary(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Fetch recently played tracks, artists, genres, and languages."""
        summary = {
            "recent_artists": set(),
            "recent_titles": set(),
            "recent_genres": set(),
            "recent_languages": set(),
            "recent_tracks": [],
            "last_survey": None
        }
        if not db or not user_id:
            return summary

        try:
            records = (
                db.query(ListeningHistory)
                .filter(ListeningHistory.user_id == user_id)
                .order_by(ListeningHistory.played_at.desc())
                .limit(30)
                .all()
            )
            for r in records:
                if r.artist:
                    summary["recent_artists"].add(r.artist.strip().lower())
                if r.title:
                    summary["recent_titles"].add(r.title.strip().lower())
                if r.genre:
                    summary["recent_genres"].add(r.genre.strip().lower())
                if r.language:
                    summary["recent_languages"].add(r.language.strip().lower())

                summary["recent_tracks"].append({
                    "title": r.title,
                    "artist": r.artist,
                    "genre": r.genre,
                    "energy": r.energy
                })

            last_s = (
                db.query(SurveyResponse)
                .filter(SurveyResponse.user_id == user_id)
                .order_by(SurveyResponse.timestamp.desc())
                .first()
            )
            if last_s:
                summary["last_survey"] = {
                    "mood": last_s.mood,
                    "stress": last_s.stress,
                    "anxiety": last_s.anxiety,
                    "language_pref": last_s.language_pref,
                    "fav_genre": last_s.fav_genre
                }
        except Exception as e:
            print(f"Error fetching history summary: {e}")

        return summary
