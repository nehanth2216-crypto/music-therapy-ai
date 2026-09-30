from typing import List, Dict, Any, Set, Optional
from urllib.parse import quote_plus
from backend.ml.language_verifier import LanguageVerifier
from backend.ml.feature_engineering import get_target_audio_features

# Compatible Therapy Category Cross-Matrix (for therapeutic synergy)
COMPATIBLE_THERAPY_CATEGORIES = {
    "Sleep Therapy": {"Sleep Therapy": 1.0, "Relaxation": 0.90, "Meditation": 0.85, "Stress Relief": 0.75, "Anxiety Relief": 0.70},
    "Anxiety Relief": {"Anxiety Relief": 1.0, "Stress Relief": 0.90, "Meditation": 0.85, "Relaxation": 0.80, "Emotional Healing": 0.75},
    "Stress Relief": {"Stress Relief": 1.0, "Anxiety Relief": 0.90, "Relaxation": 0.85, "Meditation": 0.80, "Focus": 0.70},
    "Meditation": {"Meditation": 1.0, "Relaxation": 0.85, "Sleep Therapy": 0.80, "Stress Relief": 0.75, "Anxiety Relief": 0.75},
    "Relaxation": {"Relaxation": 1.0, "Meditation": 0.85, "Sleep Therapy": 0.80, "Stress Relief": 0.80, "Emotional Healing": 0.75},
    "Focus": {"Focus": 1.0, "Motivation": 0.80, "Relaxation": 0.75, "Stress Relief": 0.70},
    "Motivation": {"Motivation": 1.0, "Workout": 0.90, "Happiness": 0.85, "Focus": 0.80},
    "Workout": {"Workout": 1.0, "Motivation": 0.90, "Happiness": 0.80},
    "Emotional Healing": {"Emotional Healing": 1.0, "Anxiety Relief": 0.85, "Stress Relief": 0.80, "Relaxation": 0.75, "Happiness": 0.70},
    "Happiness": {"Happiness": 1.0, "Motivation": 0.85, "Workout": 0.75, "Relaxation": 0.70}
}

class RecommendationRankingEngine:
    """
    Production-Grade Recommendation Ranking Engine (Requirement 7).
    Calculates recommendation score using exact clinical weights:
    - 35% Mood Match
    - 25% Therapy Match
    - 15% Activity Match
    - 10% Language Match
    - 10% Listening History Similarity
    - 5% Popularity
    Total = 100.0%
    """

    def score_track(
        self,
        track: Dict[str, Any],
        user_mood: str,
        predicted_therapy: str,
        target_activity: str,
        selected_language: str,
        selected_genre: str = "",
        favorite_artists: Optional[Set[str]] = None,
        recent_artists: Optional[Set[str]] = None,
        liked_titles: Optional[Set[str]] = None,
        skipped_titles: Optional[Set[str]] = None,
        target_audio_features: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Calculate individual component scores and total recommendation score (0.0 to 100.0).
        Strict Gatekeeper: If track does NOT belong to selected_language, return total_score = -1000.0.
        """
        fav_artists = {a.lower().strip() for a in (favorite_artists or set())}
        rec_artists = {a.lower().strip() for a in (recent_artists or set())}
        liked_t = {t.lower().strip() for t in (liked_titles or set())}
        skip_t = {t.lower().strip() for t in (skipped_titles or set())}

        track_title = str(track.get("title") or track.get("song") or "").strip().lower()
        track_artist = str(track.get("artist") or track.get("artist_or_source") or "").strip().lower()
        track_genre = str(track.get("genre") or "").strip().lower()
        sel_genre = str(selected_genre or "").strip().lower()

        # -------------------------------------------------------------------------
        # 1. MANDATORY LANGUAGE MATCH GATEKEEPER (10% WEIGHT)
        # -------------------------------------------------------------------------
        if selected_language and not LanguageVerifier.verify_track_language(track, selected_language):
            return {"total_score": -1000.0}

        # Penalty / Exclusion for skipped songs (Requirement 8)
        if track_title in skip_t:
            return {"total_score": -100.0}

        lang_score = 10.0 # 100% of 10% Language Match

        # Extract track audio features
        audio_feat = track.get("audio_features") or {}
        t_energy = float(audio_feat.get("energy", 0.50))
        t_valence = float(audio_feat.get("valence", 0.50))
        t_danceability = float(audio_feat.get("danceability", 0.45))
        t_acousticness = float(audio_feat.get("acousticness", 0.50))
        t_instrumentalness = float(audio_feat.get("instrumentalness", 0.40))

        # Target audio profile derived from mental health state
        targets = target_audio_features or {
            "energy": 0.45, "valence": 0.50, "danceability": 0.45,
            "acousticness": 0.55, "instrumentalness": 0.45
        }
        target_energy = targets.get("energy", 0.45)
        target_valence = targets.get("valence", 0.50)
        target_acousticness = targets.get("acousticness", 0.55)

        # -------------------------------------------------------------------------
        # 2. MOOD MATCH (35% WEIGHT)
        # -------------------------------------------------------------------------
        # Measure acoustic distance between song and target mental health state
        energy_dist = abs(t_energy - target_energy)
        valence_dist = abs(t_valence - target_valence)
        acoustic_dist = abs(t_acousticness - target_acousticness)

        # Normalized audio compatibility (0.0 to 1.0)
        audio_similarity = max(0.0, 1.0 - (0.45 * energy_dist + 0.35 * valence_dist + 0.20 * acoustic_dist))
        
        # Direct semantic mood alignment (e.g. Happy -> Happy, Calm -> Calm, Romantic -> Romantic)
        t_mood = str(track.get("mood") or "").strip().lower()
        u_mood = str(user_mood or "").strip().lower()
        semantic_mood_match = 0.70

        if t_mood and u_mood:
            if t_mood == u_mood:
                semantic_mood_match = 1.0
            elif any(k in u_mood for k in ["anxi", "stress"]) and any(k in t_mood for k in ["anxi", "stress"]):
                semantic_mood_match = 1.0
            elif any(k in u_mood for k in ["sleep", "relax", "tired"]) and any(k in t_mood for k in ["sleep", "relax", "tired"]):
                semantic_mood_match = 1.0
            elif any(k in u_mood for k in ["calm", "peace"]) and any(k in t_mood for k in ["calm", "peace", "relax"]):
                semantic_mood_match = 1.0
            elif any(k in u_mood for k in ["happ", "joy"]) and any(k in t_mood for k in ["happ", "joy"]):
                semantic_mood_match = 1.0
            elif any(k in u_mood for k in ["romant", "love"]) and any(k in t_mood for k in ["romant", "love"]):
                semantic_mood_match = 1.0
            elif any(k in u_mood for k in ["sad", "depress", "grief"]) and any(k in t_mood for k in ["sad", "depress", "emotional"]):
                semantic_mood_match = 1.0
            elif any(k in u_mood for k in ["energet", "dance", "party"]) and any(k in t_mood for k in ["energet", "dance", "workout"]):
                semantic_mood_match = 1.0
            elif any(k in u_mood for k in ["motivat", "dheera", "inspire", "power"]) and any(k in t_mood for k in ["motivat", "dheera", "energet"]):
                semantic_mood_match = 1.0

        # Weighted combination of audio feature similarity and semantic mood match
        if semantic_mood_match >= 0.99:
            combined_affinity = 0.30 * audio_similarity + 0.70 * semantic_mood_match
        else:
            combined_affinity = 0.60 * audio_similarity + 0.40 * semantic_mood_match

        # Genre stylistic harmony bonus
        genre_bonus = 1.0
        if sel_genre:
            if sel_genre in track_genre or track_genre in sel_genre:
                genre_bonus = 1.05
            elif any(g in sel_genre for g in ["lo-fi", "instrumental", "classical", "acoustic"]) and \
                 any(g in track_genre for g in ["lo-fi", "instrumental", "classical", "acoustic"]):
                genre_bonus = 1.02

        # Curated catalog resonance bonus
        curation_bonus = 1.08 if (track.get("is_catalog_verified") and semantic_mood_match >= 0.99) else 1.0

        mood_score = min(35.0, max(0.0, combined_affinity * 35.0 * genre_bonus * curation_bonus))

        # -------------------------------------------------------------------------
        # 3. THERAPY MATCH (25% WEIGHT)
        # -------------------------------------------------------------------------
        t_category = str(track.get("therapy_category") or "").strip()
        pred_therapy = str(predicted_therapy or "Relaxation").strip()

        if t_category.lower() == pred_therapy.lower():
            therapy_affinity = 1.0
        elif pred_therapy in COMPATIBLE_THERAPY_CATEGORIES:
            therapy_affinity = COMPATIBLE_THERAPY_CATEGORIES[pred_therapy].get(t_category, 0.60)
        else:
            therapy_affinity = 0.65

        therapy_score = min(25.0, round(therapy_affinity * 25.0, 2))

        # -------------------------------------------------------------------------
        # 4. ACTIVITY MATCH (15% WEIGHT)
        # -------------------------------------------------------------------------
        act_lower = str(target_activity or "Relaxation").lower()
        activity_affinity = 0.70

        if any(k in act_lower for k in ["exercise", "workout", "gym", "running"]):
            # Exercise: High Energy, High Tempo, High Danceability
            activity_affinity = 0.50 * t_energy + 0.50 * t_danceability
        elif any(k in act_lower for k in ["study", "work", "focus"]):
            # Study: Instrumental, Medium Energy, Low Speechiness
            activity_affinity = 0.60 * t_instrumentalness + 0.40 * (1.0 - abs(t_energy - 0.45))
        elif any(k in act_lower for k in ["sleep", "bed", "rest"]):
            # Sleep: Very Low Energy, Slow Tempo, High Acousticness
            activity_affinity = 0.55 * (1.0 - t_energy) + 0.45 * t_acousticness
        elif "meditat" in act_lower:
            # Meditation: Highest acousticness & instrumentalness
            activity_affinity = 0.50 * t_acousticness + 0.50 * t_instrumentalness
        else:
            # General: dynamically match with clinical target energy and acousticness
            activity_affinity = 0.50 * (1.0 - abs(t_energy - target_energy)) + 0.50 * (1.0 - abs(t_acousticness - target_acousticness))

        activity_score = min(15.0, max(0.0, round(activity_affinity * 15.0, 2)))

        # -------------------------------------------------------------------------
        # 5. LISTENING HISTORY SIMILARITY (10% WEIGHT) (Requirement 8)
        # -------------------------------------------------------------------------
        history_points = 0.0

        # Liked song match (+4.0 pts)
        if track_title in liked_t:
            history_points += 4.0

        # Favorite or recent artist match (+4.0 pts)
        all_user_artists = fav_artists.union(rec_artists)
        if any(ua in track_artist for ua in all_user_artists):
            history_points += 4.0

        # Preferred genre match (+2.0 pts)
        if sel_genre and (sel_genre in track_genre or track_genre in sel_genre):
            history_points += 2.0

        history_score = min(10.0, max(0.0, round(history_points, 2)))

        # -------------------------------------------------------------------------
        # 6. POPULARITY (5% WEIGHT)
        # -------------------------------------------------------------------------
        try:
            pop_val = float(track.get("popularity", 50))
        except (ValueError, TypeError):
            pop_val = 50.0

        pop_score = min(5.0, max(0.0, round((pop_val / 100.0) * 5.0, 2)))

        # -------------------------------------------------------------------------
        # TOTAL SCORE (0.0 to 100.0%)
        # -------------------------------------------------------------------------
        total_score = round(mood_score + therapy_score + activity_score + lang_score + history_score + pop_score, 1)
        total_score = min(100.0, max(0.0, total_score))

        return {
            "mood_match": round(mood_score, 1),
            "therapy_match": round(therapy_score, 1),
            "activity_match": round(activity_score, 1),
            "language_match": round(lang_score, 1),
            "history_similarity": round(history_score, 1),
            "popularity": round(pop_score, 1),
            "total_score": total_score
        }

    def rank_tracks(
        self,
        tracks: List[Dict[str, Any]],
        user_mood: str,
        predicted_therapy: str,
        target_activity: str,
        selected_language: str,
        selected_genre: str = "",
        favorite_artists: Optional[Set[str]] = None,
        recent_artists: Optional[Set[str]] = None,
        liked_titles: Optional[Set[str]] = None,
        skipped_titles: Optional[Set[str]] = None,
        target_audio_features: Optional[Dict[str, float]] = None,
        top_n: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Rank candidate tracks using the 6-factor formula and return Top-N highest ranked songs.
        """
        fav_art = favorite_artists or set()
        rec_art = recent_artists or set()
        liked_t = liked_titles or set()
        skip_t = skipped_titles or set()

        scored_candidates = []
        seen_keys = set()

        for track in tracks:
            title = str(track.get("title") or track.get("song") or "").strip()
            artist = str(track.get("artist") or track.get("artist_or_source") or "HarmonyRec").strip()
            t_key = (title.lower(), artist.lower())

            if not title or t_key in seen_keys:
                continue

            scores = self.score_track(
                track=track,
                user_mood=user_mood,
                predicted_therapy=predicted_therapy,
                target_activity=target_activity,
                selected_language=selected_language,
                selected_genre=selected_genre,
                favorite_artists=fav_art,
                recent_artists=rec_art,
                liked_titles=liked_t,
                skipped_titles=skip_t,
                target_audio_features=target_audio_features
            )

            total = scores.get("total_score", -1000.0)
            if total > -50.0: # Keep only non-discarded verified tracks
                seen_keys.add(t_key)
                scored_track = dict(track)
                scored_track["song"] = title
                scored_track["title"] = title
                scored_track["artist"] = artist
                scored_track["artist_or_source"] = artist
                scored_track["recommendation_score"] = total
                scored_track["score"] = total
                scored_track["match_score"] = total
                scored_track["score_breakdown"] = scores

                # High quality artwork
                if not scored_track.get("album_image"):
                    scored_track["album_image"] = "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&h=300&fit=crop"
                scored_track["cover_image"] = scored_track.get("album_image")

                # Playback & Streaming URLs
                sp_url = scored_track.get("play_url") or f"https://open.spotify.com/search/{quote_plus(f'{title} {artist}')}"
                scored_track["play_url"] = sp_url
                scored_track["spotify_url"] = sp_url
                scored_track["youtube_search_url"] = scored_track.get("youtube_search_url") or f"https://www.youtube.com/results?search_query={quote_plus(f'{title} {artist}')}"

                # Explainability & matched feature tags
                matched_feats = [
                    f"✓ {selected_language} (10%)",
                    f"✓ {scores['mood_match']}/35 Mood Match",
                    f"✓ {scores['therapy_match']}/25 {predicted_therapy}",
                    f"✓ {scores['activity_match']}/15 {target_activity}"
                ]
                if scores["history_similarity"] > 0:
                    matched_feats.append(f"✓ {scores['history_similarity']}/10 History Match")
                
                scored_track["matched_features"] = matched_feats
                scored_track["reason"] = (
                    f"Therapeutic match: {scores['mood_match']}% mood resonance with your {user_mood.lower()} state, "
                    f"{scores['therapy_match']}% {predicted_therapy} alignment, and tailored for {target_activity.lower()}."
                )

                scored_candidates.append((total, scored_track))

        # Sort descending by total score and return Top N
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        final_ranked = [item[1] for item in scored_candidates[:top_n]]

        for idx, tr in enumerate(final_ranked, start=1):
            tr["rank"] = idx

        return final_ranked
