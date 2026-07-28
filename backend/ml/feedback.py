from typing import Dict, Any, Set
from sqlalchemy.orm import Session
from backend.database import TrackFeedback, FavoriteTrack, ListeningHistory, User

class UserFeedbackManager:
    """Manages recording user interaction feedback (likes, skips, plays) and compiling user preference profiles."""

    def record_feedback(
        self,
        user_id: int,
        title: str,
        artist: str,
        action: str, # 'like', 'skip', 'play'
        therapy_category: str = None,
        language: str = None,
        genre: str = None,
        db: Session = None
    ) -> bool:
        """Record track-level action (like, skip, play) in database."""
        if not db or not user_id:
            return False
        try:
            entry = TrackFeedback(
                user_id=user_id,
                title=title,
                artist=artist,
                action=action,
                therapy_category=therapy_category,
                language=language,
                genre=genre
            )
            db.add(entry)
            db.commit()
            return True
        except Exception as e:
            print(f"Error recording track feedback: {e}")
            db.rollback()
            return False

    def get_user_feedback_summary(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Compile feedback signals (liked tracks, skipped tracks, favorite artists/genres/languages)."""
        summary = {
            "liked_titles": set(),
            "skipped_titles": set(),
            "favorite_artists": set(),
            "favorite_languages": set(),
            "favorite_genres": set()
        }
        if not db or not user_id:
            return summary

        try:
            # 1. Fetch from TrackFeedback table
            feedbacks = db.query(TrackFeedback).filter(TrackFeedback.user_id == user_id).all()
            for fb in feedbacks:
                t_title = (fb.title or "").strip().lower()
                t_artist = (fb.artist or "").strip().lower()
                if fb.action == "like":
                    summary["liked_titles"].add(t_title)
                    if t_artist:
                        summary["favorite_artists"].add(t_artist)
                elif fb.action == "skip":
                    summary["skipped_titles"].add(t_title)

            # 2. Fetch from FavoriteTrack table
            favs = db.query(FavoriteTrack).filter(FavoriteTrack.user_id == user_id).all()
            for f in favs:
                if f.title:
                    summary["liked_titles"].add(f.title.strip().lower())
                if f.artist:
                    summary["favorite_artists"].add(f.artist.strip().lower())

            # 3. Fetch user profile defaults
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                if user.language_pref:
                    summary["favorite_languages"].add(user.language_pref.strip().lower())
                if user.fav_genre:
                    summary["favorite_genres"].add(user.fav_genre.strip().lower())
        except Exception as e:
            print(f"Error fetching user feedback summary: {e}")

        return summary
