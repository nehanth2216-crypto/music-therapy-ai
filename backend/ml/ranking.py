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
        skipped_titles: Set[str] = None,
        user_age: Any = None
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

        # 9. Age Group & Therapeutic Context Matching Bonus (0 - 15 points)
        context_score = 0.0
        if user_age is not None:
            try:
                u_age = int(user_age)
                if u_age <= 5:
                    target_ag = "1-5"
                elif u_age <= 12:
                    target_ag = "6-12"
                elif u_age <= 17:
                    target_ag = "13-17"
                elif u_age <= 25:
                    target_ag = "18-25"
                elif u_age <= 35:
                    target_ag = "26-35"
                elif u_age <= 50:
                    target_ag = "36-50"
                elif u_age <= 65:
                    target_ag = "51-65"
                elif u_age <= 80:
                    target_ag = "66-80"
                else:
                    target_ag = "81-100"
                
                track_age_groups = track.get("age_groups", [])
                if target_ag in track_age_groups:
                    context_score += 10.0
            except (ValueError, TypeError):
                pass

        c_mood = (track.get("context_mood") or "").lower()
        c_act = (track.get("context_activity") or "").lower()
        if c_mood and m_lower and (c_mood in m_lower or m_lower in c_mood):
            context_score += 3.0
        if c_act and act_lower and (c_act in act_lower or act_lower in c_act):
            context_score += 2.0

        total_score = lang_score + genre_score + mood_score + therapy_score + activity_score + history_score + pop_score + context_score
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
        user_age: Any = None,
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
                skipped_titles=skip_t,
                user_age=user_age
            )

            if score > -500.0:
                seen_titles.add(t_key)
                scored_track = dict(track)
                title = scored_track.get("title") or scored_track.get("song") or "Therapeutic Track"
                artist = scored_track.get("artist") or scored_track.get("artist_or_source") or "HarmonyRec"
                norm_score = max(0.0, min(100.0, round(score, 1)))

                scored_track["song"] = title
                scored_track["title"] = title
                scored_track["artist"] = artist
                scored_track["artist_or_source"] = artist
                scored_track["recommendation_score"] = norm_score
                scored_track["score"] = norm_score
                scored_track["match_score"] = norm_score

                # Image formatting
                if not scored_track.get("album_image"):
                    scored_track["album_image"] = "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&h=300&fit=crop"
                scored_track["cover_image"] = scored_track.get("album_image")

                # Playback & Streaming URLs
                from urllib.parse import quote_plus
                if not scored_track.get("play_url"):
                    scored_track["play_url"] = f"https://open.spotify.com/search/{quote_plus(f'{title} {artist}')}"
                if not scored_track.get("spotify_url"):
                    scored_track["spotify_url"] = scored_track["play_url"]
                if not scored_track.get("youtube_search_url"):
                    scored_track["youtube_search_url"] = f"https://www.youtube.com/results?search_query={quote_plus(f'{title} {artist}')}"

                # Feature tags and explanations
                feats = [f"✓ {selected_language}"]
                t_mood = scored_track.get("mood") or user_mood
                feats.append(f"✓ {t_mood} mood")
                if selected_genre:
                    feats.append(f"✓ {selected_genre} style")
                if target_activity:
                    feats.append(f"✓ {target_activity}")
                scored_track["matched_features"] = feats
                scored_track["reason"] = f"Strong therapeutic match for your {selected_language} music preference, {user_mood.lower()} mood, and {target_activity.lower()} session."

                scored_list.append((norm_score, scored_track))

        scored_list.sort(key=lambda x: x[0], reverse=True)
        final_tracks = [t[1] for t in scored_list[:top_n]]
        for idx, tr in enumerate(final_tracks, start=1):
            tr["rank"] = idx
        return final_tracks
