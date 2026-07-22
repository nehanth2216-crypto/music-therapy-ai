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
    FavoriteTrack,
    ListeningHistory,
    UserPlaylist,
    PlaylistTrack
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
SUPPORTED_LANGUAGES = ["English", "Telugu", "Hindi", "Tamil", "Kannada", "Malayalam", "Punjabi", "Bengali", "Marathi", "Korean", "Japanese", "Spanish"]

PLAYLIST_THEME_MAPPING = {
    "playlist_1": {"name": "Lofi & Calm Pop", "query": "lofi hip hop chill study beats"},
    "playlist_2": {"name": "Healing Classical", "query": "peaceful classical sleep relax piano"},
    "playlist_3": {"name": "Meditation Nature Sounds", "query": "nature sounds meditation calming water"},
    "playlist_4": {"name": "Relaxing Instrumental", "query": "relaxing instrumental acoustic guitar chill"},
    "playlist_5": {"name": "Energetic Pop & Dance", "query": "workout pop dance hits energy"},
}

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

# Multi-Language Curated Track Libraries (Exact Official Movie Songs & Official Poster Artwork)
MULTI_LANG_LIBRARY = {
    "Telugu": [
        {"title": "Samayama (From \"Hi Nanna\")", "artist": "Hesham Abdul Wahab, Anurag Kulkarni & Sithara Krishnakumar", "duration": "4:12", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music116/v4/b5/04/cd/b504cdb8-d632-4b6b-1b68-10686397ff42/8903431963307_cover.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview126/v4/f3/b0/73/f3b073f5-f84b-88d5-9d46-066aa152d606/mzaf_13123944415807399306.plus.aac.p.m4a"},
        {"title": "Maate Vinadhuga (From \"Taxiwaala\")", "artist": "Sid Sriram & Jakes Bejoy", "duration": "4:34", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music125/v4/94/1d/a0/941da079-ee93-ce60-6340-3c7d0f7633a3/cover.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview125/v4/e5/59/89/e55989e2-d596-f94d-440a-5c1cf25ae90e/mzaf_6950280456108137397.plus.aac.p.m4a"},
        {"title": "Fear Song (From \"Devara Part 1\")", "artist": "Anirudh Ravichander & Ramajogayya Sastry", "duration": "3:17", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music221/v4/1d/c6/af/1dc6af82-69e9-5341-5010-a9223fc25709/8903431001368_cover.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/9e/79/f1/9e79f18a-ea35-430c-43f1-d07eb021e176/mzaf_10335035548679698944.plus.aac.p.m4a"},
        {"title": "Samajavaragamana (From \"Ala Vaikunthapurramuloo\")", "artist": "S.S. Thaman & Sid Sriram", "duration": "3:34", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music124/v4/53/98/c1/5398c1cf-7c16-24a6-bfa3-391dc6015376/cover.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview125/v4/3a/4b/e7/3a4be72b-7724-7d3b-47bd-1f064246fe76/mzaf_3926624661015484703.plus.aac.p.m4a"}
    ],
    "Hindi": [
        {"title": "Kesariya (From \"Brahmastra\")", "artist": "Pritam, Arijit Singh & Amitabh Bhattacharya", "duration": "4:28", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music112/v4/9f/13/ca/9f13ca3b-e533-03e0-f19a-f0aaa774581d/196589311191.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/38/4c/5c/384c5c8f-3ff8-e457-b2f7-3158ce108649/mzaf_12389299033886433185.plus.aac.p.m4a"},
        {"title": "Tum Se Hi (From \"Jab We Met\")", "artist": "Pritam & Mohit Chauhan", "duration": "5:23", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music118/v4/64/73/b3/6473b306-bf25-5460-6060-f561ee6dd7fa/source/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview115/v4/71/ea/09/71ea0907-8898-1e42-7801-1b072d6ffbc2/mzaf_11306915159495861118.plus.aac.p.m4a"},
        {"title": "Soniyo (From \"Raaz - The Mystery Continues\")", "artist": "Raju Singh, Sonu Nigam & Shreya Ghoshal", "duration": "5:29", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/77/4d/9f/774d9f5c-830a-c140-f1ae-6e637dc9af14/888880931542.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/19/51/ac/1951ac5b-81c8-72ea-ffe5-31e1a3369d9b/mzaf_17405745395809731793.plus.aac.p.m4a"}
    ],
    "Tamil": [
        {"title": "Neeyum Naanum (From \"Naanum Rowdy Dhaan\")", "artist": "Anirudh Ravichander & Neeti Mohan", "duration": "5:02", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music128/v4/bf/25/71/bf2571c4-9df2-aa00-8438-e6b7617c093a/source/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview128/v4/c3/ff/a6/c3ffa691-e407-3e0e-ce9c-c906666191ef/mzaf_7190040409395232971.plus.aac.p.m4a"}
    ],
    "Kannada": [
        {"title": "Singara Siriye (From \"Kantara\")", "artist": "Vijay Prakash & Ananya Bhat", "duration": "4:42", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music112/v4/4a/1b/ee/4a1bee90-87ef-e5b0-df2b-18a7d32a9eb7/source/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview112/v4/cb/21/57/cb215707-160a-0105-0e1b-8ca080352ef2/mzaf_14959085816912389650.plus.aac.p.m4a"},
        {"title": "KGF Theme (From \"K.G.F: Chapter 1\")", "artist": "Ravi Basrur", "duration": "3:45", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/65/56/67/655667a4-e9fb-ee59-b1d5-bc4fb949d03d/source/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview115/v4/bc/d0/0d/bcd00d41-477d-c200-a6ff-8451f28b4952/mzaf_10034444583151829676.plus.aac.p.m4a"}
    ],
    "Malayalam": [
        {"title": "Darshana (From \"Hridayam\")", "artist": "Hesham Abdul Wahab & Darshana Rajendran", "duration": "3:45", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music125/v4/47/f3/f1/47f3f1ec-6078-4355-08e0-16bb21558bf2/source/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview125/v4/7e/17/2d/7e172dc7-28d5-1bdf-a720-357ea1ae74cb/mzaf_16238612140417721110.plus.aac.p.m4a"},
        {"title": "Malare (From \"Premam\")", "artist": "Vijay Yesudas", "duration": "5:16", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music2/v4/6f/3c/cd/6f3ccd36-2a0f-0c4e-ce51-5aebcf9e9f84/cover.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/41/59/b4/4159b41b-708b-8140-d758-e8da1ed7bedd/mzaf_7080443034849106781.plus.aac.p.m4a"},
        {"title": "Illuminati (From \"Aavesham\")", "artist": "Sushin Shyam & Dabzee", "duration": "3:13", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music221/v4/88/4e/29/884e290c-29ed-25d5-7b25-243b89097220/cover.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/aa/16/9c/aa169cff-649d-fb1f-468a-e8d9499f0221/mzaf_7041799171869820802.plus.aac.p.m4a"}
    ],
    "Punjabi": [
        {"title": "Pasoori", "artist": "Ali Sethi & Shae Gill", "duration": "3:44", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music116/v4/41/22/e1/4122e118-2e06-44ea-8a5e-2f54817a102a/886449911961.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview116/v4/91/d5/43/91d543ee-1c39-38a4-0c58-bc4f7cbe5b92/mzaf_12984950669145610214.plus.aac.p.m4a"},
        {"title": "Softly", "artist": "Karan Aujla & Ikky", "duration": "2:35", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music126/v4/58/91/9f/58919f2c-e1bb-ec67-2483-3638d1796c99/197189182305.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview126/v4/be/a7/9d/bea79d2b-65c7-9759-aa67-727eb184be53/mzaf_15077464010629731671.plus.aac.p.m4a"}
    ],
    "Korean": [
        {"title": "Spring Day", "artist": "BTS", "duration": "4:34", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/31/6d/8a/316d8a27-eb60-c3d3-7d52-6019550b7ec1/source/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview115/v4/b8/0d/1a/b80d1a49-df63-39d3-5249-14022a106fdf/mzaf_12705139045763071850.plus.aac.p.m4a"},
        {"title": "Through the Night", "artist": "IU", "duration": "4:13", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music114/v4/b9/3e/6c/b93e6c0c-e2f6-cb01-1b91-4560d297a7e8/source/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview114/v4/f4/62/11/f4621183-1628-98e3-0d53-bc2a2f8b50f7/mzaf_17208151478523298710.plus.aac.p.m4a"}
    ],
    "Japanese": [
        {"title": "First Love", "artist": "Hikaru Utada", "duration": "4:17", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music122/v4/3e/2d/71/3e2d711b-7a54-df25-8339-e4d6537bfb1a/196589635037.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview122/v4/71/bd/5e/71bd5ea0-520e-c1d0-1c0e-ee4bdf348e89/mzaf_162589635037.plus.aac.p.m4a"},
        {"title": "Sparkle", "artist": "RADWIMPS", "duration": "6:48", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/0d/67/bf/0d67bf30-4e20-80d5-7119-eb652d5b6e2d/source/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview115/v4/10/a5/d6/10a5d6c8-581d-e465-9831-29e2e2832961/mzaf_4734891040854378129.plus.aac.p.m4a"}
    ],
    "Spanish": [
        {"title": "Despacito", "artist": "Luis Fonsi & Daddy Yankee", "duration": "3:48", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music211/v4/e2/ef/f0/e2eff0bc-c51d-7de5-9280-6891ddcee71b/18UMGIM85289.rgb.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/40/5b/e7/405be722-3ec9-ba27-7469-002182d57b39/mzaf_14120258742032474456.plus.aac.p.m4a"},
        {"title": "Vivir Mi Vida", "artist": "Marc Anthony", "duration": "4:12", "album_image": "https://is1-ssl.mzstatic.com/image/thumb/Music115/v4/f7/24/ce/f724ce48-4d0d-0cbc-3493-3d935142e5e6/886443947238.jpg/500x500bb.jpg", "preview_url": "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/10/fd/bf/10fdbf20-d17d-a8a2-6058-c1ef9f221068/mzaf_9159790581568803090.plus.aac.p.m4a"}
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

def fetch_itunes_tracks(query: str, limit: int = 8, language: str = "English") -> List[dict]:
    try:
        search_term = f"{language} {query}" if language and language != "English" else query
        url = "https://itunes.apple.com/search"
        params = {
            "term": search_term,
            "media": "music",
            "entity": "song",
            "limit": limit
        }
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            tracks = []
            for item in results:
                preview_url = item.get("previewUrl")
                if not preview_url:
                    continue
                # Get high resolution official movie cover poster photo (500x500)
                artwork = item.get("artworkUrl100", "").replace("100x100bb.jpg", "500x500bb.jpg")
                if not artwork:
                    artwork = "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&h=300&fit=crop"
                
                millis = item.get("trackTimeMillis", 0)
                minutes = millis // 60000
                seconds = (millis % 60000) // 1000
                duration_str = f"{minutes}:{seconds:02d}" if millis > 0 else "3:30"
                
                tracks.append({
                    "title": item.get("trackName"),
                    "artist": item.get("artistName"),
                    "duration": duration_str,
                    "album_image": artwork,
                    "preview_url": preview_url,
                    "play_url": item.get("trackViewUrl")
                })
            if tracks:
                return tracks
    except Exception as e:
        print(f"Exception during iTunes track fetch: {e}")
    return []

def fetch_spotify_tracks(query: str, limit: int = 8, language: str = "English") -> List[dict]:
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    search_query = f"{language} {query}" if language and language != "English" else query

    if client_id and client_secret:
        try:
            token = get_spotify_access_token(client_id, client_secret)
            if token:
                search_url = "https://api.spotify.com/v1/search"
                headers = {"Authorization": f"Bearer {token}"}
                params = {"q": search_query, "type": "track", "limit": limit}
                
                search_resp = requests.get(search_url, headers=headers, params=params, timeout=5)
                if search_resp.status_code == 200:
                    items = search_resp.json().get("tracks", {}).get("items", [])
                    tracks = []
                    for item in items:
                        duration_ms = item.get("duration_ms", 0)
                        minutes = duration_ms // 60000
                        seconds = (duration_ms % 60000) // 1000
                        duration_str = f"{minutes}:{seconds:02d}"
                        images = item.get("album", {}).get("images", [])
                        album_img = images[0].get("url") if images else "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=150&h=150&fit=crop"
                        
                        preview_url = item.get("preview_url")
                        tracks.append({
                            "title": item.get("name"),
                            "artist": ", ".join([a.get("name") for a in item.get("artists", [])]),
                            "duration": duration_str,
                            "album_image": album_img,
                            "play_url": item.get("external_urls", {}).get("spotify"),
                            "preview_url": preview_url
                        })
                    # Filter tracks to make sure they have a valid preview URL
                    valid_tracks = [t for t in tracks if t.get("preview_url")]
                    if valid_tracks:
                        return valid_tracks
        except Exception as e:
            print(f"Exception during Spotify fetch: {e}")

    # Primary High-Accuracy Music Provider: iTunes Official API
    itunes_tracks = fetch_itunes_tracks(query, limit, language)
    if itunes_tracks:
        return itunes_tracks

    # Fallback to curated multi-language mock library with official movie posters and audio
    if language in MULTI_LANG_LIBRARY:
        return MULTI_LANG_LIBRARY[language]
    return MOCK_LIBRARY.get(query, MOCK_LIBRARY["playlist_1"])

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found matching that username or email address."
        )
    
    reset_tok = generate_reset_token()
    user.reset_token = reset_tok
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
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
    
    tracks = fetch_spotify_tracks(query, limit=8, language=survey.language_pref)
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
    playlist.updated_at = datetime.utcnow()
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
    playlist_key: Optional[str] = "playlist_1",
    current_user: User = Depends(get_current_user)
):
    playlist_type = playlist_key if playlist_key in PLAYLIST_THEME_MAPPING else "playlist_1"
    theme_info = PLAYLIST_THEME_MAPPING[playlist_type]
    query = theme_info["query"]
    
    tracks = fetch_spotify_tracks(query, limit=8, language=language)
    return {
        "language": language,
        "playlist_key": playlist_type,
        "playlist_name": theme_info["name"],
        "tracks": tracks
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
