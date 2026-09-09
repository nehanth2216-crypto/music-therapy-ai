from typing import List, Dict, Any, Set
from backend.ml.language_verifier import LanguageVerifier

class RecommendationRankingEngine:
    """Recommendation Ranking Engine enforcing mandatory Language Filtering."""

    def score_track(
        self,
        track: Dict[str, Any],
        user_mood: str,
        predicted_therapy: str,
        target_activity: str,
        selected_language: str,
        selected_genre: str = "",
        favorite_artists: Set[str] = None,
        recent_artists: Set[str] = None,
        liked_titles: Set[str] = None,
        skipped_titles: Set[str] = None
    ) -> float:
        """
        Calculate total recommendation score (0.0 to 100.0).
        Strict mandatory rule: If track is NOT verified to belong to selected_language, return -1000.0 (discard).
        """
        fav_artists = favorite_artists or set()
        liked_t = liked_titles or set()
        skip_t = skipped_titles or set()

        track_title = (track.get("title") or "").strip().lower()
        track_artist = (track.get("artist") or "").strip().lower()
        
        # 1. MANDATORY LANGUAGE MATCH GATEKEEPER
        if selected_language and not LanguageVerifier.verify_track_language(track, selected_language):
            return -1000.0 # Strictly discard non-matching language tracks

        # 2. Penalty for skipped tracks
        if track_title in skip_t:
            return -100.0

        # 3. Language Match Bonus (Mandatory base 20 points)
        lang_score = 20.0

        # 4. Strict Genre Match Scoring (0 - 30 points)
        genre_score = 15.0
        t_genre = (track.get("genre") or "").strip().lower()
        sel_genre = (selected_genre or "").strip().lower()
        if sel_genre:
            if sel_genre in t_genre or t_genre in sel_genre:
                genre_score = 30.0
            elif ("instrumental" in sel_genre and any(k in t_genre or k in track_title for k in ["flute", "veena", "sitar", "piano", "guitar", "ambient", "classical", "relaxation", "instrumental"])) or \
                 ("lo-fi" in sel_genre and any(k in t_genre or k in track_title for k in ["lo-fi", "lofi", "chill", "ambient", "acoustic", "relax"])) or \
                 ("nature" in sel_genre and any(k in t_genre or k in track_title for k in ["nature", "water", "rain", "ocean", "soundscape", "birds", "bowls"])) or \
                 ("acoustic" in sel_genre and any(k in t_genre or k in track_title for k in ["acoustic", "unplugged", "guitar", "piano"])) or \
                 ("pop" in sel_genre and "pop" in t_genre):
                genre_score = 25.0
            else:
                if sel_genre in ["instrumental", "nature sounds", "lo-fi", "classical"]:
                    genre_score = -40.0
                else:
                    genre_score = 5.0

        # 5. Mood Match Score (0 - 25 points)
        mood_score = 0.0
        audio_feat = track.get("audio_features", {})
        energy = audio_feat.get("energy", 0.5)

        m_lower = (user_mood or "").lower()
        if "anxi" in m_lower or "sad" in m_lower or "tired" in m_lower or "calm" in m_lower:
            mood_score = 25.0 * (1.0 - abs(energy - 0.25))
        elif "happy" in m_lower or "energetic" in m_lower:
            mood_score = 25.0 * (1.0 - abs(energy - 0.75))
        else:
            mood_score = 15.0

        # 6. Therapy Match Score (0 - 20 points)
        therapy_score = 0.0
        t_category = (track.get("therapy_category") or "").lower()
        pred_therapy = (predicted_therapy or "").lower()
        if t_category and pred_therapy and (t_category in pred_therapy or pred_therapy in t_category):
            therapy_score = 20.0
        else:
            therapy_score = 10.0

        # 7. Activity Match Score (0 - 15 points)
        activity_score = 0.0
        act_lower = (target_activity or "").lower()
        if "sleep" in act_lower and energy <= 0.35:
            activity_score = 15.0
        elif "exercise" in act_lower or "workout" in act_lower:
            activity_score = 15.0 if energy >= 0.70 else 5.0
        elif "meditation" in act_lower:
            activity_score = 15.0 if audio_feat.get("acousticness", 0.5) >= 0.60 else 8.0
        else:
            activity_score = 10.0

        # 8. History & Popularity (0 - 10 points)
        history_score = 0.0
        if track_title in liked_t:
            history_score += 5.0
        if any(fav_a in track_artist for fav_a in fav_artists):
            history_score += 3.0
        history_score = min(7.0, history_score)

        pop = float(track.get("popularity", 50))
        pop_score = (pop / 100.0) * 3.0

        total_score = lang_score + genre_score + mood_score + therapy_score + activity_score + history_score + pop_score
        return round(total_score, 2)

    def rank_tracks(
        self,
        tracks: List[Dict[str, Any]],
        user_mood: str,
        predicted_therapy: str,
        target_activity: str,
        selected_language: str,
        selected_genre: str = "",
        favorite_artists: Set[str] = None,
        recent_artists: Set[str] = None,
        liked_titles: Set[str] = None,
        skipped_titles: Set[str] = None,
        top_n: int = 20
    ) -> List[Dict[str, Any]]:
        """Rank candidate tracks ensuring strict language and genre filtering."""
        fav_art = favorite_artists or set()
        rec_art = recent_artists or set()
        liked_t = liked_titles or set()
        skip_t = skipped_titles or set()

        scored_list = []
        seen_titles = set()

        for track in tracks:
            t_key = (track.get("title") or "").strip().lower()
            if not t_key or t_key in seen_titles:
                continue

            score = self.score_track(
                track=track,
                user_mood=user_mood,
                predicted_therapy=predicted_therapy,
                target_activity=target_activity,
                selected_language=selected_language,
                selected_genre=selected_genre,
                favorite_artists=fav_art,
                recent_artists=rec_art,
                liked_titles=liked_t,
                skipped_titles=skip_t
            )

            if score > -500.0:
                seen_titles.add(t_key)
                scored_track = dict(track)
                scored_track["recommendation_score"] = score
                scored_list.append((score, scored_track))

        scored_list.sort(key=lambda x: x[0], reverse=True)
        return [t[1] for t in scored_list[:top_n]]
