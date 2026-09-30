import os
import time
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus
from backend.ml.language_verifier import LanguageVerifier

# In-memory caches for maximum speed and zero duplicate API calls (Requirement 13)
_spotify_token_cache = {"token": None, "expires_at": 0}
_search_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 3600

THERAPY_QUERY_DESCRIPTORS = {
    "Sleep Therapy": ["Sleep Music", "Deep Sleep", "Bedtime Lofi", "Calming"],
    "Anxiety Relief": ["Anxiety Relief", "Calming Melody", "Peaceful Instrumental"],
    "Stress Relief": ["Stress Relief", "De-stress", "Soothing Acoustic", "Relaxing"],
    "Meditation": ["Meditation", "Mindfulness", "Flute Meditation", "Zen"],
    "Relaxation": ["Relaxing", "Chill Melody", "Soft Acoustic", "Unwind"],
    "Focus": ["Focus Instrumental", "Study Beats", "Deep Focus", "Piano Ambient"],
    "Motivation": ["Motivational", "Uplifting", "Inspiring Beats"],
    "Workout": ["Workout", "Gym Energy", "High Energy Beats", "Dance Workout"],
    "Emotional Healing": ["Emotional Healing", "Soulful Melody", "Heartfelt Acoustic"],
    "Happiness": ["Feel Good", "Upbeat Joy", "Happy Vibes"]
}

def get_spotify_access_token() -> Optional[str]:
    """Retrieve Spotify access token using Client Credentials Flow with caching."""
    now = time.time()
    if _spotify_token_cache["token"] and now < _spotify_token_cache["expires_at"] - 60:
        return _spotify_token_cache["token"]

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None

    try:
        url = "https://accounts.spotify.com/api/token"
        response = requests.post(
            url,
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)
            _spotify_token_cache["token"] = token
            _spotify_token_cache["expires_at"] = now + expires_in
            return token
    except Exception as e:
        print(f"Spotify token request note: {e}")
    return None

def make_yt_url(title: str, artist: str) -> str:
    q = quote_plus(f"{artist} {title}".strip())
    return f"https://www.youtube.com/results?search_query={q}"

def make_yt_embed_url(title: str, artist: str) -> str:
    q = quote_plus(f"{artist} {title}".strip())
    return f"https://www.youtube.com/embed?listType=search&list={q}"

def estimate_audio_features(therapy_category: str, genre: str = "") -> Dict[str, float]:
    """Estimate Spotify audio features when raw features are unavailable (Requirement 6)."""
    t_cat = (therapy_category or "").lower()
    gen = (genre or "").lower()

    if "sleep" in t_cat:
        return {"energy": 0.18, "valence": 0.30, "danceability": 0.20, "tempo": 62.0, "acousticness": 0.88, "instrumentalness": 0.82, "speechiness": 0.03}
    elif "meditation" in t_cat:
        return {"energy": 0.15, "valence": 0.35, "danceability": 0.15, "tempo": 58.0, "acousticness": 0.92, "instrumentalness": 0.88, "speechiness": 0.03}
    elif "anxiety" in t_cat:
        return {"energy": 0.25, "valence": 0.42, "danceability": 0.30, "tempo": 72.0, "acousticness": 0.80, "instrumentalness": 0.70, "speechiness": 0.04}
    elif "stress" in t_cat:
        return {"energy": 0.30, "valence": 0.45, "danceability": 0.35, "tempo": 78.0, "acousticness": 0.75, "instrumentalness": 0.60, "speechiness": 0.05}
    elif "focus" in t_cat:
        return {"energy": 0.42, "valence": 0.50, "danceability": 0.28, "tempo": 88.0, "acousticness": 0.65, "instrumentalness": 0.85, "speechiness": 0.04}
    elif "workout" in t_cat:
        return {"energy": 0.90, "valence": 0.82, "danceability": 0.84, "tempo": 130.0, "acousticness": 0.10, "instrumentalness": 0.08, "speechiness": 0.10}
    elif "motivation" in t_cat:
        return {"energy": 0.78, "valence": 0.72, "danceability": 0.68, "tempo": 115.0, "acousticness": 0.25, "instrumentalness": 0.15, "speechiness": 0.08}
    elif "emotional" in t_cat:
        return {"energy": 0.38, "valence": 0.40, "danceability": 0.38, "tempo": 74.0, "acousticness": 0.72, "instrumentalness": 0.45, "speechiness": 0.05}
    elif "happiness" in t_cat:
        return {"energy": 0.72, "valence": 0.85, "danceability": 0.75, "tempo": 120.0, "acousticness": 0.22, "instrumentalness": 0.10, "speechiness": 0.07}
    else:
        # Relaxation default
        return {"energy": 0.35, "valence": 0.55, "danceability": 0.45, "tempo": 85.0, "acousticness": 0.68, "instrumentalness": 0.55, "speechiness": 0.05}

class SpotifyService:
    """
    Intelligent Multi-Language Search Engine (Requirements 4, 5, 6, 13).
    Constructs targeted queries in format: '<Language> + <Therapy Descriptor> + <Genre>'
    (e.g., 'Telugu Relaxing Lo-fi', 'Hindi Meditation', 'Tamil Sleep Music').
    """

    def search_tracks(
        self,
        language: str,
        therapy_category: str,
        genre: str = "Lo-fi",
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Search tracks using structured 'Language + Therapy + Genre' queries.
        Enforces strict language verification and query response caching.
        """
        target_lang = (language or "English").strip().title()
        t_cat = therapy_category or "Relaxation"
        clean_genre = (genre or "Lo-fi").strip()

        # Cache check
        cache_key = f"{target_lang}::{t_cat}::{clean_genre}::{limit}"
        now = time.time()
        if cache_key in _search_cache:
            entry = _search_cache[cache_key]
            if now - entry["timestamp"] < CACHE_TTL_SECONDS:
                return entry["data"]

        # Construct specific Language + Therapy + Genre queries (Requirement 4)
        descriptors = THERAPY_QUERY_DESCRIPTORS.get(t_cat, ["Relaxing", "Therapy"])
        primary_desc = descriptors[0]
        secondary_desc = descriptors[1] if len(descriptors) > 1 else "Music"

        search_queries = [
            f"{target_lang} {primary_desc} {clean_genre}".strip(),
            f"{target_lang} {secondary_desc}".strip(),
            f"{target_lang} {clean_genre} songs".strip(),
            f"{target_lang} {t_cat}".strip()
        ]

        verified_tracks: List[Dict[str, Any]] = []
        seen_keys = set()

        token = get_spotify_access_token()
        if token:
            for query_str in search_queries:
                if len(verified_tracks) >= limit:
                    break
                try:
                    url = "https://api.spotify.com/v1/search"
                    headers = {"Authorization": f"Bearer {token}"}
                    market = "IN" if target_lang in [
                        "Telugu", "Hindi", "Tamil", "Kannada", "Malayalam",
                        "Punjabi", "Marathi", "Gujarati", "Bengali", "Urdu"
                    ] else ("JP" if target_lang == "Japanese" else ("KR" if target_lang == "Korean" else "US"))

                    params = {"q": query_str, "type": "track", "limit": 20, "market": market}
                    resp = requests.get(url, headers=headers, params=params, timeout=5)
                    if resp.status_code == 200:
                        items = resp.json().get("tracks", {}).get("items", [])
                        for item in items:
                            t_name = item.get("name", "")
                            artists = [a.get("name") for a in item.get("artists", [])]
                            t_artist = ", ".join(artists) if artists else "Unknown Artist"
                            t_key = (t_name.lower().strip(), t_artist.lower().strip())

                            if t_key in seen_keys:
                                continue

                            album_obj = item.get("album", {})
                            images = album_obj.get("images", [])
                            album_img = images[0].get("url") if images else "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&h=300&fit=crop"
                            millis = item.get("duration_ms", 0)
                            minutes = millis // 60000
                            seconds = (millis % 60000) // 1000
                            dur_str = f"{minutes}:{seconds:02d}"

                            candidate = {
                                "title": t_name,
                                "artist": t_artist,
                                "album": album_obj.get("name", "Single"),
                                "language": target_lang,
                                "genre": clean_genre,
                                "therapy_category": t_cat,
                                "duration": dur_str,
                                "release_year": album_obj.get("release_date", "")[:4] or "2024",
                                "album_image": album_img,
                                "preview_url": item.get("preview_url"),
                                "play_url": item.get("external_urls", {}).get("spotify"),
                                "spotify_search_url": f"https://open.spotify.com/search/{quote_plus(f'{t_name} {t_artist}')}",
                                "youtube_search_url": make_yt_url(t_name, t_artist),
                                "embed_url": make_yt_embed_url(t_name, t_artist),
                                "popularity": item.get("popularity", 50),
                                "audio_features": estimate_audio_features(t_cat, clean_genre),
                                "is_search_result": True,
                                "is_spotify": True
                            }

                            # Strict language verification (Requirement 5)
                            if LanguageVerifier.verify_track_language(candidate, target_lang):
                                seen_keys.add(t_key)
                                verified_tracks.append(candidate)
                except Exception as e:
                    print(f"Spotify search error for '{query_str}': {e}")

        # Fallback to iTunes API with structured query formatting & strict language verification
        if len(verified_tracks) < limit:
            itunes_tracks = self._fetch_itunes_tracks(
                language=target_lang,
                therapy_category=t_cat,
                genre=clean_genre,
                limit=limit - len(verified_tracks)
            )
            for it in itunes_tracks:
                t_key = (it["title"].lower().strip(), it["artist"].lower().strip())
                if t_key not in seen_keys and LanguageVerifier.verify_track_language(it, target_lang):
                    seen_keys.add(t_key)
                    verified_tracks.append(it)

        # Store in cache
        _search_cache[cache_key] = {
            "timestamp": now,
            "data": verified_tracks
        }
        return verified_tracks

    def _fetch_itunes_tracks(
        self,
        language: str,
        therapy_category: str,
        genre: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Fetch authentic tracks via iTunes search API using Language + Therapy + Genre query."""
        verified = []
        descriptors = THERAPY_QUERY_DESCRIPTORS.get(therapy_category, ["Relaxing", "Music"])

        if language and language.lower() != "english":
            terms = [
                f"{language} {descriptors[0]} {genre}".strip(),
                f"{language} {therapy_category}".strip(),
                f"{language} melody songs".strip(),
                f"{language} hits".strip()
            ]
        else:
            terms = [
                f"{descriptors[0]} {genre}".strip(),
                f"{therapy_category} {genre}".strip(),
                f"{genre} relaxation".strip()
            ]

        for query_str in terms:
            if len(verified) >= limit:
                break
            try:
                url = "https://itunes.apple.com/search"
                params = {"term": query_str, "media": "music", "entity": "song", "limit": 25}
                resp = requests.get(url, params=params, timeout=5)
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    for item in results:
                        t_name = item.get("trackName", "")
                        t_artist = item.get("artistName", "Unknown Artist")
                        if not t_name:
                            continue

                        artwork = item.get("artworkUrl100", "").replace("100x100bb.jpg", "500x500bb.jpg")
                        millis = item.get("trackTimeMillis", 0)
                        minutes = millis // 60000
                        seconds = (millis % 60000) // 1000
                        dur_str = f"{minutes}:{seconds:02d}"

                        sp_url = f"https://open.spotify.com/search/{quote_plus(f'{t_name} {t_artist}')}"
                        candidate = {
                            "title": t_name,
                            "artist": t_artist,
                            "album": item.get("collectionName", "Single"),
                            "language": language,
                            "genre": genre,
                            "therapy_category": therapy_category,
                            "duration": dur_str,
                            "release_year": item.get("releaseDate", "")[:4] or "2024",
                            "album_image": artwork or "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&h=300&fit=crop",
                            "preview_url": item.get("previewUrl"),
                            "play_url": sp_url,
                            "spotify_search_url": sp_url,
                            "youtube_search_url": make_yt_url(t_name, t_artist),
                            "embed_url": make_yt_embed_url(t_name, t_artist),
                            "popularity": 60,
                            "audio_features": estimate_audio_features(therapy_category, genre),
                            "is_search_result": True,
                            "is_itunes": True
                        }

                        if LanguageVerifier.verify_track_language(candidate, language):
                            verified.append(candidate)
            except Exception as e:
                print(f"iTunes query note for '{query_str}': {e}")

        return verified
