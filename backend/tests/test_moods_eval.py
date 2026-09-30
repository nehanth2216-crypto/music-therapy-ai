from backend.ml.recommender import hybrid_recommender

moods = [
    "Happy",
    "Calm",
    "Romantic",
    "Sad",
    "Anxious / Stress",
    "Energetic",
    "Motivated",
    "Sleep / Relaxing"
]

for m in moods:
    survey = {
        "mood": m,
        "language": "Telugu",
        "selected_language": "Telugu",
        "age": 25,
        "stress_level": 5,
        "anxiety_level": 5,
        "activity": "Relaxation"
    }
    res = hybrid_recommender.get_recommendations(survey, limit=5)
    tracks = res.get("tracks", [])
    tc = res.get("predicted_therapy_category")
    print(f"\n=== MOOD: {m} (Predicted Therapy: {tc}) ===")
    for i, t in enumerate(tracks[:4]):
        print(f"  {i+1}. {t.get('title')} - {t.get('artist')} [mood={t.get('mood')}, cat={t.get('therapy_category')}, score={t.get('match_score')}]")
