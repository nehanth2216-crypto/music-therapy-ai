import datetime
from typing import Dict, Any, List, Optional

# Supported Categoricals & Encodings
MOODS = ["Happy", "Sad", "Anxiety", "Angry", "Tired"]
SLEEP_QUALITIES = ["Good", "Fair", "Poor"]
ACTIVITIES = ["Studying", "Sleeping", "Meditation", "Exercise", "Relaxation"]
GENRES = ["Lo-fi", "Classical", "Nature Sounds", "Instrumental", "Pop"]

THERAPY_CATEGORIES = [
    "Sleep Therapy",
    "Anxiety Relief",
    "Stress Relief",
    "Meditation",
    "Relaxation",
    "Focus",
    "Motivation",
    "Workout",
    "Emotional Healing",
    "Happiness"
]

SUPPORTED_LANGUAGES = [
    "English", "Telugu", "Hindi", "Tamil", "Kannada", "Malayalam",
    "Punjabi", "Marathi", "Gujarati", "Bengali", "Urdu", "Japanese",
    "Korean", "Chinese", "Spanish", "French", "German", "Italian"
]

def encode_categorical(val: str, choices: List[str], default_idx: int = 0) -> int:
    """Safely map categorical string to numerical index."""
    if not val:
        return default_idx
    v_clean = val.strip().lower()
    for idx, choice in enumerate(choices):
        if choice.lower() == v_clean:
            return idx
    return default_idx

def get_time_of_day() -> str:
    """Determine current time of day bucket."""
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 17:
        return "Afternoon"
    elif 17 <= hour < 22:
        return "Evening"
    else:
        return "Night"

class FeatureEngineer:
    """Feature Engineering Pipeline for Therapy AI Recommendation Model."""
    
    def extract_features(
        self,
        survey_data: Dict[str, Any],
        history_summary: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract clean feature dictionary and numerical vector for XGBoost model.
        """
        age = int(survey_data.get("age", 25))
        mood = survey_data.get("mood", "Tired")
        stress = int(survey_data.get("stress", 5))
        anxiety = int(survey_data.get("anxiety", 5))
        sleep_quality = survey_data.get("sleep_quality", "Fair")
        activity = survey_data.get("activity", "Relaxation")
        fav_genre = survey_data.get("fav_genre", "Lo-fi")
        language_pref = survey_data.get("language_pref", "English")
        
        # Categorical Encodings
        mood_idx = encode_categorical(mood, MOODS)
        sleep_idx = encode_categorical(sleep_quality, SLEEP_QUALITIES)
        activity_idx = encode_categorical(activity, ACTIVITIES)
        genre_idx = encode_categorical(fav_genre, GENRES)
        lang_idx = encode_categorical(language_pref, SUPPORTED_LANGUAGES)
        time_of_day = get_time_of_day()

        # Derived Mental Health Metrics
        depression_val = 8 if mood.lower() in ["sad", "depressed"] else 3
        sleep_val = 3 if sleep_quality == "Poor" else (5 if sleep_quality == "Fair" else 8)
        energy_val = 3 if mood.lower() in ["tired", "sad"] else (9 if activity.lower() == "exercise" else 6)
        
        # User Interaction History Signals
        fav_artists = (history_summary.get("fav_artists", []) if history_summary else [])
        recent_tracks = (history_summary.get("recent_tracks", []) if history_summary else [])
        liked_tracks = (history_summary.get("liked_tracks", []) if history_summary else [])
        skipped_tracks = (history_summary.get("skipped_tracks", []) if history_summary else [])

        # Numerical vector for ML prediction matching 11 clinical features
        feature_vector = [
            float(age),
            float(mood_idx),
            float(stress),
            float(sleep_idx),
            float(anxiety),
            float(activity_idx),
            float(genre_idx),
            float(lang_idx),
            float(depression_val),
            float(sleep_val),
            float(energy_val)
        ]

        return {
            "age": age,
            "mood": mood,
            "stress": stress,
            "anxiety": anxiety,
            "sleep_quality": sleep_quality,
            "activity": activity,
            "fav_genre": fav_genre,
            "language_pref": language_pref,
            "time_of_day": time_of_day,
            "mood_idx": mood_idx,
            "sleep_idx": sleep_idx,
            "activity_idx": activity_idx,
            "genre_idx": genre_idx,
            "lang_idx": lang_idx,
            "depression_val": depression_val,
            "sleep_val": sleep_val,
            "energy_val": energy_val,
            "fav_artists": fav_artists,
            "recent_tracks": recent_tracks,
            "liked_tracks": liked_tracks,
            "skipped_tracks": skipped_tracks,
            "feature_vector": feature_vector
        }
