import os
import json
from typing import Dict, Any, List, Optional, Tuple

CATALOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dataset", "multilingual_music_catalog.json")

# Mood compatibility matrix
# Mood compatibility matrix
# Each user mood maps to a dictionary of song moods with compatibility scores (0.0 to 1.0)
MOOD_COMPATIBILITY = {
    "stressed": {
        "stressed": 1.0,
        "calm": 0.70,
        "relaxed": 0.70,
        "emotional": 0.60,
        "romantic": 0.60,
        "happy": 0.30,
        "energetic": 0.10
    },
    "anxious": {
        "anxious": 1.0,
        "calm": 0.85,
        "relaxed": 0.85,
        "stressed": 0.60,
        "romantic": 0.50,
        "emotional": 0.50,
        "happy": 0.30,
        "energetic": 0.10
    },
    "anxiety": {
        "anxiety": 1.0,
        "anxious": 1.0,
        "calm": 0.85,
        "relaxed": 0.85,
        "stressed": 0.60,
        "romantic": 0.50,
        "emotional": 0.50,
        "happy": 0.30,
        "energetic": 0.10
    },
    "calm": {
        "calm": 1.0,
        "relaxed": 1.0,
        "romantic": 0.80,
        "emotional": 0.60,
        "happy": 0.50,
        "stressed": 0.30,
        "energetic": 0.10
    },
    "relaxed": {
        "relaxed": 1.0,
        "calm": 1.0,
        "romantic": 0.80,
        "emotional": 0.60,
        "happy": 0.50,
        "stressed": 0.30,
        "energetic": 0.10
    },
    "happy": {
        "happy": 1.0,
        "energetic": 0.85,
        "romantic": 0.70,
        "calm": 0.50,
        "emotional": 0.20,
        "stressed": 0.10
    },
    "energetic": {
        "energetic": 1.0,
        "happy": 0.85,
        "romantic": 0.30,
        "calm": 0.10,
        "emotional": 0.10,
        "stressed": 0.10
    },
    "sad": {
        "emotional": 1.0,
        "sad": 1.0,
        "calm": 0.80,
        "romantic": 0.70,
        "stressed": 0.50,
        "happy": 0.20,
        "energetic": 0.10
    },
    "emotional": {
        "emotional": 1.0,
        "calm": 0.80,
        "romantic": 0.75,
        "stressed": 0.50,
        "happy": 0.30,
        "energetic": 0.10
    },
    "romantic": {
        "romantic": 1.0,
        "calm": 0.80,
        "emotional": 0.75,
        "happy": 0.70,
        "energetic": 0.20,
        "stressed": 0.10
    },
    "angry": {
        "calm": 0.85,
        "relaxed": 0.80,
        "stressed": 0.60,
        "emotional": 0.50,
        "energetic": 0.30,
        "happy": 0.20
    },
    "tired": {
        "calm": 1.0,
        "relaxed": 1.0,
        "romantic": 0.60,
        "emotional": 0.40,
        "happy": 0.30,
        "energetic": 0.10
    },
    "focused": {
        "calm": 1.0,
        "relaxed": 0.85,
        "romantic": 0.60,
        "happy": 0.50,
        "emotional": 0.40,
        "energetic": 0.10
    },
    "bored": {
        "happy": 1.0,
        "energetic": 0.90,
        "romantic": 0.60,
        "calm": 0.40,
        "emotional": 0.20
    }
}

# Activity compatibility matrix
ACTIVITY_COMPATIBILITY = {
    "studying": {
        "studying": 1.0,
        "relaxing": 0.70,
        "walking": 0.40,
        "driving": 0.30,
        "party": 0.05,
        "workout": 0.05
    },
    "working": {
        "studying": 1.0,
        "relaxing": 0.70,
        "walking": 0.40,
        "driving": 0.30,
        "workout": 0.05,
        "party": 0.05
    },
    "workout": {
        "workout": 1.0,
        "party": 0.80,
        "driving": 0.40,
        "walking": 0.40,
        "relaxing": 0.05,
        "studying": 0.05
    },
    "running": {
        "workout": 1.0,
        "party": 0.80,
        "driving": 0.40,
        "walking": 0.40,
        "relaxing": 0.05,
        "studying": 0.05
    },
    "party": {
        "party": 1.0,
        "workout": 0.80,
        "driving": 0.40,
        "walking": 0.30,
        "relaxing": 0.05,
        "studying": 0.05
    },
    "relaxing": {
        "relaxing": 1.0,
        "studying": 0.70,
        "walking": 0.50,
        "driving": 0.30,
        "party": 0.05,
        "workout": 0.05
    },
    "meditation": {
        "relaxing": 1.0,
        "studying": 0.70,
        "walking": 0.40,
        "driving": 0.20,
        "party": 0.05,
        "workout": 0.05
    },
    "sleeping": {
        "relaxing": 1.0,
        "studying": 0.60,
        "walking": 0.20,
        "driving": 0.10,
        "party": 0.05,
        "workout": 0.05
    },
    "walking": {
        "walking": 1.0,
        "relaxing": 0.70,
        "studying": 0.50,
        "driving": 0.50,
        "workout": 0.40,
        "party": 0.30
    },
    "driving": {
        "driving": 1.0,
        "walking": 0.60,
        "workout": 0.50,
        "party": 0.50,
        "relaxing": 0.40,
        "studying": 0.30
    },
    "gaming": {
        "workout": 0.80,
        "party": 0.80,
        "driving": 0.60,
        "studying": 0.50,
        "walking": 0.40,
        "relaxing": 0.30
    },
    "cooking": {
        "party": 0.70,
        "walking": 0.70,
        "relaxing": 0.60,
        "studying": 0.50,
        "driving": 0.50,
        "workout": 0.30
    }
}

# Energy compatibility matrix
ENERGY_COMPATIBILITY = {
    "low": {
        "low": 1.0,
        "medium": 0.50,
        "high": 0.0
    },
    "medium": {
        "medium": 1.0,
        "low": 0.70,
        "high": 0.70
    },
    "high": {
        "high": 1.0,
        "medium": 0.50,
        "low": 0.0
    }
}

# Genre compatibility matrix
GENRE_COMPATIBILITY = {
    "melody": {
        "melody": 1.0,
        "classical": 0.90,
        "acoustic": 0.85,
        "ballad": 0.85,
        "lo-fi": 0.80,
        "pop": 0.65,
        "folk": 0.60,
        "dance": 0.40,
        "rock": 0.30
    },
    "pop": {
        "pop": 1.0,
        "dance": 0.85,
        "rock": 0.70,
        "melody": 0.65,
        "ballad": 0.65,
        "acoustic": 0.60,
        "folk": 0.50,
        "lo-fi": 0.50
    },
    "dance": {
        "dance": 1.0,
        "pop": 0.85,
        "rock": 0.75,
        "folk": 0.60,
        "melody": 0.40,
        "ballad": 0.20,
        "lo-fi": 0.20
    },
    "rock": {
        "rock": 1.0,
        "dance": 0.75,
        "pop": 0.70,
        "folk": 0.50,
        "melody": 0.35,
        "ballad": 0.30
    },
    "folk": {
        "folk": 1.0,
        "acoustic": 0.85,
        "melody": 0.80,
        "dance": 0.60,
        "pop": 0.50,
        "classical": 0.60
    },
    "ballad": {
        "ballad": 1.0,
        "melody": 0.85,
        "acoustic": 0.85,
        "pop": 0.65,
        "classical": 0.70,
        "lo-fi": 0.70
    },
    "acoustic": {
        "acoustic": 1.0,
        "melody": 0.85,
        "ballad": 0.85,
        "lo-fi": 0.85,
        "folk": 0.80,
        "pop": 0.60,
        "classical": 0.75
    },
    "lo-fi": {
        "lo-fi": 1.0,
        "acoustic": 0.90,
        "melody": 0.85,
        "ballad": 0.80,
        "classical": 0.80,
        "folk": 0.60,
        "pop": 0.50,
        "dance": 0.20,
        "rock": 0.10
    },
    "classical": {
        "classical": 1.0,
        "melody": 0.90,
        "acoustic": 0.85,
        "lo-fi": 0.80,
        "ballad": 0.80,
        "folk": 0.60,
        "pop": 0.40,
        "dance": 0.10,
        "rock": 0.10
    },
    "instrumental": {
        "acoustic": 0.95,
        "melody": 0.90,
        "ballad": 0.80,
        "classical": 0.80,
        "folk": 0.70,
        "pop": 0.50,
        "dance": 0.20,
        "rock": 0.20
    },
    "nature sounds": {
        "acoustic": 0.95,
        "melody": 0.85,
        "ballad": 0.80,
        "classical": 0.80,
        "folk": 0.70,
        "pop": 0.30,
        "dance": 0.05,
        "rock": 0.05
    },
    "soundtrack": {
        "melody": 0.95,
        "ballad": 0.90,
        "pop": 0.85,
        "acoustic": 0.80,
        "rock": 0.75,
        "dance": 0.70,
        "folk": 0.65
    }
}

class WeightedSongRecommendationEngine:
    """
    Production Deterministic Weighted Music Recommendation Engine.
    Operates directly on the 500-song authentic catalog across Telugu, Tamil, Hindi, Malayalam, and English.
    """

    def __init__(self, catalog_path: Optional[str] = None):
        self.catalog_path = catalog_path or CATALOG_PATH
        self.catalog: List[Dict[str, Any]] = []
        self.load_catalog()

    def load_catalog(self):
        """Load authentic music catalog from previous dataset (multilingual_music_catalog.json)."""
        if os.path.exists(self.catalog_path):
            try:
                with open(self.catalog_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self.catalog = data
                elif isinstance(data, dict):
                    # Flatten previous multilingual music catalog dictionary
                    flattened = []
                    for lang, songs in data.items():
                        for s in songs:
                            s_copy = dict(s)
                            if "language" not in s_copy:
                                s_copy["language"] = lang
                            if "song" not in s_copy:
                                s_copy["song"] = s_copy.get("title", "")
                            if "title" not in s_copy:
                                s_copy["title"] = s_copy.get("song", "")
                            if "artist" not in s_copy:
                                s_copy["artist"] = s_copy.get("artist_or_source", "")
                            if "artist_or_source" not in s_copy:
                                s_copy["artist_or_source"] = s_copy.get("artist", "")

                            # Map / infer clinical features from mood and genre if not explicitly present
                            m_lower = str(s_copy.get("mood", "")).lower()
                            g_lower = str(s_copy.get("genre", "")).lower()
                            if "energy" not in s_copy or not s_copy["energy"]:
                                if m_lower in ["energetic", "happy"] or g_lower in ["dance", "pop", "rock"]:
                                    s_copy["energy"] = "High"
                                elif m_lower in ["calm", "calming", "relaxed", "tired", "anxiety", "lo-fi"] or g_lower in ["lo-fi", "acoustic", "classical", "melody"]:
                                    s_copy["energy"] = "Low"
                                else:
                                    s_copy["energy"] = "Medium"

                            if "activity" not in s_copy or not s_copy["activity"]:
                                if m_lower in ["energetic"] or g_lower in ["dance", "party"]:
                                    s_copy["activity"] = "Party"
                                elif g_lower in ["rock", "workout"]:
                                    s_copy["activity"] = "Workout"
                                elif g_lower in ["lo-fi", "acoustic"] or m_lower in ["studying", "focused"]:
                                    s_copy["activity"] = "Studying"
                                else:
                                    s_copy["activity"] = "Relaxing"

                            if "min_age" not in s_copy:
                                s_copy["min_age"] = 10
                            if "max_age" not in s_copy:
                                s_copy["max_age"] = 80

                            flattened.append(s_copy)
                    self.catalog = flattened
            except Exception as e:
                print(f"Error loading song catalog: {e}")
                self.catalog = []
        else:
            print(f"Warning: catalog file {self.catalog_path} not found.")
            self.catalog = []

    @staticmethod
    def calculate_language_match(song_lang: str, user_lang: str) -> float:
        """Language Match (Hard gate: must match exactly)."""
        if not user_lang or not song_lang:
            return 1.0
        return 1.0 if song_lang.strip().lower() == user_lang.strip().lower() else 0.0

    @staticmethod
    def calculate_mood_match(song_mood: str, user_mood: str) -> float:
        """Mood compatibility match (0.0 to 1.0) strictly based on authentic song mood."""
        s_m = (song_mood or "").strip().lower()
        u_m = (user_mood or "calm").strip().lower()

        # Mood normalizations
        mood_synonyms = {
            "calming": "calm",
            "relaxed": "calm",
            "relaxing": "calm",
            "anxious": "anxiety",
            "stressed": "anxiety",
            "energetic": "happy",
            "joyful": "happy",
            "exhausted": "tired",
            "fatigued": "tired"
        }
        s_norm = mood_synonyms.get(s_m, s_m)
        u_norm = mood_synonyms.get(u_m, u_m)

        if not s_m:
            return 0.30
        if s_m == u_m or s_norm == u_norm:
            return 1.0

        compat_table = MOOD_COMPATIBILITY.get(u_norm, MOOD_COMPATIBILITY.get(u_m, {}))
        return compat_table.get(s_norm, compat_table.get(s_m, 0.10))

    @staticmethod
    def calculate_activity_match(song_act: str, user_act: str) -> float:
        """Activity compatibility match (0.0 to 1.0) strictly based on authentic song activity."""
        s_a = (song_act or "").strip().lower()
        u_a = (user_act or "relaxing").strip().lower()

        if not s_a:
            return 0.20
        if s_a == u_a:
            return 1.0

        compat_table = ACTIVITY_COMPATIBILITY.get(u_a, {})
        return compat_table.get(s_a, 0.05)

    @staticmethod
    def calculate_genre_match(song_genre: str, user_genre: str) -> float:
        """Genre compatibility match (0.0 to 1.0)."""
        s_g = (song_genre or "").strip().lower()
        u_g = (user_genre or "").strip().lower()

        if not u_g:
            return 1.0
        if s_g == u_g or s_g in u_g or u_g in s_g:
            return 1.0

        compat_table = GENRE_COMPATIBILITY.get(u_g, {})
        return compat_table.get(s_g, 0.20)

    @staticmethod
    @staticmethod
    def calculate_energy_match(song_energy: str, user_energy: str) -> float:
        """Energy compatibility match according to exact specification."""
        s_e = (song_energy or "medium").strip().lower()
        u_e = (user_energy or "medium").strip().lower()

        table = ENERGY_COMPATIBILITY.get(u_e, ENERGY_COMPATIBILITY["medium"])
        return table.get(s_e, 0.50)

    @staticmethod
    def calculate_stress_anxiety_fit(song_mood: str, song_act: str, song_energy: str, stress: int, anxiety: int) -> float:
        """Clinical therapy fit based on user's stress and anxiety levels (1-10)."""
        s_m = (song_mood or "").strip().lower()
        s_a = (song_act or "").strip().lower()
        s_e = (song_energy or "").strip().lower()
        
        # High stress or acute anxiety (>= 7)
        if stress >= 7 or anxiety >= 7:
            if s_e == "high" or s_a in ["party", "workout"]:
                return 0.05  # Severe contraindication for acute stress/anxiety
            if s_m in ["calm", "stressed", "emotional", "romantic"] and s_e in ["low", "medium"]:
                return 1.0  # Therapeutic nervous system down-regulation
            return 0.50

        # Low stress / low anxiety (<= 3)
        elif stress <= 3 and anxiety <= 3:
            if s_e in ["high", "medium"]:
                return 1.0
            return 0.75

        # Moderate / baseline (4 to 6)
        else:
            return 0.85

    @staticmethod
    def calculate_age_match(min_age: int, max_age: int, user_age: int) -> float:
        """Age compatibility curve (1–100, non-restrictive factor)."""
        try:
            u_age = int(user_age)
        except (ValueError, TypeError):
            return 1.0

        if min_age <= u_age <= max_age:
            return 1.0

        # Distance to closest age range boundary
        dist = min(abs(u_age - min_age), abs(u_age - max_age))
        # Gentle decay with floor of 0.40
        return max(0.40, 1.0 - (dist / 100.0) * 0.75)

    def score_song(
        self,
        song_item: Dict[str, Any],
        user_state: Dict[str, Any]
    ) -> Tuple[float, List[str], str]:
        """
        Calculate weighted score (0.0 - 100.0) factoring in complete user state:
        Language (25%), Mood (20%), Activity (20%), Energy (15%), Stress/Anxiety Therapy Fit (10%), Genre (5%), Age (5%).
        """
        user_lang = str(user_state.get("language") or user_state.get("language_pref") or "English").strip()
        user_mood = str(user_state.get("mood") or "Calm").strip()
        user_act = str(user_state.get("activity") or "Relaxing").strip()
        user_genre = str(user_state.get("genre") or user_state.get("fav_genre") or "").strip()
        user_energy = str(user_state.get("energy") or "Medium").strip()
        user_age = int(user_state.get("age") or 25)
        user_stress = int(user_state.get("stress") or 5)
        user_anxiety = int(user_state.get("anxiety") or 5)

        s_lang = str(song_item.get("language") or "").strip()
        s_mood = str(song_item.get("mood") or "").strip()
        s_act = str(song_item.get("activity") or "").strip()
        s_genre = str(song_item.get("genre") or "").strip()
        s_energy = str(song_item.get("energy") or "").strip()
        s_artist = str(song_item.get("artist") or song_item.get("artist_or_source") or "").strip()
        s_min_age = int(song_item.get("min_age") or 1)
        s_max_age = int(song_item.get("max_age") or 100)

        # Fallback infer energy if empty
        if not s_energy:
            if s_mood.lower() in ["energetic", "happy"] or s_genre.lower() in ["dance", "pop", "rock"]:
                s_energy = "High"
            elif s_mood.lower() in ["calm", "calming", "relaxed", "tired", "anxiety", "lo-fi"] or s_genre.lower() in ["lo-fi", "acoustic", "classical", "melody"]:
                s_energy = "Low"
            else:
                s_energy = "Medium"

        # Fallback infer activity if empty
        if not s_act:
            if s_mood.lower() in ["energetic"] or s_genre.lower() in ["dance", "party"]:
                s_act = "Party"
            elif s_genre.lower() in ["rock", "workout"]:
                s_act = "Workout"
            elif s_genre.lower() in ["lo-fi", "acoustic"] or s_mood.lower() in ["studying", "focused"]:
                s_act = "Studying"
            else:
                s_act = "Relaxing"

        # 1. Language Match (25% - Hard Gate)
        lang_match = self.calculate_language_match(s_lang, user_lang)
        if lang_match == 0.0:
            return 0.0, [], "Non-matching language"

        # 2. Mood Match (20%)
        mood_match = self.calculate_mood_match(s_mood, user_mood)

        # 3. Activity Match (20%)
        act_match = self.calculate_activity_match(s_act, user_act)

        # 4. Energy Match (15% - Sharpened to eliminate energy clashes)
        energy_match = self.calculate_energy_match(s_energy, user_energy)

        # 5. Clinical Stress & Anxiety Fit (10%)
        therapy_fit = self.calculate_stress_anxiety_fit(s_mood, s_act, s_energy, user_stress, user_anxiety)

        # 6. Genre Match (5%)
        genre_match = self.calculate_genre_match(s_genre, user_genre)

        # 7. Age Compatibility (5%)
        age_match = self.calculate_age_match(s_min_age, s_max_age, user_age)

        # Weighted calculation normalized to 0–100
        score = (
            (lang_match * 0.25) +
            (mood_match * 0.20) +
            (act_match * 0.20) +
            (energy_match * 0.15) +
            (therapy_fit * 0.10) +
            (genre_match * 0.05) +
            (age_match * 0.05)
        ) * 100.0

        # Hard conflict penalty: polar opposite energy during intensity-specific activities
        if user_energy.lower() == "high" and s_energy.lower() == "low" and user_act.lower() in ["workout", "running", "party"]:
            score *= 0.50  # Heavy penalty for slow lullabies during high-intensity workout
        if user_energy.lower() == "low" and s_energy.lower() == "high" and user_act.lower() in ["studying", "sleeping", "meditation"]:
            score *= 0.50  # Heavy penalty for loud party tracks during quiet study/sleep

        # Secondary personalization from listening history
        history = user_state.get("history") or user_state.get("listening_history") or []
        if history and isinstance(history, list):
            hist_genres = [str(h.get("genre", "")).lower() for h in history if isinstance(h, dict)]
            hist_artists = [str(h.get("artist", "")).lower() for h in history if isinstance(h, dict)]
            hist_energies = [str(h.get("energy", "")).lower() for h in history if isinstance(h, dict)]
            history_bonus = 0.0
            if s_genre.lower() in hist_genres:
                history_bonus += 0.5
            if s_artist.lower() in hist_artists:
                history_bonus += 0.5
            if s_energy.lower() in hist_energies:
                history_bonus += 0.2
            score = min(100.0, score + min(1.2, history_bonus))

        score = round(score, 1)

        # Generate matched features checklist
        matched_features = []
        if lang_match == 1.0:
            matched_features.append(f"✓ {s_lang}")

        if s_genre.lower() == user_genre.lower():
            matched_features.append(f"✓ {s_genre}")
        elif genre_match >= 0.70:
            matched_features.append(f"✓ {s_genre} ({user_genre}-compatible)")

        if s_mood.lower() == user_mood.lower():
            matched_features.append(f"✓ {s_mood} Mood")
        elif mood_match >= 0.70:
            matched_features.append(f"✓ {s_mood}/{user_mood}-compatible")

        if s_act.lower() == user_act.lower():
            matched_features.append(f"✓ {s_act}")
        elif act_match >= 0.70:
            matched_features.append(f"✓ {s_act}-compatible")

        if s_energy.lower() == user_energy.lower():
            matched_features.append(f"✓ {s_energy} energy")

        if therapy_fit >= 0.90 and (user_stress >= 7 or user_anxiety >= 7):
            matched_features.append("✓ Stress/Anxiety Relief")

        if s_min_age <= user_age <= s_max_age:
            matched_features.append(f"✓ Target demographic (age {user_age})")

        # Generate human-readable explanation
        reason_parts = []
        if genre_match >= 0.80 and user_genre:
            reason_parts.append(f"{user_lang} {s_genre} preference")
        else:
            reason_parts.append(f"{user_lang} catalog")

        if mood_match >= 0.80:
            reason_parts.append(f"{user_mood.lower()} therapeutic mindset")
        elif s_mood:
            reason_parts.append(f"{s_mood.lower()} vibes")

        if act_match >= 0.80:
            reason_parts.append(f"{user_act.lower()} session")

        if energy_match == 1.0:
            reason_parts.append(f"{user_energy.lower()} energy level")

        reason = f"Strong match for your {', '.join(reason_parts)}."

        return score, matched_features, reason

    def recommend(
        self,
        user_state: Dict[str, Any],
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate top 5–10 deterministic, explainable song recommendations.
        Strict sorting:
          1. score descending
          2. song title ascending
          3. artist ascending
        Guarantees fallback so never empty when songs exist in the target language.
        """
        user_lang = str(user_state.get("language") or user_state.get("language_pref") or "English").strip()

        # Step A: Filter by target language (Hard filter: Telugu/Tamil/Hindi/Malayalam/English)
        candidate_items = [
            it for it in self.catalog
            if it.get("language", "").strip().lower() == user_lang.lower()
        ]

        if len(candidate_items) < 10:
            try:
                from backend.ml.recommender import fetch_live_itunes_tracks
                genre_term = str(user_state.get("genre") or user_state.get("fav_genre") or "").strip()
                mood_term = str(user_state.get("mood") or "").strip()
                queries_to_try = [genre_term, mood_term, "hits", "popular"]
                for q in queries_to_try:
                    if len(candidate_items) >= 15:
                        break
                    if not q:
                        continue
                    live_tracks = fetch_live_itunes_tracks(
                        q,
                        language=user_lang,
                        limit=15
                    )
                    for lt in live_tracks:
                        lt_copy = dict(lt)
                        lt_copy["language"] = user_lang
                        if not lt_copy.get("genre"):
                            lt_copy["genre"] = genre_term or "Pop"
                        if not lt_copy.get("mood"):
                            lt_copy["mood"] = mood_term or "Calm"
                        candidate_items.append(lt_copy)
            except Exception:
                pass

        if not candidate_items:
            return []

        # Step B: Score all candidate items and group by unique song title + artist
        scored_unique_songs: Dict[str, Dict[str, Any]] = {}

        for item in candidate_items:
            song_name = (item.get("song") or item.get("title") or "").strip()
            artist = (item.get("artist") or item.get("artist_or_source") or "").strip()
            song_key = f"{song_name.lower()}___{artist.lower()}"

            score, matched_features, reason = self.score_song(item, user_state)

            song_record = {
                "id": item.get("id"),
                "song": song_name,
                "title": song_name,
                "artist": artist,
                "artist_or_source": artist,
                "language": item.get("language"),
                "genre": item.get("genre"),
                "mood": item.get("mood"),
                "activity": item.get("activity"),
                "energy": item.get("energy"),
                "age_group": item.get("age_group"),
                "score": score,
                "match_score": score,
                "matched_features": matched_features,
                "reason": reason,
                "album_image": item.get("album_image") or "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&h=300&fit=crop",
                "cover_image": item.get("album_image") or "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&h=300&fit=crop",
                "preview_url": item.get("preview_url") or "",
                "play_url": item.get("play_url") or f"https://open.spotify.com/search/{song_name}",
                "youtube_search_url": f"https://www.youtube.com/results?search_query={song_name.replace(' ', '+')}+{artist.replace(' ', '+')}"
            }

            if song_key not in scored_unique_songs or score > scored_unique_songs[song_key]["score"]:
                scored_unique_songs[song_key] = song_record

        unique_song_list = list(scored_unique_songs.values())

        # Step C: Deterministic sorting
        # Primary: Score descending (-score)
        # Secondary: Song title ascending (song.lower())
        # Tertiary: Artist ascending (artist.lower())
        unique_song_list.sort(key=lambda s: (-s["score"], s["song"].lower(), s["artist"].lower()))

        # Step D: Apply quality filter (filter out complete mismatches, guarantee at least 5 songs)
        high_quality = [s for s in unique_song_list if s["score"] >= 65.0]
        final_candidates = high_quality if len(high_quality) >= 5 else unique_song_list
        effective_limit = max(5, min(top_n, len(final_candidates)))
        top_recommendations = final_candidates[:effective_limit]

        # Assign rank 1-indexed
        for idx, rec in enumerate(top_recommendations, start=1):
            rec["rank"] = idx

        return top_recommendations

