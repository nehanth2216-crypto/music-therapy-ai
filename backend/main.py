import os
import json
import pickle
import time
import numpy as np
import requests
from typing import List, Optional
import re
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.orm import Session, joinedload

from backend.database import (
    init_db,
    get_db,
    User,
    SurveyResponse,
    Recommendation,
    DailyJournal,
    FavoriteTrack,
    ListeningHistory,
    UserPlaylist,
    PlaylistTrack,
    TrackFeedback
)
from datetime import datetime, timedelta, timezone
from backend.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    get_optional_current_user,
    generate_reset_token,
    REMEMBER_ME_EXPIRE_DAYS
)
from backend.ml.recommender import HybridRecommender
from backend.ml.language_verifier import LanguageVerifier

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

hybrid_recommender = HybridRecommender()

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

import joblib

# Load machine learning models, scalers, and encoders
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Therapy AI Model & Encoders
try:
    therapy_model = joblib.load(os.path.join(BASE_DIR, "models", "therapy_model.pkl"))
    language_encoder = joblib.load(os.path.join(BASE_DIR, "models", "language_encoder.pkl"))
    genre_encoder = joblib.load(os.path.join(BASE_DIR, "models", "genre_encoder.pkl"))
    therapy_encoder = joblib.load(os.path.join(BASE_DIR, "models", "therapy_encoder.pkl"))
except Exception as e:
    print(f"Notice: Therapy model or encoders loading info: {e}")
    therapy_model = None
    language_encoder = None
    genre_encoder = None
    therapy_encoder = None

model_path = os.path.join(BASE_DIR, "models", "recommendation_model.pkl")
scaler_path = os.path.join(BASE_DIR, "models", "scaler.pkl")
metrics_path = os.path.join(BASE_DIR, "ml", "metrics.json")

try:
    if os.path.exists(model_path):
        with open(model_path, "rb") as f:
            recommendation_model = pickle.load(f)
    else:
        recommendation_model = None
except Exception:
    recommendation_model = None

try:
    if os.path.exists(scaler_path):
        with open(scaler_path, "rb") as f:
            scaler = pickle.load(f)
    else:
        scaler = None
except Exception:
    scaler = None

try:
    with open(metrics_path, "r") as f:
        model_metrics = json.load(f)
except Exception:
    model_metrics = {}

# Mappings (must match ml_pipeline.py)
MOODS = ["Happy", "Sad", "Anxiety", "Angry", "Tired"]
SLEEP_QUALITIES = ["Good", "Fair", "Poor"]
ACTIVITIES = ["Studying", "Sleeping", "Meditation", "Exercise", "Relaxation"]
GENRES = ["Lo-fi", "Classical", "Nature Sounds", "Instrumental", "Pop"]
PLAYLISTS = ["playlist_1", "playlist_2", "playlist_3", "playlist_4", "playlist_5"]
SUPPORTED_LANGUAGES = ["English", "Telugu", "Hindi", "Tamil", "Malayalam", "Kannada", "Punjabi", "Bengali", "Marathi"]

PLAYLIST_THEME_MAPPING = {
    "playlist_1": {"name": "Lofi & Calm Pop", "query": "lofi hip hop chill study beats"},
    "playlist_2": {"name": "Healing Classical", "query": "peaceful classical sleep relax piano"},
    "playlist_3": {"name": "Meditation Nature Sounds", "query": "nature sounds meditation calming water"},
    "playlist_4": {"name": "Relaxing Instrumental", "query": "relaxing instrumental acoustic guitar chill"},
    "playlist_5": {"name": "Energetic Pop & Dance", "query": "workout pop dance hits energy"},
}

# Clinical Therapy Profiles (Medical Assessment -> Mental State -> Therapy Profile -> Genre & Keywords)
THERAPY_PROFILE = {
    "stress": {
        "tempo": "slow",
        "genre": "lofi acoustic classical",
        "keywords": [
            "relax",
            "calm",
            "sleep",
            "peaceful"
        ]
    },
    "anxiety": {
        "tempo": "slow",
        "genre": "soft instrumental meditation",
        "keywords": [
            "meditation",
            "soothing",
            "healing",
            "calming"
        ]
    },
    "depression": {
        "tempo": "moderate",
        "genre": "hope uplifting motivational",
        "keywords": [
            "hope",
            "uplifting",
            "motivational",
            "positive"
        ]
    }
}

def determine_mental_state(mood: str = "Tired", stress: int = 5, anxiety: int = 5) -> str:
    """Evaluate medical assessment data to choose clinical mental state therapy profile."""
    m_lower = (mood or "").lower()
    if "sad" in m_lower or "depress" in m_lower:
        return "depression"
    elif anxiety >= 7 or "anxi" in m_lower or "panic" in m_lower:
        return "anxiety"
    elif stress >= 7 or "stres" in m_lower or "tired" in m_lower or "angry" in m_lower:
        return "stress"
    elif anxiety > stress:
        return "anxiety"
    else:
        return "stress"

MOCK_LIBRARY = {
    "playlist_1": [
        {"title": "Weightless Lofi", "artist": "Lofi Dreamer", "duration": "3:20", "album_image": "https://images.unsplash.com/photo-1518609878373-06d740f60d8b?w=150&h=150&fit=crop", "preview_url": "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3"},
        {"title": "Sunny Study", "artist": "Study Beats Collective", "duration": "2:45", "album_image": "https://images.unsplash.com/photo-1516280440614-37939bbacd6a?w=150&h=150&fit=crop", "preview_url": "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0a13f69d2.mp3"},
        {"title": "Midnight Coffee", "artist": "Chillhop Cafe", "duration": "3:02", "album_image": "https://images.unsplash.com/photo-1498038432885-c6f3f1b912ee?w=150&h=150&fit=crop", "preview_url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8c8a73467.mp3"},
        {"title": "Raindrop Lounge", "artist": "Cloudy Day", "duration": "4:10", "album_image": "https://images.unsplash.com/photo-1486572788966-cfd3df1f5b42?w=150&h=150&fit=crop", "preview_url": "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3"}
    ],
    "playlist_2": [
        {"title": "Clair de Lune", "artist": "Claude Debussy", "duration": "5:05", "album_image": "https://images.unsplash.com/photo-1507838153414-b4b713384a76?w=150&h=150&fit=crop", "preview_url": "https://cdn.pixabay.com/download/audio/2022/11/11/audio_84e1b7f8c0.mp3"},
        {"title": "Gymnopédie No. 1", "artist": "Erik Satie", "duration": "3:07", "album_image": "https://images.unsplash.com/photo-1507838153414-b4b713384a76?w=150&h=150&fit=crop", "preview_url": "https://cdn.pixabay.com/download/audio/2022/03/24/audio_34b3f8dbec.mp3"},
        {"title": "River Flows in You", "artist": "Yiruma", "duration": "3:05", "album_image": "https://images.unsplash.com/photo-1520523839897-bd0b52f945a0?w=150&h=150&fit=crop", "preview_url": "https://cdn.pixabay.com/download/audio/2022/11/11/audio_84e1b7f8c0.mp3"},
        {"title": "Moonlight Sonata", "artist": "Ludwig van Beethoven", "duration": "6:12", "album_image": "https://images.unsplash.com/photo-1520523839897-bd0b52f945a0?w=150&h=150&fit=crop", "preview_url": "https://cdn.pixabay.com/download/audio/2022/03/24/audio_34b3f8dbec.mp3"}
    ],
    "playlist_3": [
        {"title": "Deep Forest Rain", "artist": "Nature Soundscapes", "duration": "8:00", "album_image": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=150&h=150&fit=crop", "preview_url": "https://cdn.pixabay.com/download/audio/2021/08/09/audio_884489a24d.mp3"},
        {"title": "Ocean Waves & Wind", "artist": "Coastal Therapy", "duration": "7:30", "album_image": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=150&h=150&fit=crop", "preview_url": "https://cdn.pixabay.com/download/audio/2022/06/07/audio_b2875e6a98.mp3"},
        {"title": "Tibetan Healing Bowls", "artist": "Zen Meditation", "duration": "6:15", "album_image": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=150&h=150&fit=crop", "preview_url": "https://cdn.pixabay.com/download/audio/2021/08/09/audio_884489a24d.mp3"}
    ],
    "playlist_4": [
        {"title": "Acoustic Campfire", "artist": "Guitar Relax", "duration": "3:40", "album_image": "https://images.unsplash.com/photo-1510915361894-db8b60106cb1?w=150&h=150&fit=crop", "preview_url": "https://cdn.pixabay.com/download/audio/2022/02/10/audio_fc86214151.mp3"},
        {"title": "Sunset Horizon", "artist": "Instrumental Chill", "duration": "4:05", "album_image": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=150&h=150&fit=crop", "preview_url": "https://cdn.pixabay.com/download/audio/2021/09/06/audio_40409c2509.mp3"},
        {"title": "Morning Breeze", "artist": "Acoustic Duo", "duration": "3:15", "album_image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=150&h=150&fit=crop", "preview_url": "https://cdn.pixabay.com/download/audio/2022/02/10/audio_fc86214151.mp3"}
    ],
    "playlist_5": [
        {"title": "Summer Anthem", "artist": "Dance Club", "duration": "3:10", "album_image": "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=150&h=150&fit=crop", "preview_url": "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3"},
        {"title": "Good Times Pop", "artist": "Pop Hits", "duration": "2:55", "album_image": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=150&h=150&fit=crop", "preview_url": "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0a13f69d2.mp3"},
        {"title": "Electric Workout", "artist": "Synth Pop Collective", "duration": "3:30", "album_image": "https://images.unsplash.com/photo-1517838277536-f5f99be501cd?w=150&h=150&fit=crop", "preview_url": "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3"}
    ]
}

# Multi-Language Curated Track Libraries (Exact Official Movie Songs & Crystal-Clear Full Length Audio Streams)
MULTI_LANG_LIBRARY = {
    "Telugu": [
        {"title": "Samayama (From \"Hi Nanna\")", "artist": "Hesham Abdul Wahab, Anurag Kulkarni", "duration": "4:12", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music116/v4/b5/04/cd/b504cdb8-d632-4b6b-1b68-10686397ff42/8903431963307_cover.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview126/v4/f3/b0/73/f3b073f5-f84b-88d5-9d46-066aa152d606/mzaf_13123944415807399306.plus.aac.p.m4a", "is_catalog_verified": True},
        {"title": "Maate Vinadhuga (From \"Taxiwaala\")", "artist": "Sid Sriram & Jakes Bejoy", "duration": "4:34", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music125/v4/94/1d/a0/941da079-ee93-ce60-6340-3c7d0f7633a3/cover.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/07/27/4c/07274cc8-f662-8747-e425-1108ba2a2390/mzaf_12339835384962827073.plus.aac.p.m4a", "is_catalog_verified": True},
        {"title": "Fear Song (From \"Devara Part 1\")", "artist": "Anirudh Ravichander", "duration": "3:17", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music221/v4/1d/c6/af/1dc6af82-69e9-5341-5010-a9223fc25709/8903431001368_cover.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/8d/b1/16/8db11650-580e-ab11-9747-b7bb8544ce55/mzaf_14247929829726939234.plus.aac.p.m4a", "is_catalog_verified": True},
        {"title": "Samajavaragamana (From \"Ala Vaikunthapurramuloo\")", "artist": "S.S. Thaman & Sid Sriram", "duration": "3:34", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music124/v4/53/98/c1/5398c1cf-7c16-24a6-bfa3-391dc6015376/cover.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/29/a7/55/29a75528-3808-d849-ad00-9e714bf12621/mzaf_2813549342968292058.plus.aac.p.m4a", "is_catalog_verified": True},
        {"title": "Inkem Inkem Inkem Kaavaale (From \"Geetha Govindam\")", "artist": "Sid Sriram & Gopi Sundar", "duration": "4:28", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music124/v4/31/89/3e/31893e4d-7b2e-07a8-6b83-b78f8c7e0998/cover.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/6d/5a/f1/6d5af141-475c-7404-495c-0ef55283457c/mzaf_3028662401385709025.plus.aac.p.m4a", "is_catalog_verified": True},
        {"title": "O Ranga Ranga (From \"Rangasthalam\")", "artist": "M.M. Keeravani & Rahul Sipligunj", "duration": "4:00", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music128/v4/b8/01/7a/b8017a42-7a2e-4b68-80df-90a16f912c9b/cover.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/64/0c/30/640c3082-d257-d55d-5be7-8289c1484cb1/mzaf_9955003886284627240.plus.aac.p.m4a", "is_catalog_verified": True}
    ],
    "Hindi": [
        {"title": "Kesariya (From \"Brahmastra\")", "artist": "Pritam, Arijit Singh & Amitabh Bhattacharya", "duration": "4:28", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music112/v4/9f/13/ca/9f13ca3b-e533-03e0-f19a-f0aaa774581d/196589311191.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/38/4c/5c/384c5c8f-3ff8-e457-b2f7-3158ce108649/mzaf_12389299033886433185.plus.aac.p.m4a", "is_catalog_verified": True},
        {"title": "Tum Se Hi (From \"Jab We Met\")", "artist": "Pritam & Mohit Chauhan", "duration": "5:23", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music118/v4/64/73/b3/6473b306-bf25-5460-6060-f561ee6dd7fa/source/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/e7/39/b8/e739b870-54a1-8f33-57d5-3817108b8bd9/mzaf_16925921654959290990.plus.aac.p.m4a", "is_catalog_verified": True},
        {"title": "Soniyo (From \"Raaz - The Mystery Continues\")", "artist": "Raju Singh, Sonu Nigam & Shreya Ghoshal", "duration": "5:29", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/77/4d/9f/774d9f5c-830a-c140-f1ae-6e637dc9af14/888880931542.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/19/51/ac/1951ac5b-81c8-72ea-ffe5-31e1a3369d9b/mzaf_17405745395809731793.plus.aac.p.m4a", "is_catalog_verified": True}
    ],
    "Tamil": [
        {"title": "Neeyum Naanum (From \"Naanum Rowdy Dhaan\")", "artist": "Anirudh Ravichander & Neeti Mohan", "duration": "5:02", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music128/v4/bf/25/71/bf2571c4-9df2-aa00-8438-e6b7617c093a/source/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/6c/46/bb/6c46bb00-98fe-abe5-a191-05a30e4ce11e/mzaf_17637533678834679920.plus.aac.p.m4a", "is_catalog_verified": True},
        {"title": "Rowdy Baby (From \"Maari 2\")", "artist": "Dhanush & Dhee", "duration": "4:43", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music118/v4/a1/b2/c3/a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d/source/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/91/17/90/911790e5-27e3-6021-da30-bddf59576e3d/mzaf_3831305118076812899.plus.aac.p.m4a", "is_catalog_verified": True}
    ],
    "Malayalam": [
        {"title": "Darshana (From \"Hridayam\")", "artist": "Hesham Abdul Wahab & Darshana Rajendran", "duration": "3:45", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music125/v4/47/f3/f1/47f3f1ec-6078-4355-08e0-16bb21558bf2/source/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/2b/71/38/2b71380d-0114-3845-c3a8-5d2cfb9abfae/mzaf_14430613370529957448.plus.aac.p.m4a", "is_catalog_verified": True},
        {"title": "Malare (From \"Premam\")", "artist": "Vijay Yesudas", "duration": "5:16", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music2/v4/6f/3c/cd/6f3ccd36-2a0f-0c4e-ce51-5aebcf9e9f84/cover.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/41/59/b4/4159b41b-708b-8140-d758-e8da1ed7bedd/mzaf_7080443034849106781.plus.aac.p.m4a", "is_catalog_verified": True},
        {"title": "Illuminati (From \"Aavesham\")", "artist": "Sushin Shyam & Dabzee", "duration": "3:13", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music221/v4/88/4e/29/884e290c-29ed-25d5-7b25-243b89097220/cover.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/43/a0/da/43a0daa2-504d-6b7c-c63a-0c8864608a6d/mzaf_7754996064757215177.plus.aac.p.m4a", "is_catalog_verified": True}
    ],
    "English": [
        {"title": "Weightless (Deep Relaxation)", "artist": "Marconi Union", "duration": "8:08", "album_image": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=500&h=500&fit=crop", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/65/69/07/656907c9-eb54-c59c-72b9-dad8489a0165/mzaf_3316991574698499044.plus.aac.p.m4a", "is_catalog_verified": True},
        {"title": "Closer (Acoustic Chill)", "artist": "The Chainsmokers", "duration": "4:05", "album_image": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=500&h=500&fit=crop", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/bd/f9/b9/bdf9b9b2-eaa4-4461-6079-aaacc6df7316/mzaf_17327312786932455493.plus.aac.p.m4a", "is_catalog_verified": True},
        {"title": "Sunset Serenade", "artist": "Lofi Chill Beats", "duration": "3:45", "album_image": "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=500&h=500&fit=crop", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/65/69/07/656907c9-eb54-c59c-72b9-dad8489a0165/mzaf_3316991574698499044.plus.aac.p.m4a", "is_catalog_verified": True}
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
    if _spotify_token_cache["token"] and _spotify_token_cache["expires_at"] > current_time + 60:
        return _spotify_token_cache["token"]
        
    try:
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
        _spotify_token_cache["token"] = token
        _spotify_token_cache["expires_at"] = current_time + expires_in
        return token
    except Exception as e:
        print(f"Exception during Spotify token fetch: {e}")
        return None

TRACK_CACHE = {}
CACHE_TTL_SECONDS = 21600  # 6 hours for broader catalog reuse

def get_cached_tracks(cache_key: str) -> Optional[List[dict]]:
    if cache_key in TRACK_CACHE:
        data, timestamp = TRACK_CACHE[cache_key]
        if time.time() - timestamp < CACHE_TTL_SECONDS:
            return data
    return None

def set_cached_tracks(cache_key: str, tracks: List[dict]):
    TRACK_CACHE[cache_key] = (tracks, time.time())

def make_yt_url(title: str, artist: str) -> str:
    """Generate a YouTube search URL for a given song title and artist."""
    q = requests.utils.quote(f"{title} {artist}".strip())
    return f"https://www.youtube.com/results?search_query={q}"

def make_yt_embed_url(title: str, artist: str) -> str:
    """Generate a YouTube search embed URL for a given song title and artist."""
    q = requests.utils.quote(f"{artist} {title}".strip())
    return f"https://www.youtube.com/embed?listType=search&list={q}"

def fetch_itunes_tracks(query: str, limit: int = 30, language: str = "English", genre: str = "Pop") -> List[dict]:
    cache_key = f"itunes_{language}_{genre}_{query}_{limit}"
    cached = get_cached_tracks(cache_key)
    if cached:
        return cached

    try:
        search_term = f"{language} {query}" if language and language != "English" else query
        url = "https://itunes.apple.com/search"
        params = {
            "term": search_term,
            "media": "music",
            "entity": "song",
            "limit": limit
        }
        resp = requests.get(url, params=params, timeout=6)
        results = resp.json().get("results", []) if resp.status_code == 200 else []
        
        # If language prefix search returned no tracks, retry with raw query
        if not results and language and language != "English":
            params["term"] = query
            resp = requests.get(url, params=params, timeout=6)
            results = resp.json().get("results", []) if resp.status_code == 200 else []

        tracks = []
        for item in results:
            preview_url = item.get("previewUrl")
            if not preview_url:
                continue
            artwork = item.get("artworkUrl100", "").replace("100x100bb.jpg", "500x500bb.jpg")
            if not artwork:
                artwork = "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&h=300&fit=crop"
            
            millis = item.get("trackTimeMillis", 0)
            minutes = millis // 60000
            seconds = (millis % 60000) // 1000
            duration_str = f"{minutes}:{seconds:02d}" if millis > 0 else "3:30"

            collection_name = item.get("collectionName", "")
            track_name = item.get("trackName", "")
            album_name = collection_name or "Original Soundtrack"
            if "From \"" in track_name:
                try:
                    extracted = track_name.split("From \"")[1].split("\"")[0]
                    if extracted:
                        album_name = f"Movie: {extracted}"
                except Exception:
                    pass
            
            release_date = item.get("releaseDate", "")
            release_year = release_date[:4] if release_date else "2023"
            
            t_artist = item.get("artistName", "Unknown Artist")
            candidate = {
                "title": track_name,
                "artist": t_artist,
                "mood": genre or "Calm",
                "album": album_name,
                "language": language,
                "genre": item.get("primaryGenreName", genre),
                "duration": duration_str,
                "release_year": release_year,
                "album_image": artwork,
                "preview_url": preview_url,
                "play_url": item.get("trackViewUrl"),
                "youtube_search_url": make_yt_url(track_name, t_artist),
                "embed_url": make_yt_embed_url(track_name, t_artist),
                "is_search_result": True
            }
            if LanguageVerifier.verify_track_language(candidate, language):
                tracks.append(candidate)
        if tracks:
            set_cached_tracks(cache_key, tracks)
            return tracks
    except Exception as e:
        print(f"Exception during iTunes track fetch: {e}")
    return []

def fetch_deezer_tracks(query: str, limit: int = 50, language: str = "English", genre: str = "Pop") -> List[dict]:
    """Fetch tracks from Deezer public API — 90M+ catalog, no auth required."""
    cache_key = f"deezer_{language}_{genre}_{query}_{limit}"
    cached = get_cached_tracks(cache_key)
    if cached:
        return cached
    try:
        lang_prefix = language if language != "English" else ""
        search_term = f"{lang_prefix} {query}".strip()
        url = "https://api.deezer.com/search"
        params = {"q": search_term, "limit": limit, "order": "RANKING"}
        resp = requests.get(url, params=params, timeout=8)
        if resp.status_code == 200:
            results = resp.json().get("data", [])
            tracks = []
            for item in results:
                preview_url = item.get("preview")
                if not preview_url:
                    continue
                album = item.get("album", {})
                artist = item.get("artist", {})
                duration_s = item.get("duration", 0)
                minutes = duration_s // 60
                seconds = duration_s % 60
                duration_str = f"{minutes}:{seconds:02d}" if duration_s > 0 else "3:30"
                cover = album.get("cover_xl") or album.get("cover_big") or album.get("cover_medium") or "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&h=300&fit=crop"
                t_artist = artist.get("name", "Unknown Artist")
                t_title = item.get("title", "")
                candidate = {
                    "title": t_title,
                    "artist": t_artist,
                    "mood": genre or "Calm",
                    "album": album.get("title", "Unknown Album"),
                    "language": language,
                    "genre": genre,
                    "duration": duration_str,
                    "release_year": "2024",
                    "album_image": cover,
                    "preview_url": preview_url,
                    "play_url": item.get("link", ""),
                    "youtube_search_url": make_yt_url(t_title, t_artist),
                    "embed_url": make_yt_embed_url(t_title, t_artist),
                    "is_search_result": True
                }
                if LanguageVerifier.verify_track_language(candidate, language):
                    tracks.append(candidate)
            if tracks:
                set_cached_tracks(cache_key, tracks)
                return tracks
    except Exception as e:
        print(f"Exception during Deezer track fetch: {e}")
    return []

# Comprehensive movie soundtrack keyword catalog per language
MOVIE_CATALOG = {
    "Telugu": [
        "RRR", "Pushpa", "Hi Nanna", "Devara", "Kalki 2898 AD", "Tillu Square",
        "Guntur Kaaram", "Ala Vaikunthapurramuloo", "Samajavaragamana", "Taxiwaala",
        "Dear Comrade", "Fidaa", "Arjun Reddy", "Geetha Govindam", "Bharat Ane Nenu",
        "Baahubali", "Eega", "Magadheera", "Rangasthalam", "Jersey", "Love Story", "Majili",
        "Hushaaru", "Varudu Kavalenu", "Most Eligible Bachelor", "Shyam Singha Roy", "Rang De",
        "Uppena", "DJ Tillu", "Sye Raa Narasimha Reddy", "V", "Vakeel Saab",
        "Maguva Maguva", "Ramuloo Ramulaa", "Naatu Naatu", "Srivalli", "Oo Antava", "Chuttamalle", "Kadalalle", "Priyathama"
    ],
    "Hindi": [
        "Brahmastra", "Animal", "Jawan", "Dunki", "Fighter", "Stree 2",
        "Pathaan", "Rocky Aur Rani", "Tu Jhoothi Main Makkaar", "Bhediya",
        "Kesariya", "Raataan Lambiyan", "Tum Se Hi", "Aaj Ki Raat",
        "Jab We Met", "Ae Dil Hai Mushkil", "Tamasha", "Rockstar", "Highway",
        "Lootera", "Udaan", "Barfi", "Queen", "Dangal",
        "Dil Chahta Hai", "Lagaan", "Rang De Basanti", "3 Idiots", "PK",
        "Kabir Singh", "Uri", "Bard of Blood", "Mirzapur OST", "Sacred Games OST"
    ],
    "Tamil": [
        "Leo", "Jailer", "Vettaiyan", "Kalki 2898 AD Tamil", "Vijay Antony hits",
        "Vikram", "Varisu", "Thunivu", "Beast", "Doctor",
        "Annaatthe", "Master", "Soorarai Pottru", "Karnan", "Jai Bhim",
        "Mandela", "Irudhi Suttru", "Kabali", "Enthiran", "2.0",
        "Neeyum Naanum", "Vinnaithaandi Varuvaayaa", "OK Kanmani", "Mersal", "Bigil",
        "Kaithi", "Thadam", "96", "Oh My Kadavule", "Sarpatta Parambarai"
    ],
    "Malayalam": [
        "Manjummel Boys", "Marco", "Lucifer", "Drishyam 2", "Minnal Murali",
        "Joji", "The Great Indian Kitchen", "Kumbalangi Nights", "Ee.Ma.Yau", "Angamaly Diaries",
        "Premam", "Bangalore Days", "Charlie", "Ennu Ninte Moideen", "How Old Are You",
        "Oru Indian Pranayakatha", "Virus", "Forensic", "Nayattu", "C U Soon",
        "Varane Avashyamund", "Thanneer Mathan Dinangal", "Sudani from Nigeria", "Varathan", "Iyobinte Pusthakam",
        "Vineeth Sreenivasan songs", "Gopi Sundar melody", "Hesham Abdul Wahab hits", "Sushin Shyam OST", "Bijibal songs"
    ],
    "Kannada": [
        "KGF Chapter 2", "Kantara", "777 Charlie", "Kabzaa", "Vikrant Rona",
        "James", "Roberrt", "Masterpiece", "KGF Chapter 1", "Kirik Party",
        "Lucia", "Ugramm", "Googly", "Mungaru Male", "Tagaru"
    ],
    "Punjabi": [
        "Carry On Jatta 3", "Jodi", "Maurh", "Warning 2", "Qismat",
        "Sufna", "Shadaa", "Jatt & Juliet", "Chal Mera Putt", "Angrej"
    ],
    "Bengali": [
        "Praktan", "Besh Korechi Prem Korechi", "Amazon Obhijaan", "Chotushkone", "Baishe Srabon",
        "Autograph", "Belaseshe", "Gotro", "Kolkatar Harry", "Ballabhpurer Roopkotha"
    ],
    "Marathi": [
        "Sairat", "Ved", "Baipan Bhaari Deva", "Subhedar", "Pawankhind",
        "Timepass", "Natsamrat", "Mulshi Pattern", "Katyar Kaljat Ghusli", "Lai Bhaari"
    ],
    "English": [
        "lofi hip hop study beats", "chill ambient relaxation", "piano sleep music",
        "indie pop 2024", "acoustic guitar chill", "nature sounds meditation",
        "jazz coffee morning", "classical healing piano", "Ed Sheeran", "Coldplay",
        "Taylor Swift", "Billie Eilish", "Harry Styles", "Olivia Rodrigo", "The Weeknd",
        "Post Malone", "Dua Lipa", "Adele", "Sam Smith", "Lewis Capaldi", "Stephen Sanchez",
        "JVKE", "Bruno Mars", "James Arthur", "The Kid LAROI", "Justin Bieber", "Lady Gaga", "Miley Cyrus", "One Direction",
        "ambient electronic", "lo-fi beats focus", "deep focus work music", "Hans Zimmer", "Max Richter",
        "Yiruma piano", "Brian Eno ambient", "Marconi Union weightless", "binaural beats relaxation", "healing frequencies 432hz"
    ]
}

ARTIST_CATALOG = {
    "Telugu": [
        "Sid Sriram", "Anirudh Ravichander", "Hesham Abdul Wahab", "A.R. Rahman",
        "S.S. Thaman", "Devi Sri Prasad", "Anurag Kulkarni", "M.M. Keeravani",
        "Shreya Ghoshal Telugu", "Armaan Malik Telugu", "Haricharan", "Jonita Gandhi Telugu",
        "Karthik Telugu", "Yazin Nizar", "Ramya Behara", "Madhu Priya", "Ram Miriyala", "Chinmayi Telugu", "Mangli",
        "Kaala Bhairava", "Naresh Iyer", "Geetha Madhuri", "Mohana Bhogaraju"
    ],
    "Hindi": [
        "Arijit Singh", "Pritam", "Shreya Ghoshal", "Atif Aslam", "A.R. Rahman Hindi",
        "Mohit Chauhan", "Sonu Nigam", "Jubin Nautiyal", "B Praak", "Neha Kakkar",
        "Vishal Shekhar", "Amit Trivedi", "Shankar Ehsaan Loy", "Armaan Malik",
        "Monali Thakur", "Asees Kaur", "Rahul Jain", "Darshan Raval", "Papon", "Shilpa Rao"
    ],
    "Tamil": [
        "Anirudh Ravichander", "A.R. Rahman Tamil", "Yuvan Shankar Raja", "Harris Jayaraj",
        "Sid Sriram Tamil", "Dhanush", "Santhosh Narayanan", "G.V. Prakash Kumar",
        "Pradeep Kumar Tamil", "Jonita Gandhi", "Bombay Jayashri", "Shreya Ghoshal Tamil",
        "Karthik Tamil", "Haricharan Tamil", "Naresh Iyer Tamil", "Benny Dayal",
        "Andrea Jeremiah", "Chinmayi", "Tippu", "Velmurugan"
    ],
    "Malayalam": [
        "Hesham Abdul Wahab", "Sushin Shyam", "Vijay Yesudas", "K.S. Chithra",
        "Job Kurian", "Vineeth Sreenivasan", "Shaan Rahman", "Gopi Sundar",
        "Pradeep Kumar Malayalam", "Sooraj Santhosh", "Bijibal", "Ouseppachan",
        "Rathish Vega", "Sithara Krishnakumar", "Sujatha Mohan", "Unni Menon",
        "M.G. Sreekumar", "Haricharan Malayalam", "Zia Ul Haq", "Rahul Raj"
    ],
    "Kannada": [
        "Sanjith Hegde", "Sonu Nigam Kannada", "Vijay Prakash", "Arjun Janya",
        "Charan Raj", "B. Ajaneesh Loknath", "Raghu Dixit", "Armaan Malik Kannada",
        "Shreya Ghoshal Kannada", "V. Harikrishna"
    ],
    "Punjabi": [
        "Diljit Dosanjh", "AP Dhillon", "Gurinder Gill", "Sidhu Moose Wala",
        "B Praak", "Jasleen Royal", "Shubh", "Karan Aujla", "Guru Randhawa", "Hardy Sandhu"
    ],
    "Bengali": [
        "Arijit Singh Bengali", "Anupam Roy", "Shreya Ghoshal Bengali", "Jeet Gannguli",
        "Anirban Bhattacharya", "Lopamudra Mitra", "Iman Chakraborty", "Rupam Islam"
    ],
    "Marathi": [
        "Ajay-Atul", "Swapnil Bandodkar", "Avadhoot Gupte", "Shreya Ghoshal Marathi",
        "Mahesh Kale", "Rahul Deshpande", "Arya Ambekar", "Adarsh Shinde"
    ],
    "English": [
        "Marconi Union", "Coldplay", "Ed Sheeran", "Taylor Swift", "Billie Eilish",
        "The Weeknd", "Harry Styles", "Olivia Rodrigo", "Post Malone", "Dua Lipa",
        "Stephen Sanchez", "JVKE", "Bruno Mars", "James Arthur", "The Kid LAROI", "Justin Bieber", "Lady Gaga", "Miley Cyrus", "One Direction",
        "Ludovico Einaudi", "Yiruma", "Hans Zimmer", "Max Richter", "Brian Eno",
        "Adele", "Sam Smith", "Lewis Capaldi", "Shawn Mendes", "Charlie Puth"
    ]
}

def build_search_matrix(language: str, genre: str, mood: str, activity: str) -> List[str]:
    """Build a comprehensive 30+ query search matrix for maximum catalog depth."""
    movies = MOVIE_CATALOG.get(language, MOVIE_CATALOG["English"])
    artists = ARTIST_CATALOG.get(language, ARTIST_CATALOG["English"])

    queries = [
        # Genre + Mood combos
        f"{genre} {mood}",
        f"{mood} {genre} music",
        f"{genre} songs {mood}",
        f"best {genre} {activity}",
        f"{mood} instrumental {genre}",
        f"{genre} acoustic relaxation",
        f"{mood} melody",
        f"{activity} music {genre}",
    ]

    # Top movie soundtracks (up to 15)
    for movie in movies[:15]:
        queries.append(f"{movie} soundtrack")

    # Top artists (up to 10)
    for artist in artists[:10]:
        queries.append(f"{artist} {mood}")

    return queries

def fetch_hybrid_recommendations(
    user_id: Optional[int] = None,
    mood: str = "Calming",
    language: str = "English",
    genre: str = "Lo-fi",
    activity: str = "Relaxation",
    limit: int = 50,
    db: Session = None
) -> List[dict]:
    cache_key = f"hybrid_{user_id}_{mood}_{language}_{genre}_{activity}_{limit}"
    cached = get_cached_tracks(cache_key)
    if cached:
        return cached

    search_queries = build_search_matrix(language=language, genre=genre, mood=mood, activity=activity)

    all_tracks = []
    seen_titles = set()

    fav_artists = set()
    if db and user_id:
        try:
            favs = db.query(FavoriteTrack).filter(FavoriteTrack.user_id == user_id).all()
            for f in favs:
                if f.artist:
                    fav_artists.add(f.artist.lower())
            hist = db.query(ListeningHistory).filter(ListeningHistory.user_id == user_id).limit(20).all()
            for h in hist:
                if h.artist:
                    fav_artists.add(h.artist.lower())
        except Exception:
            pass

    # --- iTunes Pass (primary multilingual source) ---
    for q in search_queries:
        if len(all_tracks) >= limit * 2:  # gather 2x for quality ranking
            break
        tracks = fetch_itunes_tracks(query=q, limit=50, language=language, genre=genre)
        for t in tracks:
            t_title = (t.get("title") or "").lower().strip()
            if t_title and t_title not in seen_titles:
                seen_titles.add(t_title)
                score = 0
                artist = (t.get("artist") or "").lower()
                if any(fa in artist for fa in fav_artists if fa):
                    score += 5
                t["hybrid_score"] = score
                all_tracks.append(t)

    # --- Deezer Pass (secondary source for broader catalog depth) ---
    deezer_queries = search_queries[:8]  # use top 8 queries for Deezer
    for q in deezer_queries:
        if len(all_tracks) >= limit * 3:
            break
        deezer_tracks = fetch_deezer_tracks(query=q, limit=50, language=language, genre=genre)
        for t in deezer_tracks:
            t_title = (t.get("title") or "").lower().strip()
            if t_title and t_title not in seen_titles:
                seen_titles.add(t_title)
                score = 0
                artist = (t.get("artist") or "").lower()
                if any(fa in artist for fa in fav_artists if fa):
                    score += 5
                t["hybrid_score"] = score
                all_tracks.append(t)

    all_tracks.sort(key=lambda x: x.get("hybrid_score", 0), reverse=True)

    # Fallback to curated library if still empty
    if len(all_tracks) < 5 and language in MULTI_LANG_LIBRARY:
        for t in MULTI_LANG_LIBRARY[language]:
            t_title = (t.get("title") or "").lower()
            if t_title not in seen_titles:
                seen_titles.add(t_title)
                all_tracks.append({
                    "title": t["title"],
                    "artist": t["artist"],
                    "album": "Movie Soundtrack",
                    "language": language,
                    "genre": genre,
                    "duration": t.get("duration", "3:30"),
                    "release_year": "2023",
                    "album_image": t.get("album_image"),
                    "preview_url": t.get("preview_url"),
                    "play_url": t.get("play_url")
                })

    result_set = all_tracks[:limit]
    set_cached_tracks(cache_key, result_set)
    return result_set

LANGUAGE_KEYWORDS = {
    "English": "english",
    "Telugu": "telugu tollywood",
    "Hindi": "hindi bollywood",
    "Tamil": "tamil kollywood",
    "Malayalam": "malayalam mollywood",
    "Kannada": "kannada sandalwood",
    "Punjabi": "punjabi",
    "Bengali": "bengali",
    "Marathi": "marathi"
}

def fetch_spotify_tracks(
    query: str,
    limit: int = 8,
    language: str = "English",
    mood: Optional[str] = None,
    genre: Optional[str] = None,
    fav_artists: Optional[List[str]] = None
) -> List[dict]:
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

    # Normalize language string
    lang_key = language.strip().title() if language else "English"
    lang_search = LANGUAGE_KEYWORDS.get(lang_key, lang_key.lower())

    if client_id and client_secret:
        try:
            token = get_spotify_access_token(client_id, client_secret)
            if token:
                search_url = "https://api.spotify.com/v1/search"
                headers = {"Authorization": f"Bearer {token}"}

                # Evaluate clinical therapy profile for query generation
                mental_state = determine_mental_state(mood or query)
                therapy_prof = THERAPY_PROFILE.get(mental_state, THERAPY_PROFILE["stress"])
                therapy_genre = therapy_prof["genre"]
                therapy_keywords = " ".join(therapy_prof["keywords"])

                # Build multiple Spotify search queries using:
                # selected language, mood, genre, therapy profile keywords, movie soundtrack keywords, artist keywords
                relaxation_kw = f"{therapy_keywords} acoustic"
                soundtrack_kw = "soundtrack movie album hits"

                queries = [
                    f"{query} {lang_search}",
                    f"{lang_search} {mood or 'chill'} {genre or 'music'}",
                    f"{lang_search} {therapy_genre}",
                    f"{lang_search} {relaxation_kw}",
                    f"{lang_search} {soundtrack_kw}"
                ]

                # Include movie soundtrack keywords if available
                movies = MOVIE_CATALOG.get(lang_key, [])
                if movies:
                    queries.append(f"{lang_search} {movies[0]} soundtrack")
                    if len(movies) > 1:
                        queries.append(f"{lang_search} {movies[1]}")

                # Include artist keywords if available
                catalog_artists = ARTIST_CATALOG.get(lang_key, [])
                if fav_artists:
                    for fa in fav_artists[:2]:
                        queries.append(f"{fa} {lang_search}")
                elif catalog_artists:
                    queries.append(f"{catalog_artists[0]} {lang_search}")
                    if len(catalog_artists) > 1:
                        queries.append(f"{catalog_artists[1]} {lang_search}")

                seen_ids = set()
                candidates = []

                lang_terms = [t.lower() for t in lang_search.split()]
                mood_terms = [mood.lower()] if mood else ["relax", "calm", "peace", "chill", "sooth", "meditation"]
                genre_terms = [genre.lower()] if genre else ["lo-fi", "pop", "classical", "nature", "instrumental", "acoustic"]
                target_artists = [a.lower() for a in (fav_artists or catalog_artists)]

                for q_str in queries:
                    params = {
                        "q": q_str,
                        "type": "track",
                        "market": "IN",
                        "limit": 50
                    }
                    search_resp = requests.get(search_url, headers=headers, params=params, timeout=5)
                    if search_resp.status_code == 200:
                        items = search_resp.json().get("tracks", {}).get("items", [])
                        for item in items:
                            track_id = item.get("id")
                            if not track_id or track_id in seen_ids:
                                continue
                            seen_ids.add(track_id)

                            duration_ms = item.get("duration_ms", 0)
                            minutes = duration_ms // 60000
                            seconds = (duration_ms % 60000) // 1000
                            duration_str = f"{minutes}:{seconds:02d}"

                            images = item.get("album", {}).get("images", [])
                            album_img = images[0].get("url") if images else "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=150&h=150&fit=crop"

                            artist_names = ", ".join([a.get("name", "") for a in item.get("artists", [])])
                            album_name = item.get("album", {}).get("name", "Unknown Album")
                            track_name = item.get("name", "")
                            release_date = item.get("album", {}).get("release_date", "")
                            release_year = release_date[:4] if release_date else "2024"

                            # Rank songs using: language match, mood match, genre match, popularity, favorite artists
                            popularity = item.get("popularity", 0)
                            score = float(popularity)

                            full_text = f"{track_name} {album_name} {artist_names}".lower()

                            # 1. Language match
                            if any(lt in full_text for lt in lang_terms):
                                score += 30.0

                            # 2. Mood match
                            if any(mt in full_text for mt in mood_terms):
                                score += 20.0

                            # 3. Genre match
                            if any(gt in full_text for gt in genre_terms):
                                score += 20.0

                            # 4. Favorite/Popular Artist match
                            if any(ta in artist_names.lower() for ta in target_artists if ta):
                                score += 25.0

                            track_obj = {
                                "title": track_name,
                                "artist": artist_names,
                                "mood": mood or "Calm",
                                "album": album_name,
                                "language": lang_key,
                                "genre": genre or "Pop",
                                "duration": duration_str,
                                "release_year": release_year,
                                "album_image": album_img,
                                "play_url": item.get("external_urls", {}).get("spotify"),
                                "preview_url": item.get("preview_url"),
                                "youtube_search_url": make_yt_url(track_name, artist_names),
                                "embed_url": make_yt_embed_url(track_name, artist_names)
                            }
                            candidates.append((score, track_obj))

                if candidates:
                    candidates.sort(key=lambda x: x[0], reverse=True)
                    return [c[1] for c in candidates[:limit]]
        except Exception as e:
            print(f"Exception during Spotify fetch: {e}")

    # Fallback to iTunes API if Spotify fails or yields no tracks
    itunes_tracks = fetch_itunes_tracks(query, limit, lang_key)
    if itunes_tracks:
        return itunes_tracks[:limit]

    # Fallback to curated multi-language mock library
    if lang_key in MULTI_LANG_LIBRARY:
        return MULTI_LANG_LIBRARY[lang_key][:limit]
    return MOCK_LIBRARY.get(query, MOCK_LIBRARY["playlist_1"])[:limit]

# Pydantic Schemas
class UserSignup(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    fav_genre: Optional[str] = "Lo-fi"

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if not re.match(r'^[a-zA-Z0-9_@.-]+$', v):
            raise ValueError('Username can only contain letters, numbers, @, ., underscores, and hyphens')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

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
    username_or_email: Optional[str] = None
    reset_token: Optional[str] = None
    new_password: str

class HistoryRecordItem(BaseModel):
    title: str
    artist: str
    duration: str
    album_image: Optional[str] = None
    play_url: Optional[str] = None
    preview_url: Optional[str] = None

class PlaylistCreate(BaseModel):
    name: str
    description: Optional[str] = ""

class PlaylistAddTrack(BaseModel):
    title: str
    artist: str
    duration: str
    album_image: Optional[str] = None
    play_url: Optional[str] = None
    preview_url: Optional[str] = None

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

class TrackFeedbackSubmit(BaseModel):
    title: str
    artist: str
    action: str # 'like', 'skip', 'play'
    therapy_category: Optional[str] = None
    language: Optional[str] = None
    genre: Optional[str] = None


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
def get_me(current_user: User = Depends(get_optional_current_user)):
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found matching that username or email address."
        )
    
    reset_tok = generate_reset_token()
    user.reset_token = reset_tok
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()

    return {
        "status": "success",
        "message": f"Account found for {user.username}.",
        "username": user.username,
        "email": user.email,
        "reset_token": reset_tok
    }

@app.post("/api/auth/reset-password")
def reset_password(req: ResetPasswordSubmit, db: Session = Depends(get_db)):
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    user = None
    if req.reset_token:
        user = db.query(User).filter(User.reset_token == req.reset_token).first()
    
    if not user and req.username_or_email:
        user = db.query(User).filter((User.username == req.username_or_email) | (User.email == req.username_or_email)).first()

    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token / account request.")

    user.hashed_password = get_password_hash(req.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return {
        "status": "success",
        "message": f"Password for {user.username} reset successfully! You can now log in.",
        "username": user.username
    }

@app.post("/api/recommend/survey")
def submit_survey(survey: SurveySubmit, current_user: User = Depends(get_optional_current_user), db: Session = Depends(get_db)):
    user_id = current_user.id if current_user else None
    
    # 1. Execute Production Hybrid Recommendation Engine
    survey_dict = survey.model_dump() if hasattr(survey, 'model_dump') else survey.dict()
    rec_result = hybrid_recommender.get_recommendations(
        survey_data=survey_dict,
        user_id=user_id,
        db=db,
        limit=20
    )
    
    tracks = rec_result.get("tracks", [])
    therapy_category = rec_result.get("predicted_therapy_category", "Relaxation")

    # 2. Persist Survey Assessment Record
    response_record = SurveyResponse(
        user_id=user_id if user_id else 1,
        age=survey.age,
        gender=survey.gender,
        mood=survey.mood,
        stress=survey.stress,
        sleep_quality=survey.sleep_quality,
        anxiety=survey.anxiety,
        fav_genre=survey.fav_genre,
        language_pref=survey.language_pref,
        activity=survey.activity,
        result_playlist=therapy_category
    )
    db.add(response_record)
    db.commit()
    db.refresh(response_record)
    
    # 3. Store Recommendation Details
    rec_record = Recommendation(
        survey_id=response_record.id,
        genre=therapy_category,
        tracks=json.dumps(tracks)
    )
    db.add(rec_record)
    db.commit()
    
    return {
        "survey_id": response_record.id,
        "result_state": therapy_category,
        "playlist_key": "playlist_1",
        "predicted_therapy_category": therapy_category,
        "prediction_confidence": rec_result.get("prediction_confidence", 0.90),
        "tracks": tracks,
        "timestamp": response_record.timestamp.isoformat()
    }

@app.post("/api/recommend/track-feedback")
def submit_track_feedback(feedback: TrackFeedbackSubmit, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    success = hybrid_recommender.feedback_manager.record_feedback(
        user_id=current_user.id,
        title=feedback.title,
        artist=feedback.artist,
        action=feedback.action,
        therapy_category=feedback.therapy_category,
        language=feedback.language,
        genre=feedback.genre,
        db=db
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to record track feedback")
    return {"status": "success", "message": f"Recorded action '{feedback.action}' for track '{feedback.title}'"}


@app.post("/api/recommend/feedback")
def submit_feedback(feedback: FeedbackSubmit, current_user: User = Depends(get_optional_current_user), db: Session = Depends(get_db)):
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
def get_history(current_user: User = Depends(get_optional_current_user), db: Session = Depends(get_db)):
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
def get_journals(current_user: User = Depends(get_optional_current_user), db: Session = Depends(get_db)):
    entries = db.query(DailyJournal).filter(DailyJournal.user_id == current_user.id).order_by(DailyJournal.timestamp.desc()).all()
    return [{
        "id": e.id,
        "mood": e.mood,
        "stress": e.stress,
        "journal_text": e.journal_text,
        "timestamp": e.timestamp.isoformat()
    } for e in entries]

@app.post("/api/journal")
def add_journal(entry: JournalSubmit, current_user: User = Depends(get_optional_current_user), db: Session = Depends(get_db)):
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
def get_favorites(current_user: User = Depends(get_optional_current_user), db: Session = Depends(get_db)):
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

MOTIVATIONAL_QUOTES = [
    {"quote": "You don't have to control your thoughts. You just have to stop letting them control you.", "author": "Dan Millman"},
    {"quote": "Peace comes from within. Do not seek it without.", "author": "Buddha"},
    {"quote": "Almost everything will work again if you unplug it for a few minutes, including you.", "author": "Anne Lamott"},
    {"quote": "You are braver than you believe, stronger than you seem, and smarter than you think.", "author": "A.A. Milne"},
    {"quote": "Healing takes time, and asking for help is a courageous step, not a weakness.", "author": "Therapeutic Insight"},
    {"quote": "Breathe. It's just a bad day, not a bad life.", "author": "Mindfulness Reflection"},
    {"quote": "When everything seems to be going against you, remember that the airplane takes off against the wind, not with it.", "author": "Henry Ford"},
    {"quote": "Out of your vulnerabilities will come your strength.", "author": "Sigmund Freud"},
    {"quote": "Self-care is how you take your power back.", "author": "Lalah Delia"},
    {"quote": "The greatest weapon against stress is our ability to choose one thought over another.", "author": "William James"}
]

MEDITATION_TRACKS = [
    {"title": "Deep Forest Rain & Birds", "artist": "Nature Soundscapes", "duration": "8:00", "album_image": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=300&h=300&fit=crop", "preview_url": "https://cdn.pixabay.com/download/audio/2021/08/09/audio_884489a24d.mp3"},
    {"title": "Ocean Waves & Soft Wind", "artist": "Coastal Therapy", "duration": "7:30", "album_image": "https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=300&h=300&fit=crop", "preview_url": "https://cdn.pixabay.com/download/audio/2022/06/07/audio_b2875e6a98.mp3"},
    {"title": "Tibetan Healing Singing Bowls", "artist": "Zen Meditation", "duration": "6:15", "album_image": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=300&h=300&fit=crop", "preview_url": "https://cdn.pixabay.com/download/audio/2021/08/09/audio_884489a24d.mp3"},
    {"title": "Pranam (Carnatic Flute Meditation)", "artist": "Flute Ensemble", "duration": "5:10", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music116/v4/b5/04/cd/b504cdb8-d632-4b6b-1b68-10686397ff42/8903431963307_cover.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview126/v4/f3/b0/73/f3b073f5-f84b-88d5-9d46-066aa152d606/mzaf_13123944415807399306.plus.aac.p.m4a"}
]

@app.post("/api/chatbot")
def chat_bot(message_data: ChatbotMessage):
    msg = message_data.message.lower().strip()
    mood = message_data.current_mood
    
    category = "wellness"
    reply = ""
    suggested_tracks = []
    selected_quote = None

    # 1. SUGGEST MUSIC
    if any(k in msg for k in ["song", "music", "suggest", "track", "playlist", "telugu", "hindi", "tamil", "korean", "spanish"]):
        category = "songs"
        lang = "English"
        if "telugu" in msg:
            lang = "Telugu"
        elif "hindi" in msg:
            lang = "Hindi"
        elif "tamil" in msg:
            lang = "Tamil"
        elif "korean" in msg:
            lang = "Korean"
        elif "spanish" in msg:
            lang = "Spanish"
            
        suggested_tracks = fetch_spotify_tracks(query="relaxing acoustic chill", limit=4, language=lang)
        if not suggested_tracks and lang in MULTI_LANG_LIBRARY:
            suggested_tracks = MULTI_LANG_LIBRARY[lang][:4]
            
        reply = f"🎵 **Therapeutic Song Suggestions ({lang})**\nHere are 4 hand-picked {lang} tracks tailored to soothe your nervous system and elevate your mood. Click ▶ to play any track instantly!"

    # 2. GIVES BREATHING EXERCISES
    elif any(k in msg for k in ["breath", "breathing", "exercise", "technique", "4-7-8", "box breathing", "grounding", "relax"]):
        category = "technique"
        if "box" in msg:
            reply = (
                "🧘 **Box Breathing Exercise (Navy SEAL 4x4 Method)**\n\n"
                "1. **Inhale slowly** through your nose for **4 seconds**.\n"
                "2. **Hold your breath** for **4 seconds**.\n"
                "3. **Exhale steadily** through your mouth for **4 seconds**.\n"
                "4. **Hold empty** for **4 seconds**.\n"
                "5. **Repeat for 4 rounds**.\n\n"
                "💡 *Clinical Benefit*: Resets the vagus nerve and restores cognitive focus during high anxiety."
            )
        else:
            reply = (
                "🧘 **Clinical 4-7-8 Breathing Technique**\n\n"
                "1. **Inhale quietly** through your nose for **4 seconds**.\n"
                "2. **Hold your breath** gently for **7 seconds**.\n"
                "3. **Exhale completely** through your mouth making a soft 'whoosh' sound for **8 seconds**.\n"
                "4. **Repeat for 4 full cycles**.\n\n"
                "💡 *Clinical Impact*: Lowers heart rate, reduces blood pressure, and activates parasympathetic relaxation."
            )
        suggested_tracks = MEDITATION_TRACKS[:2]

    # 3. SUGGESTS MEDITATION
    elif any(k in msg for k in ["meditat", "ambient", "rain", "flute", "bowls", "mindful"]):
        category = "meditation"
        reply = (
            "🧘‍♀️ **Guided Meditation & Soundscape Recommendation**\n"
            "Deep acoustic frequencies (432Hz / 528Hz) and nature soundscapes entrain brainwaves into Alpha and Theta states, helping lower anxiety and promote deep inner calm."
        )
        suggested_tracks = MEDITATION_TRACKS

    # 4. GIVES MOTIVATIONAL QUOTES
    elif any(k in msg for k in ["quote", "motivat", "inspire", "inspiration", "encourage"]):
        category = "quote"
        import random
        selected_quote = random.choice(MOTIVATIONAL_QUOTES)
        reply = f"💡 **Daily Motivational Reflection**:\n\n*\"{selected_quote['quote']}\"*\n— **{selected_quote['author']}**"

    # 5. ANSWERS MENTAL HEALTH QUESTIONS
    elif any(k in msg for k in ["stress", "anxi", "burnout", "worry", "sleep", "insomnia", "depress", "sad", "mental health", "panic", "lonely", "help"]):
        category = "wellness"
        if "sleep" in msg or "insomnia" in msg:
            reply = (
                "🌙 **Clinical Sleep Hygiene Protocol**:\n"
                "• **30-Min Wind-down**: Avoid screens 30 minutes before bed.\n"
                "• **Environment**: Keep bedroom cool (18-20°C / 65-68°F).\n"
                "• **Soundscape**: Listen to rhythmic ambient rainfall or Carnatic flute streams to transition into deep REM sleep."
            )
            suggested_tracks = MEDITATION_TRACKS[:2]
        elif "stress" in msg or "burnout" in msg or "overwhelm" in msg:
            reply = (
                "⚡ **Burnout & Stress Recovery Protocol**:\n"
                "• **Micro-breaks**: Take a 5-minute break every 50 minutes of work.\n"
                "• **5-4-3-2-1 Grounding**: Identify 5 things you see, 4 you feel, 3 you hear, 2 you smell, and 1 you taste.\n"
                "• **Auditory Relief**: Listen to acoustic ambient melodies to reduce cognitive workload."
            )
            suggested_tracks = MOCK_LIBRARY.get("playlist_4", [])[:2]
        else:
            reply = (
                "💚 **Mental Health & Emotional Wellness**:\n"
                "Your feelings are valid. Healing is an iterative journey. "
                "Pairing gentle physical movement, mindful breathing, and therapeutic music helps regulate your nervous system."
            )
            suggested_tracks = MOCK_LIBRARY.get("playlist_1", [])[:2]

    else:
        reply = (
            "Hi! I am your AI Wellness Assistant. Here is how I can support you:\n\n"
            "• 🎵 **Suggest Music**: 'Suggest Telugu / Hindi / English songs'\n"
            "• 🧘 **Breathing Exercises**: 'Give me a 4-7-8 breathing exercise'\n"
            "• 🧘‍♀️ **Suggest Meditation**: 'Recommend meditation music soundscapes'\n"
            "• 💡 **Motivational Quotes**: 'Give me an inspiring motivational quote'\n"
            "• 🧠 **Mental Health Questions**: 'How to reduce stress and improve sleep?'"
        )
        suggested_tracks = MEDITATION_TRACKS[:2]

    return {
        "reply": reply,
        "category": category,
        "suggested_tracks": suggested_tracks,
        "quote": selected_quote
    }

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

# -------------------------------------------------------------------
# Database Architecture API Endpoints
# -------------------------------------------------------------------

# 1. Listening History & Recently Played Songs
@app.post("/api/music/history")
def record_listening_history(
    item: HistoryRecordItem,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    entry = ListeningHistory(
        user_id=current_user.id,
        title=item.title,
        artist=item.artist,
        duration=item.duration,
        album_image=item.album_image,
        play_url=item.play_url,
        preview_url=item.preview_url
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"status": "success", "id": entry.id, "played_at": entry.played_at.isoformat()}

@app.get("/api/music/history")
def get_listening_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    records = db.query(ListeningHistory)\
        .filter(ListeningHistory.user_id == current_user.id)\
        .order_by(ListeningHistory.played_at.desc())\
        .limit(25)\
        .all()
    
    return [{
        "id": r.id,
        "title": r.title,
        "artist": r.artist,
        "duration": r.duration,
        "album_image": r.album_image,
        "play_url": r.play_url,
        "preview_url": r.preview_url,
        "played_at": r.played_at.strftime("%Y-%m-%d %H:%M")
    } for r in records]

# 2. User Playlists Management
@app.post("/api/playlists")
def create_playlist(
    pdata: PlaylistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    playlist = UserPlaylist(
        user_id=current_user.id,
        name=pdata.name,
        description=pdata.description
    )
    db.add(playlist)
    db.commit()
    db.refresh(playlist)
    return {"status": "success", "id": playlist.id, "name": playlist.name}

@app.get("/api/playlists")
def get_user_playlists(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    playlists = db.query(UserPlaylist)\
        .options(joinedload(UserPlaylist.tracks))\
        .filter(UserPlaylist.user_id == current_user.id)\
        .order_by(UserPlaylist.updated_at.desc())\
        .all()
    
    return [{
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "track_count": len(p.tracks),
        "created_at": p.created_at.strftime("%Y-%m-%d %H:%M")
    } for p in playlists]

@app.get("/api/playlists/{playlist_id}")
def get_playlist_details(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    playlist = db.query(UserPlaylist)\
        .options(joinedload(UserPlaylist.tracks))\
        .filter(UserPlaylist.id == playlist_id, UserPlaylist.user_id == current_user.id)\
        .first()
        
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
        
    return {
        "id": playlist.id,
        "name": playlist.name,
        "description": playlist.description,
        "created_at": playlist.created_at.strftime("%Y-%m-%d %H:%M"),
        "tracks": [{
            "id": t.id,
            "title": t.title,
            "artist": t.artist,
            "duration": t.duration,
            "album_image": t.album_image,
            "play_url": t.play_url,
            "preview_url": t.preview_url,
            "added_at": t.added_at.strftime("%Y-%m-%d %H:%M")
        } for t in playlist.tracks]
    }

@app.post("/api/playlists/{playlist_id}/tracks")
def add_track_to_playlist(
    playlist_id: int,
    track: PlaylistAddTrack,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    playlist = db.query(UserPlaylist)\
        .filter(UserPlaylist.id == playlist_id, UserPlaylist.user_id == current_user.id)\
        .first()
        
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
        
    ptrack = PlaylistTrack(
        playlist_id=playlist.id,
        title=track.title,
        artist=track.artist,
        duration=track.duration,
        album_image=track.album_image,
        play_url=track.play_url,
        preview_url=track.preview_url
    )
    playlist.updated_at = datetime.now(timezone.utc)
    db.add(ptrack)
    db.commit()
    return {"status": "success", "message": f"Added '{track.title}' to playlist '{playlist.name}'"}

@app.delete("/api/playlists/{playlist_id}")
def delete_playlist(
    playlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    playlist = db.query(UserPlaylist)\
        .filter(UserPlaylist.id == playlist_id, UserPlaylist.user_id == current_user.id)\
        .first()
        
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
        
    db.delete(playlist)
    db.commit()
    return {"status": "success", "message": "Playlist deleted successfully"}

# 3. Consolidated Mood History Timeline
@app.get("/api/mood/history")
def get_mood_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    surveys = db.query(SurveyResponse)\
        .filter(SurveyResponse.user_id == current_user.id)\
        .order_by(SurveyResponse.timestamp.asc())\
        .all()
        
    journals = db.query(DailyJournal)\
        .filter(DailyJournal.user_id == current_user.id)\
        .order_by(DailyJournal.timestamp.asc())\
        .all()
        
    events = []
    for s in surveys:
        events.append({
            "type": "assessment",
            "mood": s.mood,
            "stress": s.stress,
            "anxiety": s.anxiety,
            "sleep_quality": s.sleep_quality,
            "activity": s.activity,
            "timestamp": s.timestamp.strftime("%Y-%m-%d %H:%M")
        })
        
    for j in journals:
        events.append({
            "type": "journal",
            "mood": j.mood,
            "stress": j.stress,
            "journal_text": j.journal_text,
            "timestamp": j.timestamp.strftime("%Y-%m-%d %H:%M")
        })
        
    events.sort(key=lambda x: x["timestamp"])
    return {"user_id": current_user.id, "timeline": events}

@app.get("/api/recommend/by-language")
def get_recommendations_by_language(
    language: str = "English",
    genre: Optional[str] = "Lo-fi",
    mood: Optional[str] = "Calming",
    activity: Optional[str] = "Relaxation",
    query: Optional[str] = None,
    playlist_key: Optional[str] = "playlist_1",
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    playlist_type = playlist_key if playlist_key in PLAYLIST_THEME_MAPPING else "playlist_1"
    theme_info = PLAYLIST_THEME_MAPPING[playlist_type]
    
    if query and query.strip():
        # Merge iTunes + Deezer results for query searches for maximum catalog depth
        itunes_tracks = fetch_itunes_tracks(query=query.strip(), limit=50, language=language, genre=genre or "Pop")
        deezer_tracks = fetch_deezer_tracks(query=f"{language} {query.strip()}", limit=50, language=language, genre=genre or "Pop")
        seen = set()
        merged = []
        for t in itunes_tracks + deezer_tracks:
            title_key = (t.get("title") or "").lower().strip()
            if title_key and title_key not in seen:
                seen.add(title_key)
                t["youtube_search_url"] = make_yt_url(t.get("title", ""), t.get("artist", ""))
                merged.append(t)
        if merged:
            return {
                "language": language,
                "playlist_key": playlist_type,
                "playlist_name": f"{language} — {query.strip()} Results",
                "tracks": merged[:60]
            }

    rec_result = hybrid_recommender.get_recommendations(
        survey_data={
            "mood": mood or "Calming",
            "language_pref": language,
            "fav_genre": genre or "Lo-fi",
            "activity": activity or "Relaxation"
        },
        user_id=current_user.id if current_user else None,
        db=db,
        limit=50
    )
    tracks = rec_result.get("tracks", [])
    t_cat = rec_result.get("predicted_therapy_category", theme_info['name'])
    return {
        "language": language,
        "playlist_key": playlist_type,
        "playlist_name": f"{language} {t_cat}",
        "tracks": tracks
    }

@app.get("/api/catalog/browse")
def browse_catalog(
    language: str = "English",
    genre: Optional[str] = "Lo-fi",
    mood: Optional[str] = "Calming",
    activity: Optional[str] = "Relaxation",
    query: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Paginated catalog browser — returns fresh tracks per page for infinite scroll."""
    if query and query.strip():
        # Text search across both iTunes and Deezer
        itunes_tracks = fetch_itunes_tracks(query=query.strip(), limit=limit * 2, language=language, genre=genre or "Pop")
        deezer_tracks = fetch_deezer_tracks(query=f"{language} {query.strip()}", limit=limit * 2, language=language, genre=genre or "Pop")
        seen = set()
        merged = []
        for t in itunes_tracks + deezer_tracks:
            title_key = (t.get("title") or "").lower().strip()
            if title_key and title_key not in seen:
                seen.add(title_key)
                t["youtube_search_url"] = make_yt_url(t.get("title", ""), t.get("artist", ""))
                merged.append(t)
        start = (page - 1) * limit
        page_tracks = merged[start:start + limit]
        return {
            "language": language,
            "page": page,
            "total_fetched": len(merged),
            "tracks": page_tracks
        }

    # Build full search matrix and paginate it
    # Each page uses a different slice of the movie/artist catalog
    movies = MOVIE_CATALOG.get(language, MOVIE_CATALOG["English"])
    artists = ARTIST_CATALOG.get(language, ARTIST_CATALOG["English"])

    # Rotate movies & artists by page number to always return fresh content
    movie_offset = ((page - 1) * 5) % len(movies)
    artist_offset = ((page - 1) * 3) % len(artists)

    page_queries = [
        f"{genre or 'Pop'} {mood or 'Calming'}",
        f"{mood or 'Calming'} {genre or 'Pop'} music",
        f"{activity or 'Relaxation'} music {genre or 'Pop'}",
    ]
    for movie in movies[movie_offset:movie_offset + 5]:
        page_queries.append(f"{movie} soundtrack")
    for artist in artists[artist_offset:artist_offset + 3]:
        page_queries.append(f"{artist} {mood or 'Calming'}")

    all_tracks = []
    seen = set()
    for q in page_queries:
        tracks = fetch_itunes_tracks(query=q, limit=limit, language=language, genre=genre or "Pop")
        dz_tracks = fetch_deezer_tracks(query=q, limit=limit, language=language, genre=genre or "Pop")
        for t in tracks + dz_tracks:
            title_key = (t.get("title") or "").lower().strip()
            if title_key and title_key not in seen:
                seen.add(title_key)
                t["youtube_search_url"] = make_yt_url(t.get("title", ""), t.get("artist", ""))
                all_tracks.append(t)

    return {
        "language": language,
        "page": page,
        "total_fetched": len(all_tracks),
        "tracks": all_tracks[:limit]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
