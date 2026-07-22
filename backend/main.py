import os
import json
import pickle
import time
import numpy as np
import requests
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session, joinedload

from backend.database import (
    init_db,
    get_db,
    User,
    SurveyResponse,
    Recommendation,
    DailyJournal,
    FavoriteTrack
)
from datetime import datetime, timedelta
from backend.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    generate_reset_token,
    REMEMBER_ME_EXPIRE_DAYS
)

# Initialize Database on Startup
init_db()

# Load env variables manually to avoid python-dotenv dependency issues
def load_env():
    paths = [".env", "backend/.env", "../.env"]
    for path in paths:
        if os.path.exists(path):
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip()

load_env()

app = FastAPI(title="HarmonyRec API", version="1.0.0")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load machine learning model, scaler, and performance metrics
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, "models", "recommendation_model.pkl")
scaler_path = os.path.join(BASE_DIR, "models", "scaler.pkl")
metrics_path = os.path.join(BASE_DIR, "ml", "metrics.json")

try:
    with open(model_path, "rb") as f:
        recommendation_model = pickle.load(f)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    with open(metrics_path, "r") as f:
        model_metrics = json.load(f)
except Exception as e:
    print(f"Warning: Failed to load ML model or scaler. Error: {e}")
    recommendation_model = None
    scaler = None
    model_metrics = {}

# Mappings (must match ml_pipeline.py)
MOODS = ["Happy", "Sad", "Anxiety", "Angry", "Tired"]
SLEEP_QUALITIES = ["Good", "Fair", "Poor"]
ACTIVITIES = ["Studying", "Sleeping", "Meditation", "Exercise", "Relaxation"]
GENRES = ["Lo-fi", "Classical", "Nature Sounds", "Instrumental", "Pop"]
PLAYLISTS = ["playlist_1", "playlist_2", "playlist_3", "playlist_4", "playlist_5"]

PLAYLIST_THEME_MAPPING = {
    "playlist_1": {"name": "Lofi & Calm Pop", "query": "lofi hip hop chill study beats"},
    "playlist_2": {"name": "Healing Classical", "query": "peaceful classical sleep relax piano"},
    "playlist_3": {"name": "Meditation Nature Sounds", "query": "nature sounds meditation calming water"},
    "playlist_4": {"name": "Relaxing Instrumental", "query": "relaxing instrumental acoustic guitar chill"},
    "playlist_5": {"name": "Energetic Pop & Dance", "query": "workout pop dance hits energy"},
}

MOCK_LIBRARY = {
    "playlist_1": [
        {"title": "Weightless Lofi", "artist": "Lofi Dreamer", "duration": "3:20", "album_image": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=150&h=150&fit=crop", "play_url": "https://open.spotify.com/track/6UaR2v567dGg36329", "preview_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"},
        {"title": "Sunny Study", "artist": "Study Beats Collective", "duration": "2:45", "album_image": "https://images.unsplash.com/photo-1516280440614-37939bbacd6a?w=150&h=150&fit=crop", "play_url": "https://open.spotify.com/track/6UaR2v567dGg36329", "preview_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3"},
        {"title": "Midnight Coffee", "artist": "Chillhop Cafe", "duration": "3:02", "album_image": "https://images.unsplash.com/photo-1498038432885-c6f3f1b912ee?w=150&h=150&fit=crop", "play_url": "https://open.spotify.com/track/6UaR2v567dGg36329", "preview_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3"},
        {"title": "Raindrop Lounge", "artist": "Cloudy Day", "duration": "4:10", "album_image": "https://images.unsplash.com/photo-1486572788966-cfd3df1f5b42?w=150&h=150&fit=crop", "play_url": "https://open.spotify.com/track/6UaR2v567dGg36329", "preview_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3"}
    ],
    "playlist_2": [
        {"title": "Clair de Lune", "artist": "Claude Debussy", "duration": "5:05", "album_image": "https://images.unsplash.com/photo-1507838153414-b4b713384a76?w=150&h=150&fit=crop", "play_url": "https://open.spotify.com/track/6UaR2v567dGg36329", "preview_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3"},
        {"title": "Gymnopédie No. 1", "artist": "Erik Satie", "duration": "3:07", "album_image": "https://images.unsplash.com/photo-1507838153414-b4b713384a76?w=150&h=150&fit=crop", "play_url": "https://open.spotify.com/track/6UaR2v567dGg36329", "preview_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3"},
        {"title": "River Flows in You", "artist": "Yiruma", "duration": "3:05", "album_image": "https://images.unsplash.com/photo-1520523839897-bd0b52f945a0?w=150&h=150&fit=crop", "play_url": "https://open.spotify.com/track/6UaR2v567dGg36329", "preview_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3"},
        {"title": "Moonlight Sonata", "artist": "Ludwig van Beethoven", "duration": "6:12", "album_image": "https://images.unsplash.com/photo-1520523839897-bd0b52f945a0?w=150&h=150&fit=crop", "play_url": "https://open.spotify.com/track/6UaR2v567dGg36329", "preview_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3"}
    ],
    "playlist_3": [
        {"title": "Deep Forest Rain", "artist": "Nature Soundscapes", "duration": "8:00", "album_image": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=150&h=150&fit=crop", "play_url": "https://open.spotify.com/track/6UaR2v567dGg36329", "preview_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-9.mp3"},
        {"title": "Ocean Waves & Wind", "artist": "Coastal Therapy", "duration": "7:30", "album_image": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=150&h=150&fit=crop", "play_url": "https://open.spotify.com/track/6UaR2v567dGg36329", "preview_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3"},
        {"title": "Tibetan Healing Bowls", "artist": "Zen Meditation", "duration": "6:15", "album_image": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=150&h=150&fit=crop", "play_url": "https://open.spotify.com/track/6UaR2v567dGg36329", "preview_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-11.mp3"}
    ],
    "playlist_4": [
        {"title": "Acoustic Campfire", "artist": "Guitar Relax", "duration": "3:40", "album_image": "https://images.unsplash.com/photo-1510915361894-db8b60106cb1?w=150&h=150&fit=crop", "play_url": "https://open.spotify.com/track/6UaR2v567dGg36329", "preview_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-12.mp3"},
        {"title": "Sunset Horizon", "artist": "Instrumental Chill", "duration": "4:05", "album_image": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=150&h=150&fit=crop", "play_url": "https://open.spotify.com/track/6UaR2v567dGg36329", "preview_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-13.mp3"},
        {"title": "Morning Breeze", "artist": "Acoustic Duo", "duration": "3:15", "album_image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=150&h=150&fit=crop", "play_url": "https://open.spotify.com/track/6UaR2v567dGg36329", "preview_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-14.mp3"}
    ],
    "playlist_5": [
        {"title": "Summer Anthem", "artist": "Dance Club", "duration": "3:10", "album_image": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=150&h=150&fit=crop", "play_url": "https://open.spotify.com/track/6UaR2v567dGg36329", "preview_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-15.mp3"},
        {"title": "Good Times Pop", "artist": "Pop Hits", "duration": "2:55", "album_image": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=150&h=150&fit=crop", "play_url": "https://open.spotify.com/track/6UaR2v567dGg36329", "preview_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-16.mp3"},
        {"title": "Electric Workout", "artist": "Synth Pop Collective", "duration": "3:30", "album_image": "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=150&h=150&fit=crop", "play_url": "https://open.spotify.com/track/6UaR2v567dGg36329", "preview_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"}
    ]
}

# Spotify API Client Credentials Flow Token Cache
_spotify_token_cache = {
    "token": None,
    "expires_at": 0
}

def get_spotify_access_token(client_id: str, client_secret: str) -> Optional[str]:
    global _spotify_token_cache
    current_time = time.time()
    
    # Check if we have a valid cached token (with a 60-second buffer)
    if _spotify_token_cache["token"] and _spotify_token_cache["expires_at"] > current_time + 60:
        return _spotify_token_cache["token"]
        
    try:
        # Get access token
        auth_url = "https://accounts.spotify.com/api/token"
        response = requests.post(
            auth_url,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
            timeout=5
        )
        if response.status_code != 200:
            print(f"Spotify authentication failed. Status code: {response.status_code}")
            return None
            
        data = response.json()
        token = data.get("access_token")
        expires_in = data.get("expires_in", 3600)
        
        # Cache token with its expiration time
        _spotify_token_cache["token"] = token
        _spotify_token_cache["expires_at"] = current_time + expires_in
        return token
    except Exception as e:
        print(f"Exception during Spotify token fetch: {e}")
        return None

def fetch_spotify_tracks(query: str, limit: int = 8) -> List[dict]:
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("Spotify credentials missing in .env. Falling back to Mock Library.")
        return []
        
    try:
        # 1. Get access token (cached)
        token = get_spotify_access_token(client_id, client_secret)
        if not token:
            return []
            
        # 2. Search tracks
        search_url = "https://api.spotify.com/v1/search"
        headers = {"Authorization": f"Bearer {token}"}
        params = {"q": query, "type": "track", "limit": limit}
        
        search_resp = requests.get(search_url, headers=headers, params=params, timeout=5)
        if search_resp.status_code != 200:
            print(f"Spotify track search failed. Status code: {search_resp.status_code}")
            return []
            
        items = search_resp.json().get("tracks", {}).get("items", [])
        
        tracks = []
        for item in items:
            # Format duration from ms to mm:ss
            duration_ms = item.get("duration_ms", 0)
            minutes = duration_ms // 60000
            seconds = (duration_ms % 60000) // 1000
            duration_str = f"{minutes}:{seconds:02d}"
            
            # Album image
            images = item.get("album", {}).get("images", [])
            album_img = images[0].get("url") if images else "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=150&h=150&fit=crop"
            
            tracks.append({
                "title": item.get("name"),
                "artist": ", ".join([a.get("name") for a in item.get("artists", [])]),
                "duration": duration_str,
                "album_image": album_img,
                "play_url": item.get("external_urls", {}).get("spotify"),
                "preview_url": item.get("preview_url") # Note: Spotify preview_url is sometimes null
            })
            
        return tracks
    except Exception as e:
        print(f"Exception during Spotify fetch: {e}")
        return []

# Pydantic Schemas
class UserSignup(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    fav_genre: Optional[str] = "Lo-fi"

class UserLogin(BaseModel):
    username: str
    password: str
    remember_me: Optional[bool] = False

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    fav_genre: Optional[str] = "Lo-fi"

class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    fav_genre: Optional[str] = "Lo-fi"
    language_pref: Optional[str] = "English"
    default_activity: Optional[str] = "Relaxation"
    created_at: Optional[str] = None

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    fav_genre: Optional[str] = "Lo-fi"
    language_pref: Optional[str] = "English"
    default_activity: Optional[str] = "Relaxation"

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    email_or_username: str

class ResetPasswordSubmit(BaseModel):
    reset_token: str
    new_password: str

class SurveySubmit(BaseModel):
    age: int
    gender: Optional[str] = "Prefer not to say"
    mood: str
    stress: int
    sleep_quality: str
    anxiety: int
    fav_genre: str
    language_pref: str
    activity: str

class FeedbackSubmit(BaseModel):
    survey_id: int
    rating: int
    helped: bool

class JournalSubmit(BaseModel):
    mood: str
    stress: int
    journal_text: str

class FavoriteToggle(BaseModel):
    title: str
    artist: str
    duration: str
    album_image: Optional[str] = None
    play_url: Optional[str] = None
    preview_url: Optional[str] = None

class ChatbotMessage(BaseModel):
    message: str
    current_mood: Optional[str] = "None"


@app.post("/api/auth/signup", response_model=TokenResponse)
def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter((User.username == user_data.username) | (User.email == user_data.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or Email already registered"
        )
        
    hashed_pwd = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_pwd,
        full_name=user_data.full_name,
        fav_genre=user_data.fav_genre or "Lo-fi"
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    token = create_access_token(data={"sub": new_user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": new_user.username,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "fav_genre": new_user.fav_genre
    }

@app.post("/api/auth/login", response_model=TokenResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    # Support login via username OR email
    user = db.query(User).filter((User.username == login_data.username) | (User.email == login_data.username)).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password"
        )
        
    expires_delta = timedelta(days=REMEMBER_ME_EXPIRE_DAYS) if login_data.remember_me else None
    token = create_access_token(data={"sub": user.username}, expires_delta=expires_delta)
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "fav_genre": user.fav_genre or "Lo-fi"
    }

@app.get("/api/auth/me", response_model=UserProfileResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "fav_genre": current_user.fav_genre or "Lo-fi",
        "language_pref": current_user.language_pref or "English",
        "default_activity": current_user.default_activity or "Relaxation",
        "created_at": current_user.created_at.strftime("%Y-%m-%d %H:%M") if current_user.created_at else None
    }

@app.put("/api/auth/profile", response_model=UserProfileResponse)
def update_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if profile_data.email and profile_data.email != current_user.email:
        existing = db.query(User).filter(User.email == profile_data.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email is already taken by another account.")
        current_user.email = profile_data.email

    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name
    if profile_data.fav_genre is not None:
        current_user.fav_genre = profile_data.fav_genre
    if profile_data.language_pref is not None:
        current_user.language_pref = profile_data.language_pref
    if profile_data.default_activity is not None:
        current_user.default_activity = profile_data.default_activity

    db.commit()
    db.refresh(current_user)

    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "fav_genre": current_user.fav_genre or "Lo-fi",
        "language_pref": current_user.language_pref or "English",
        "default_activity": current_user.default_activity or "Relaxation",
        "created_at": current_user.created_at.strftime("%Y-%m-%d %H:%M") if current_user.created_at else None
    }

@app.post("/api/auth/change-password")
def change_password(
    pwd_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(pwd_data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    
    if len(pwd_data.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters.")

    current_user.hashed_password = get_password_hash(pwd_data.new_password)
    db.commit()
    return {"status": "success", "message": "Password updated successfully!"}

@app.post("/api/auth/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter((User.email == req.email_or_username) | (User.username == req.email_or_username)).first()
    if not user:
        # Avoid user enumeration attack; return success message anyway
        return {"status": "success", "message": "If an account matching the details exists, password reset instructions have been generated."}
    
    reset_tok = generate_reset_token()
    user.reset_token = reset_tok
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()

    return {
        "status": "success",
        "message": "Password reset token generated successfully.",
        "reset_token": reset_tok
    }

@app.post("/api/auth/reset-password")
def reset_password(req: ResetPasswordSubmit, db: Session = Depends(get_db)):
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    user = db.query(User).filter(User.reset_token == req.reset_token).first()
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    user.hashed_password = get_password_hash(req.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return {"status": "success", "message": "Password reset successfully! You can now log in with your new password."}

@app.post("/api/recommend/survey")
def submit_survey(survey: SurveySubmit, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if recommendation_model is None or scaler is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction model or scaler is not loaded on backend."
        )
        
    # Map categoricals to indexes
    try:
        mood_idx = MOODS.index(survey.mood)
    except ValueError:
        mood_idx = 0
        
    try:
        sleep_idx = SLEEP_QUALITIES.index(survey.sleep_quality)
    except ValueError:
        sleep_idx = 0
        
    try:
        activity_idx = ACTIVITIES.index(survey.activity)
    except ValueError:
        activity_idx = 0
        
    try:
        genre_idx = GENRES.index(survey.fav_genre)
    except ValueError:
        genre_idx = 0

    # Features must match ML pipeline features: ["Age", "Mood", "Stress", "SleepQuality", "Anxiety", "Activity", "FavGenre"]
    feature_arr = np.array([[
        survey.age,
        mood_idx,
        survey.stress,
        sleep_idx,
        survey.anxiety,
        activity_idx,
        genre_idx
    ]], dtype=float)
    
    # Scale features
    feature_scaled = scaler.transform(feature_arr)
    
    # Predict playlist
    pred_idx = recommendation_model.predict(feature_scaled)[0]
    result_playlist = PLAYLISTS[int(pred_idx)]
    
    # Create DB entry
    response_record = SurveyResponse(
        user_id=current_user.id,
        age=survey.age,
        gender=survey.gender,
        mood=survey.mood,
        stress=survey.stress,
        sleep_quality=survey.sleep_quality,
        anxiety=survey.anxiety,
        fav_genre=survey.fav_genre,
        language_pref=survey.language_pref,
        activity=survey.activity,
        result_playlist=result_playlist
    )
    db.add(response_record)
    db.commit()
    db.refresh(response_record)
    
    # Fetch tracks from Spotify or load mock library
    theme_info = PLAYLIST_THEME_MAPPING[result_playlist]
    playlist_name = theme_info["name"]
    query = theme_info["query"]
    
    tracks = fetch_spotify_tracks(query, limit=8)
    if not tracks:
        print(f"Fetching from Spotify failed or credentials missing. Loading mock tracks for {result_playlist}.")
        tracks = MOCK_LIBRARY.get(result_playlist, MOCK_LIBRARY["playlist_1"])
        
    # Store recommendation
    rec_record = Recommendation(
        survey_id=response_record.id,
        genre=playlist_name,
        tracks=json.dumps(tracks)
    )
    db.add(rec_record)
    db.commit()
    
    return {
        "survey_id": response_record.id,
        "result_state": playlist_name,
        "playlist_key": result_playlist,
        "tracks": tracks,
        "timestamp": response_record.timestamp.isoformat()
    }

@app.post("/api/recommend/feedback")
def submit_feedback(feedback: FeedbackSubmit, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verify survey response belongs to the user
    survey = db.query(SurveyResponse).filter(SurveyResponse.id == feedback.survey_id, SurveyResponse.user_id == current_user.id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey response not found")
        
    rec = db.query(Recommendation).filter(Recommendation.survey_id == survey.id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation details not found")
        
    rec.rating = feedback.rating
    rec.helped = feedback.helped
    db.commit()
    return {"status": "success", "message": "Feedback submitted successfully"}

@app.get("/api/recommend/history")
def get_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    surveys = (
        db.query(SurveyResponse)
        .options(joinedload(SurveyResponse.recommendation))
        .filter(SurveyResponse.user_id == current_user.id)
        .order_by(SurveyResponse.timestamp.asc())
        .all()
    )
    
    history_list = []
    for s in surveys:
        rec = s.recommendation
        tracks = json.loads(rec.tracks) if rec else []
        history_list.append({
            "id": s.id,
            "age": s.age,
            "gender": s.gender,
            "mood": s.mood,
            "stress": s.stress,
            "sleep_quality": s.sleep_quality,
            "anxiety": s.anxiety,
            "fav_genre": s.fav_genre,
            "language_pref": s.language_pref,
            "activity": s.activity,
            "result_state": rec.genre if rec else "Calming",
            "playlist_key": s.result_playlist,
            "timestamp": s.timestamp.isoformat(),
            "tracks": tracks,
            "rating": rec.rating if rec else None,
            "helped": rec.helped if rec else None
        })
        
    return history_list

@app.get("/api/journal")
def get_journals(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    entries = db.query(DailyJournal).filter(DailyJournal.user_id == current_user.id).order_by(DailyJournal.timestamp.desc()).all()
    return [{
        "id": e.id,
        "mood": e.mood,
        "stress": e.stress,
        "journal_text": e.journal_text,
        "timestamp": e.timestamp.isoformat()
    } for e in entries]

@app.post("/api/journal")
def add_journal(entry: JournalSubmit, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_entry = DailyJournal(
        user_id=current_user.id,
        mood=entry.mood,
        stress=entry.stress,
        journal_text=entry.journal_text
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return {
        "id": new_entry.id,
        "mood": new_entry.mood,
        "stress": new_entry.stress,
        "journal_text": new_entry.journal_text,
        "timestamp": new_entry.timestamp.isoformat()
    }

@app.get("/api/favorites")
def get_favorites(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    favs = db.query(FavoriteTrack).filter(FavoriteTrack.user_id == current_user.id).order_by(FavoriteTrack.timestamp.desc()).all()
    return [{
        "title": f.title,
        "artist": f.artist,
        "duration": f.duration,
        "album_image": f.album_image,
        "play_url": f.play_url,
        "preview_url": f.preview_url
    } for f in favs]

@app.post("/api/favorites/toggle")
def toggle_favorite(track: FavoriteToggle, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(FavoriteTrack).filter(
        FavoriteTrack.user_id == current_user.id,
        FavoriteTrack.title == track.title,
        FavoriteTrack.artist == track.artist
    ).first()
    
    if existing:
        db.delete(existing)
        db.commit()
        return {"status": "removed", "message": f"Removed '{track.title}' from favorites"}
    else:
        new_fav = FavoriteTrack(
            user_id=current_user.id,
            title=track.title,
            artist=track.artist,
            duration=track.duration,
            album_image=track.album_image,
            play_url=track.play_url,
            preview_url=track.preview_url
        )
        db.add(new_fav)
        db.commit()
        return {"status": "added", "message": f"Added '{track.title}' to favorites"}

@app.post("/api/chatbot")
def chat_bot(message_data: ChatbotMessage):
    msg = message_data.message.lower()
    mood = message_data.current_mood
    
    # Simple supportive rule-based responses
    advice = ""
    suggested_playlist = ""
    
    if "stress" in msg or "anxious" in msg or "anxiety" in msg or "worry" in msg:
        advice = "I hear you. High anxiety or stress triggers the body's fight-or-flight response. I suggest trying a 5-minute grounding breathing exercise (inhale 4s, hold 4s, exhale 4s). Focus on the physical sensation of breathing."
        suggested_playlist = "Nature Sounds & Meditation or Calming Instrumental playlists"
    elif "sad" in msg or "depressed" in msg or "lonely" in msg or "mood" in msg:
        advice = "I'm sorry you are feeling low right now. Be gentle with yourself. Sometimes minor activities, like stretching or looking out the window, can help break the inertia. Listening to light Lofi or uplifting songs can provide a gentle mood boost."
        suggested_playlist = "Lofi & Calm Pop playlist"
    elif "sleep" in msg or "insomnia" in msg or "tired" in msg or "exhausted" in msg:
        advice = "Good sleep hygiene is essential. Ensure your screen brightness is low and try a cognitive shuffle exercise or listen to ambient frequencies. Keeping a slow, rhythmic classical track in the background helps lower heart rate."
        suggested_playlist = "Healing Classical playlist"
    elif "focus" in msg or "study" in msg or "work" in msg or "concentrate" in msg:
        advice = "To optimize concentration, minimize notification distractions and set a Pomodoro timer (25 minutes focus, 5 minutes rest). Binaural beats or ambient lofi are proven to enhance spatial reasoning without cognitive loading."
        suggested_playlist = "Lofi & Calm Pop playlist"
    elif "exercise" in msg or "workout" in msg or "energy" in msg:
        advice = "Awesome! Physical exercise releases endorphins. Rhythmic tempos above 120 BPM naturally synchronize with your stride frequency to elevate athletic output."
        suggested_playlist = "Energetic Pop & Dance playlist"
    else:
        # Default response based on user's current diagnostic mood if available
        if mood == "Sad":
            advice = "I see your mood is set to Sad. I highly recommend taking a slow walk or letting some classical piano music play in the background. Remember, it's okay to feel down; give yourself time."
            suggested_playlist = "Healing Classical playlist"
        elif mood == "Anxiety" or mood == "Angry":
            advice = "To soothe anxious or tense feelings, try the 5-4-3-2-1 grounding technique: Name 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, and 1 you can taste."
            suggested_playlist = "Nature Sounds & Meditation playlist"
        elif mood == "Tired":
            advice = "If you're feeling exhausted, listen to soft acoustic instrumentals and allow yourself a structured 20-minute power nap."
            suggested_playlist = "Relaxing Instrumental playlist"
        else:
            advice = "Hi there! I'm your wellness chatbot. You can ask me for wellness tips, breathing exercises, focus advice, or sleep recommendations. How can I support your health today?"
            suggested_playlist = "Lofi & Calm Pop or Instrumental playlists"
            
    reply = f"{advice}\n\n**Recommendation**: Try switching your audio queue to the **{suggested_playlist}**."
    return {"reply": reply}

@app.get("/api/analytics/model-comparison")
def get_model_comparison(current_user: User = Depends(get_current_user)):
    return model_metrics

@app.get("/api/spotify/status")
def get_spotify_status():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    return {
        "connected": bool(client_id and client_secret),
        "client_id": client_id[:6] + "..." if client_id else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
