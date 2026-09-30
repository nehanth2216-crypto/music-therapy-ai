import datetime
from typing import Dict, Any, List, Optional

# Supported Categoricals & Encodings
MOODS = [
    "Happy", "Sad", "Anxiety", "Angry", "Tired",
    "Calm", "Stressed", "Energetic", "Relaxed", "Focused",
    "Romantic", "Motivated"
]
SLEEP_QUALITIES = ["Good", "Fair", "Poor"]
ACTIVITIES = ["Studying", "Sleeping", "Meditation", "Exercise", "Relaxation", "Working", "Walking", "Driving"]
GENRES = ["Lo-fi", "Classical", "Nature Sounds", "Instrumental", "Pop", "Melody", "Acoustic", "Ambient"]

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
    """Safely map categorical string to numerical index with semantic alias awareness."""
    if not val:
        return default_idx
    v_clean = str(val).strip().lower()
    for idx, choice in enumerate(choices):
        if choice.lower() == v_clean:
            return idx

    # Mood specific semantic routing
    if choices == MOODS:
        if any(k in v_clean for k in ["romant", "love"]):
            return choices.index("Romantic")
        if any(k in v_clean for k in ["motivat", "dheera", "inspire", "power"]):
            return choices.index("Motivated")
        if any(k in v_clean for k in ["anxi", "panic"]):
            return choices.index("Anxiety")
        if any(k in v_clean for k in ["stress"]):
            return choices.index("Stressed")
        if any(k in v_clean for k in ["angr"]):
            return choices.index("Angry")
        if any(k in v_clean for k in ["sleep", "tired"]):
            return choices.index("Tired")
        if any(k in v_clean for k in ["calm"]):
            return choices.index("Calm")
        if any(k in v_clean for k in ["relax"]):
            return choices.index("Relaxed")
        if any(k in v_clean for k in ["energet", "workout"]):
            return choices.index("Energetic")
        if any(k in v_clean for k in ["sad", "depress", "grief"]):
            return choices.index("Sad")
        if any(k in v_clean for k in ["happ", "joy"]):
            return choices.index("Happy")
        if any(k in v_clean for k in ["focus", "study", "work"]):
            return choices.index("Focused")

    # Partial matching fallback
    for idx, choice in enumerate(choices):
        if choice.lower() in v_clean or v_clean in choice.lower():
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

def get_target_audio_features(survey_data: Dict[str, Any]) -> Dict[str, float]:
    """
    Synthesize target audio features (energy, valence, danceability, tempo, acousticness, instrumentalness, speechiness)
    matching the user's mental health state and clinical requirements (Requirement 6).
    """
    mood = str(survey_data.get("mood") or "Calm").strip().lower()
    try:
        stress = float(survey_data.get("stress") or 5)
    except (ValueError, TypeError):
        stress = 5.0
    try:
        anxiety = float(survey_data.get("anxiety") or 5)
    except (ValueError, TypeError):
        anxiety = 5.0
        
    activity = str(survey_data.get("activity") or "Relaxation").strip().lower()
    sleep_quality = str(survey_data.get("sleep_quality") or "Fair").strip().lower()
    time_of_day = survey_data.get("time_of_day") or get_time_of_day()

    # Base neutral parameters
    energy = 0.50
    valence = 0.50
    danceability = 0.45
    tempo = 90.0
    acousticness = 0.50
    instrumentalness = 0.40
    speechiness = 0.06

    # 1. Anxiety Relief (High Anxiety -> Low Energy, Slow Tempo, High Acousticness, Instrumental)
    if anxiety >= 7 or "anxi" in mood:
        energy = max(0.15, 0.35 - (anxiety - 7) * 0.05)
        tempo = max(60.0, 75.0 - (anxiety - 7) * 3.0)
        acousticness = min(0.95, 0.75 + (anxiety - 7) * 0.05)
        instrumentalness = min(0.90, 0.70 + (anxiety - 7) * 0.05)
        valence = 0.45
        speechiness = 0.04

    # 2. Stress Relief (High Stress -> Soothing, Low Energy, High Acousticness)
    elif stress >= 7 or "stress" in mood or "angr" in mood:
        energy = max(0.20, 0.40 - (stress - 7) * 0.04)
        tempo = max(65.0, 80.0 - (stress - 7) * 2.5)
        acousticness = min(0.90, 0.70 + (stress - 7) * 0.05)
        instrumentalness = min(0.85, 0.60 + (stress - 7) * 0.05)
        valence = 0.45
        speechiness = 0.05

    # 3. Depression / Sad / Emotional Healing
    elif "sad" in mood or "depress" in mood:
        energy = 0.35
        tempo = 72.0
        acousticness = 0.75
        instrumentalness = 0.55
        valence = 0.38
        speechiness = 0.06

    # 4. Motivated / Inspiring / Power
    elif any(k in mood for k in ["motivat", "dheera", "inspire", "power"]):
        energy = 0.88
        tempo = 126.0
        acousticness = 0.25
        danceability = 0.72
        valence = 0.80
        instrumentalness = 0.15
        speechiness = 0.08

    # 5. Romantic / Love
    elif any(k in mood for k in ["romant", "love"]):
        energy = 0.52
        tempo = 92.0
        acousticness = 0.65
        danceability = 0.55
        valence = 0.75
        instrumentalness = 0.25
        speechiness = 0.05

    # 6. Calm / Peace / Relaxed
    elif any(k in mood for k in ["calm", "peace", "relax"]):
        energy = 0.35
        tempo = 76.0
        acousticness = 0.75
        instrumentalness = 0.60
        valence = 0.55
        speechiness = 0.04

    # 7. Sleep / Tired / Night
    elif any(k in mood for k in ["sleep", "tired"]):
        energy = 0.20
        tempo = 65.0
        acousticness = 0.85
        instrumentalness = 0.80
        valence = 0.40
        speechiness = 0.03

    # 8. Happiness / Joy / Upbeat
    elif "happ" in mood or "energetic" in mood:
        energy = 0.78
        tempo = 120.0
        acousticness = 0.25
        danceability = 0.72
        valence = 0.82
        instrumentalness = 0.15
        speechiness = 0.08

    # 9. Activity Modulations (Requirement 6: Gym, Study, Sleep, Meditation)
    if any(k in activity for k in ["exercise", "workout", "gym", "running"]):
        # Gym: High Energy, High Tempo, High Danceability
        energy = max(energy, 0.85)
        tempo = max(tempo, 128.0)
        danceability = max(danceability, 0.78)
        acousticness = min(acousticness, 0.20)
        valence = max(valence, 0.65)
    elif any(k in activity for k in ["study", "work", "focus"]):
        # Study: Instrumental, Medium Energy, Low Speechiness
        instrumentalness = max(instrumentalness, 0.80)
        energy = 0.45
        tempo = 88.0
        speechiness = min(speechiness, 0.04)
    elif any(k in activity for k in ["sleep", "bed", "rest"]) or sleep_quality == "poor":
        # Sleep: Very Low Energy, Slow Tempo, High Acousticness, Low Danceability
        energy = min(energy, 0.20)
        tempo = min(tempo, 65.0)
        acousticness = max(acousticness, 0.85)
        instrumentalness = max(instrumentalness, 0.80)
        danceability = min(danceability, 0.20)
        speechiness = 0.03
    elif "meditat" in activity:
        # Meditation: Deep peacefulness, high acousticness & instrumentalness
        energy = 0.18
        tempo = 60.0
        acousticness = 0.90
        instrumentalness = 0.88
        danceability = 0.15
        speechiness = 0.03

    # 6. Time of Day Adjustment
    if time_of_day == "Night":
        energy = max(0.15, energy - 0.08)
        acousticness = min(0.95, acousticness + 0.08)
    elif time_of_day == "Morning" and activity not in ["sleeping", "meditation"]:
        energy = min(0.90, energy + 0.05)
        valence = min(0.90, valence + 0.05)

    return {
        "energy": round(energy, 2),
        "valence": round(valence, 2),
        "danceability": round(danceability, 2),
        "tempo": round(tempo, 1),
        "acousticness": round(acousticness, 2),
        "instrumentalness": round(instrumentalness, 2),
        "speechiness": round(speechiness, 2)
    }

class FeatureEngineer:
    """Feature Engineering Pipeline for Therapy AI Recommendation Model."""
    
    def extract_features(
        self,
        survey_data: Dict[str, Any],
        history_summary: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract clean feature dictionary, target audio features, and numerical vector for XGBoost model.
        """
        try:
            age = int(survey_data.get("age", 25))
        except (ValueError, TypeError):
            age = 25
            
        mood = str(survey_data.get("mood", "Tired"))
        try:
            stress = int(survey_data.get("stress", 5))
        except (ValueError, TypeError):
            stress = 5
            
        try:
            anxiety = int(survey_data.get("anxiety", 5))
        except (ValueError, TypeError):
            anxiety = 5
            
        sleep_quality = str(survey_data.get("sleep_quality", "Fair"))
        activity = str(survey_data.get("activity", "Relaxation"))
        fav_genre = str(survey_data.get("fav_genre", "Lo-fi"))
        language_pref = str(survey_data.get("language_pref", "English"))
        
        # Categorical Encodings
        mood_idx = encode_categorical(mood, MOODS)
        sleep_idx = encode_categorical(sleep_quality, SLEEP_QUALITIES)
        activity_idx = encode_categorical(activity, ACTIVITIES)
        genre_idx = encode_categorical(fav_genre, GENRES)
        lang_idx = encode_categorical(language_pref, SUPPORTED_LANGUAGES)
        time_of_day = get_time_of_day()

        # Derived Mental Health Metrics
        m_low = mood.lower()
        depression_val = 8.0 if any(k in m_low for k in ["sad", "depressed", "grief", "heartbreak"]) else 3.0
        sleep_val = 3.0 if sleep_quality.lower() == "poor" or any(k in m_low for k in ["sleep", "tired"]) else (5.0 if sleep_quality.lower() == "fair" else 8.0)
        energy_val = 9.0 if any(k in m_low for k in ["energetic", "motivated", "pumped"]) or any(k in activity.lower() for k in ["exercise", "workout"]) else (3.0 if any(k in m_low for k in ["tired", "sleep", "sad"]) else 6.0)
        
        # User Interaction History Signals
        fav_artists = (history_summary.get("favorite_artists", set()) if history_summary else set())
        recent_artists = (history_summary.get("recent_artists", set()) if history_summary else set())
        liked_tracks = (history_summary.get("liked_titles", set()) if history_summary else set())
        skipped_tracks = (history_summary.get("skipped_titles", set()) if history_summary else set())

        # Target clinical audio features based on user mental health state
        target_audio = get_target_audio_features(survey_data)

        # Numerical vector for ML prediction matching 11 clinical features for XGBoost
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
            "fav_artists": list(fav_artists) if isinstance(fav_artists, set) else fav_artists,
            "recent_artists": list(recent_artists) if isinstance(recent_artists, set) else recent_artists,
            "liked_tracks": list(liked_tracks) if isinstance(liked_tracks, set) else liked_tracks,
            "skipped_tracks": list(skipped_tracks) if isinstance(skipped_tracks, set) else skipped_tracks,
            "target_audio_features": target_audio,
            "feature_vector": feature_vector
        }
