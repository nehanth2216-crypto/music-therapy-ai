from typing import List, Dict, Any, Set

class RecommendationRankingEngine:
    """Recommendation Ranking Engine applying strict weightings."""

    def score_track(
        self,
        track: Dict[str, Any],
        user_mood: str,
        predicted_therapy: str,
        target_activity: str,
        selected_language: str,
        favorite_artists: Set[str],
        recent_artists: Set[str],
        liked_titles: Set[str],
        skipped_titles: Set[str]
    ) -> float:
        """
        Calculate total recommendation score (0.0 to 100.0) based on weighted rules:
        - 35% Mood Match
        - 25% Therapy Match
        - 15% Activity Match
        - 10% Language Match
        - 10% Listening History Similarity
        - 5% Popularity
        """
        track_title = (track.get("title") or "").strip().lower()
        track_artist = (track.get("artist") or "").strip().lower()
        track_lang = (track.get("language") or "").strip().lower()

        # Strict Language Filtering: If languages do not match, heavily penalize or drop score
        if selected_language and track_lang and selected_language.lower() != track_lang:
            return -100.0 # Strict filter

        # Penalty for skipped tracks
        if track_title in skipped_titles:
            return -50.0

        # 1. Mood Match Score (0 - 35 points)
        mood_score = 0.0
        audio_feat = track.get("audio_features", {})
        energy = audio_feat.get("energy", 0.5)
        valence = audio_feat.get("valence", 0.5)

        m_lower = (user_mood or "").lower()
        if "anxi" in m_lower or "sad" in m_lower or "tired" in m_lower:
            # Low energy, soothing valence is best
            mood_score = 35.0 * (1.0 - abs(energy - 0.25))
        elif "happy" in m_lower or "energetic" in m_lower:
            mood_score = 35.0 * (1.0 - abs(energy - 0.75))
        else:
            mood_score = 25.0

        # 2. Therapy Match Score (0 - 25 points)
        therapy_score = 0.0
        t_category = (track.get("therapy_category") or "").lower()
        pred_therapy = (predicted_therapy or "").lower()
        if t_category and pred_therapy and (t_category in pred_therapy or pred_therapy in t_category):
            therapy_score = 25.0
        else:
            therapy_score = 15.0

        # 3. Activity Match Score (0 - 15 points)
        activity_score = 0.0
        act_lower = (target_activity or "").lower()
        if "sleep" in act_lower and energy <= 0.35:
            activity_score = 15.0
        elif "exercise" in act_lower or "workout" in act_lower:
            activity_score = 15.0 if energy >= 0.70 else 5.0
        elif "meditation" in act_lower:
            activity_score = 15.0 if audio_feat.get("acousticness", 0.5) >= 0.60 else 8.0
        elif "study" in act_lower or "focus" in act_lower:
            activity_score = 15.0 if audio_feat.get("instrumentalness", 0.5) >= 0.50 else 9.0
        else:
            activity_score = 12.0

        # 4. Language Match Score (0 - 10 points)
        lang_score = 10.0 if track_lang == selected_language.lower() else 0.0

        # 5. Listening History & Preference Similarity (0 - 10 points)
        history_score = 0.0
        if track_title in liked_titles:
            history_score += 6.0
        if any(fav_a in track_artist for fav_a in favorite_artists):
            history_score += 4.0
        elif any(rec_a in track_artist for rec_a in recent_artists):
            history_score += 2.0
        history_score = min(10.0, history_score)

        # 6. Popularity Score (0 - 5 points)
        pop = float(track.get("popularity", 50))
        pop_score = (pop / 100.0) * 5.0

        total_score = mood_score + therapy_score + activity_score + lang_score + history_score + pop_score
        return round(total_score, 2)

    def rank_tracks(
        self,
        tracks: List[Dict[str, Any]],
        user_mood: str,
        predicted_therapy: str,
        target_activity: str,
        selected_language: str,
        favorite_artists: Set[str] = None,
        recent_artists: Set[str] = None,
        liked_titles: Set[str] = None,
        skipped_titles: Set[str] = None,
        top_n: int = 20
    ) -> List[Dict[str, Any]]:
        """Rank candidates and return top_n highest scoring tracks."""
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
                favorite_artists=fav_art,
                recent_artists=rec_art,
                liked_titles=liked_t,
                skipped_titles=skip_t
            )

            if score > 0.0: # Filter out strictly invalid language or heavily skipped tracks
                track["match_score"] = score
                scored_list.append((score, track))
                seen_titles.add(t_key)

        scored_list.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored_list[:top_n]]
