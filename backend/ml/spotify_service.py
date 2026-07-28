import os
import time
import requests
from typing import List, Dict, Any, Optional

# Caching structures
_spotify_token_cache = {"token": None, "expires_at": 0}
_track_search_cache = {}
CACHE_TTL_SECONDS = 3600 # 1 hour search cache

# Comprehensive Movie & Landmark Soundtracks across 18 Supported Languages
LANGUAGE_QUERY_MAP = {
    "Telugu": ["Telugu Relaxing Lo-fi", "Telugu Meditation Melody", "Telugu Sleep Songs", "Hi Nanna", "Pushpa 2", "Devara", "RRR", "Ala Vaikunthapurramuloo", "Sid Sriram Hits", "Hesham Abdul Wahab"],
    "Hindi": ["Hindi Meditation", "Hindi Lofi Chill", "Hindi Sleep Music", "Brahmastra", "Animal OST", "Tum Se Hi", "Kesariya", "Arijit Singh Peaceful", "Pritam Melodies"],
    "Tamil": ["Tamil Sleep Music", "Tamil Relaxing Melody", "Tamil Meditation", "Leo OST", "Jailer", "Anirudh Melodies", "A.R. Rahman Tamil Chill", "Neeyum Naanum"],
    "Kannada": ["Kannada Devotional", "Kannada Relaxing Melody", "KGF Chapter 2", "Kantara OST", "777 Charlie", "Sanjith Hegde Hits"],
    "Malayalam": ["Malayalam Meditation", "Malayalam Lofi Melody", "Hridayam OST", "Manjummel Boys", "Premam Melodies", "Hesham Abdul Wahab Malayalam"],
    "Punjabi": ["Punjabi Lofi Chill", "Punjabi Acoustic Soft", "Qismat OST", "Diljit Dosanjh Soft", "B Praak Melodies"],
    "Marathi": ["Marathi Devotional Melody", "Marathi Soft Acoustic", "Sairat OST", "Ajay Atul Soft Hits"],
    "Gujarati": ["Gujarati Folk Chill", "Gujarati Devotional Meditation", "Gujarati Soft Melody"],
    "Bengali": ["Bengali Acoustic Lofi", "Bengali Rabindra Sangeet Chill", "Arijit Singh Bengali Soft"],
    "Urdu": ["Urdu Sufi Meditation", "Urdu Acoustic Ghazal", "Coke Studio Pakistan Chill"],
    "Japanese": ["Japanese Anime Lofi", "Japanese Zen Meditation", "Studio Ghibli Piano Relax"],
    "Korean": ["Korean Drama OST Lofi", "K-Pop Chill Ballad", "IU Soft Melodies", "Korean Piano Sleep"],
    "Chinese": ["Chinese Guzheng Meditation", "Chinese Bamboo Flute Relax", "Mandopop Acoustic Chill"],
    "Spanish": ["Spanish Acoustic Chill", "Guitarra Espanola Relax", "Latino Lofi Beats"],
    "French": ["French Cafe Accordion Chill", "French Acoustic Pop Soft", "Chanson Francaise Relax"],
    "German": ["German Classical Healing", "German Acoustic Chill", "Hans Zimmer Soundtrack"],
    "Italian": ["Italian Opera Piano Soft", "Italian Acoustic Melodies", "Ludovico Einaudi Piano"],
    "English": ["English Focus Instrumental", "Lo-fi Hip Hop Chill Beats", "Acoustic Guitar Relax", "Deep Focus Binaural Beats", "Peaceful Piano Sleep"]
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
        print(f"Spotify token request error: {e}")
    return None

def make_yt_url(title: str, artist: str) -> str:
    """Generate YouTube search URL for playback fallback."""
    q = requests.utils.quote(f"{artist} {title}".strip())
    return f"https://www.youtube.com/results?search_query={q}"

def make_yt_embed_url(title: str, artist: str) -> str:
    """Generate YouTube embed search URL."""
    q = requests.utils.quote(f"{artist} {title}".strip())
    return f"https://www.youtube.com/embed?listType=search&list={q}"

def estimate_audio_features(therapy_category: str, genre: str) -> Dict[str, float]:
    """Estimate audio features (Energy, Valence, Danceability, Tempo, Acousticness, Instrumentalness, Speechiness) based on therapy profile."""
    t_cat = (therapy_category or "").lower()
    if "sleep" in t_cat or "meditation" in t_cat:
        return {"energy": 0.20, "valence": 0.35, "danceability": 0.25, "tempo": 65.0, "acousticness": 0.85, "instrumentalness": 0.80, "speechiness": 0.05}
    elif "anxiety" in t_cat or "stress" in t_cat:
        return {"energy": 0.30, "valence": 0.45, "danceability": 0.35, "tempo": 75.0, "acousticness": 0.75, "instrumentalness": 0.65, "speechiness": 0.08}
    elif "focus" in t_cat:
        return {"energy": 0.40, "valence": 0.50, "danceability": 0.30, "tempo": 90.0, "acousticness": 0.60, "instrumentalness": 0.85, "speechiness": 0.05}
    elif "workout" in t_cat or "motivation" in t_cat:
        return {"energy": 0.88, "valence": 0.80, "danceability": 0.82, "tempo": 128.0, "acousticness": 0.15, "instrumentalness": 0.10, "speechiness": 0.12}
    elif "healing" in t_cat or "relaxation" in t_cat:
        return {"energy": 0.35, "valence": 0.60, "danceability": 0.40, "tempo": 80.0, "acousticness": 0.70, "instrumentalness": 0.50, "speechiness": 0.06}
    else: # Happiness / General
        return {"energy": 0.65, "valence": 0.75, "danceability": 0.65, "tempo": 105.0, "acousticness": 0.40, "instrumentalness": 0.20, "speechiness": 0.08}

class SpotifyService:
    """Spotify Search & Audio Metadata Fetching Service with fallbacks."""

    def search_tracks(
        self,
        language: str,
        therapy_category: str,
        genre: str,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Search tracks using exact format: 'Language + Therapy + Genre'
        e.g. 'Telugu Relaxing Lo-fi', 'Hindi Meditation', 'Tamil Sleep Music'
        """
        cache_key = f"{language}_{therapy_category}_{genre}_{limit}"
        now = time.time()
        if cache_key in _track_search_cache:
            c_time, c_data = _track_search_cache[cache_key]
            if now - c_time < CACHE_TTL_SECONDS:
                return c_data

        # Construct primary search query format
        query_str = f"{language} {therapy_category} {genre}".strip()

        token = get_spotify_access_token()
        tracks = []
        if token:
            try:
                url = "https://api.spotify.com/v1/search"
                headers = {"Authorization": f"Bearer {token}"}
                params = {"q": query_str, "type": "track", "limit": limit, "market": "US"}
                resp = requests.get(url, headers=headers, params=params, timeout=6)
                if resp.status_code == 200:
                    items = resp.json().get("tracks", {}).get("items", [])
                    for item in items:
                        t_name = item.get("name", "")
                        artists = [a.get("name") for a in item.get("artists", [])]
                        t_artist = ", ".join(artists) if artists else "Unknown Artist"
                        album = item.get("album", {})
                        images = album.get("images", [])
                        album_img = images[0].get("url") if images else "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&h=300&fit=crop"
                        millis = item.get("duration_ms", 0)
                        minutes = millis // 60000
                        seconds = (millis % 60000) // 1000
                        dur_str = f"{minutes}:{seconds:02d}"
                        
                        audio_feat = estimate_audio_features(therapy_category, genre)

                        tracks.append({
                            "title": t_name,
                            "artist": t_artist,
                            "album": album.get("name", "Single"),
                            "language": language,
                            "genre": genre,
                            "therapy_category": therapy_category,
                            "duration": dur_str,
                            "release_year": album.get("release_date", "")[:4] or "2024",
                            "album_image": album_img,
                            "preview_url": item.get("preview_url"),
                            "play_url": item.get("external_urls", {}).get("spotify"),
                            "youtube_search_url": make_yt_url(t_name, t_artist),
                            "embed_url": make_yt_embed_url(t_name, t_artist),
                            "popularity": item.get("popularity", 50),
                            "audio_features": audio_feat
                        })
            except Exception as e:
                print(f"Spotify search error: {e}")

        # Fallback to iTunes API if Spotify returns insufficient tracks
        if len(tracks) < 10:
            itunes_tracks = self._fetch_itunes_fallback(query_str, language, therapy_category, genre, limit)
            seen = {(t["title"].lower(), t["artist"].lower()) for t in tracks}
            for it in itunes_tracks:
                if (it["title"].lower(), it["artist"].lower()) not in seen:
                    tracks.append(it)
                    seen.add((it["title"].lower(), it["artist"].lower()))

        # Fallback to Deezer API
        if len(tracks) < 10:
            deezer_tracks = self._fetch_deezer_fallback(query_str, language, therapy_category, genre, limit)
            seen = {(t["title"].lower(), t["artist"].lower()) for t in tracks}
            for dt in deezer_tracks:
                if (dt["title"].lower(), dt["artist"].lower()) not in seen:
                    tracks.append(dt)
                    seen.add((dt["title"].lower(), dt["artist"].lower()))

        _track_search_cache[cache_key] = (now, tracks)
        return tracks

    def _fetch_itunes_fallback(self, query: str, language: str, therapy_category: str, genre: str, limit: int) -> List[Dict[str, Any]]:
        """iTunes public search fallback."""
        try:
            url = "https://itunes.apple.com/search"
            params = {"term": query, "media": "music", "entity": "song", "limit": limit}
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                tracks = []
                for item in results:
                    t_name = item.get("trackName", "")
                    t_artist = item.get("artistName", "Unknown Artist")
                    artwork = item.get("artworkUrl100", "").replace("100x100bb.jpg", "500x500bb.jpg")
                    millis = item.get("trackTimeMillis", 0)
                    minutes = millis // 60000
                    seconds = (millis % 60000) // 1000
                    dur_str = f"{minutes}:{seconds:02d}"
                    audio_feat = estimate_audio_features(therapy_category, genre)

                    tracks.append({
                        "title": t_name,
                        "artist": t_artist,
                        "album": item.get("collectionName", "Single"),
                        "language": language,
                        "genre": genre,
                        "therapy_category": therapy_category,
                        "duration": dur_str,
                        "release_year": item.get("releaseDate", "")[:4] or "2023",
                        "album_image": artwork or "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&h=300&fit=crop",
                        "preview_url": item.get("previewUrl"),
                        "play_url": item.get("trackViewUrl"),
                        "youtube_search_url": make_yt_url(t_name, t_artist),
                        "embed_url": make_yt_embed_url(t_name, t_artist),
                        "popularity": 60,
                        "audio_features": audio_feat
                    })
                return tracks
        except Exception:
            pass
        return []

    def _fetch_deezer_fallback(self, query: str, language: str, therapy_category: str, genre: str, limit: int) -> List[Dict[str, Any]]:
        """Deezer public search fallback."""
        try:
            url = "https://api.deezer.com/search"
            params = {"q": query, "limit": limit, "order": "RANKING"}
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                results = resp.json().get("data", [])
                tracks = []
                for item in results:
                    t_name = item.get("title", "")
                    artist_obj = item.get("artist", {})
                    t_artist = artist_obj.get("name", "Unknown Artist")
                    album_obj = item.get("album", {})
                    cover = album_obj.get("cover_xl") or album_obj.get("cover_big") or "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&h=300&fit=crop"
                    duration_s = item.get("duration", 0)
                    minutes = duration_s // 60
                    seconds = duration_s % 60
                    dur_str = f"{minutes}:{seconds:02d}"
                    audio_feat = estimate_audio_features(therapy_category, genre)

                    tracks.append({
                        "title": t_name,
                        "artist": t_artist,
                        "album": album_obj.get("title", "Single"),
                        "language": language,
                        "genre": genre,
                        "therapy_category": therapy_category,
                        "duration": dur_str,
                        "release_year": "2024",
                        "album_image": cover,
                        "preview_url": item.get("preview"),
                        "play_url": item.get("link"),
                        "youtube_search_url": make_yt_url(t_name, t_artist),
                        "embed_url": make_yt_embed_url(t_name, t_artist),
                        "popularity": 55,
                        "audio_features": audio_feat
                    })
                return tracks
        except Exception:
            pass
        return []
