import os
import time
import requests
from typing import List, Dict, Any, Optional
from backend.ml.language_verifier import LanguageVerifier

_spotify_token_cache = {"token": None, "expires_at": 0}
_track_search_cache = {}
CACHE_TTL_SECONDS = 3600

def get_spotify_access_token() -> Optional[str]:
    """Retrieve Spotify access token using Client Credentials Flow."""
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
    q = requests.utils.quote(f"{artist} {title}".strip())
    return f"https://www.youtube.com/results?search_query={q}"

def make_yt_embed_url(title: str, artist: str) -> str:
    q = requests.utils.quote(f"{artist} {title}".strip())
    return f"https://www.youtube.com/embed?listType=search&list={q}"

def estimate_audio_features(therapy_category: str, genre: str) -> Dict[str, float]:
    t_cat = (therapy_category or "").lower()
    if "sleep" in t_cat or "meditation" in t_cat:
        return {"energy": 0.20, "valence": 0.35, "danceability": 0.25, "tempo": 65.0, "acousticness": 0.85, "instrumentalness": 0.80, "speechiness": 0.05}
    elif "anxiety" in t_cat or "stress" in t_cat:
        return {"energy": 0.30, "valence": 0.45, "danceability": 0.35, "tempo": 75.0, "acousticness": 0.75, "instrumentalness": 0.65, "speechiness": 0.08}
    elif "focus" in t_cat:
        return {"energy": 0.40, "valence": 0.50, "danceability": 0.30, "tempo": 90.0, "acousticness": 0.60, "instrumentalness": 0.85, "speechiness": 0.05}
    elif "workout" in t_cat or "motivation" in t_cat:
        return {"energy": 0.88, "valence": 0.80, "danceability": 0.82, "tempo": 128.0, "acousticness": 0.15, "instrumentalness": 0.10, "speechiness": 0.12}
    else:
        return {"energy": 0.50, "valence": 0.60, "danceability": 0.50, "tempo": 95.0, "acousticness": 0.50, "instrumentalness": 0.30, "speechiness": 0.07}

class SpotifyService:
    """Spotify Search Engine with strict Language Verification."""

    def search_tracks(
        self,
        language: str,
        therapy_category: str,
        genre: str,
        limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Search tracks using query format: '<Language> + <Genre> + <Therapy>'
        Example: 'Telugu melody', 'Hindi lofi', 'Tamil sleep music', 'Kannada instrumental'
        Verifies every track against LanguageVerifier and discards non-matching language results.
        """
        target_lang = (language or "English").strip()
        cache_key = f"{target_lang}_{therapy_category}_{genre}_{limit}"
        now = time.time()
        if cache_key in _track_search_cache:
            c_time, c_data = _track_search_cache[cache_key]
            if now - c_time < CACHE_TTL_SECONDS:
                return c_data

        # Construct exact search query: <Language> + <Genre> + <Therapy>
        search_terms = [
            f"{target_lang} {genre} {therapy_category}".strip(),
            f"{target_lang} {genre} songs".strip(),
            f"{target_lang} {therapy_category} music".strip(),
            f"{target_lang} relaxing songs".strip()
        ]

        token = get_spotify_access_token()
        verified_tracks = []
        seen_keys = set()

        if token:
            for query_str in search_terms:
                if len(verified_tracks) >= limit:
                    break
                try:
                    url = "https://api.spotify.com/v1/search"
                    headers = {"Authorization": f"Bearer {token}"}
                    params = {"q": query_str, "type": "track", "limit": 20, "market": "IN" if target_lang in ["Telugu", "Hindi", "Tamil", "Kannada", "Malayalam", "Punjabi", "Marathi", "Gujarati", "Bengali"] else "US"}
                    resp = requests.get(url, headers=headers, params=params, timeout=6)
                    if resp.status_code == 200:
                        items = resp.json().get("tracks", {}).get("items", [])
                        for item in items:
                            t_name = item.get("name", "")
                            artists = [a.get("name") for a in item.get("artists", [])]
                            t_artist = ", ".join(artists) if artists else "Unknown Artist"
                            t_key = (t_name.lower(), t_artist.lower())

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
                                "language": target_lang, # Only verified language!
                                "genre": genre,
                                "therapy_category": therapy_category,
                                "duration": dur_str,
                                "release_year": album_obj.get("release_date", "")[:4] or "2024",
                                "album_image": album_img,
                                "preview_url": item.get("preview_url"),
                                "play_url": item.get("external_urls", {}).get("spotify"),
                                "youtube_search_url": make_yt_url(t_name, t_artist),
                                "embed_url": make_yt_embed_url(t_name, t_artist),
                                "popularity": item.get("popularity", 50),
                                "audio_features": estimate_audio_features(therapy_category, genre)
                            }

                            # STRICT VERIFICATION: Discard candidate if language check fails
                            if LanguageVerifier.verify_track_language(candidate, target_lang):
                                seen_keys.add(t_key)
                                verified_tracks.append(candidate)
                except Exception as e:
                    print(f"Spotify search error: {e}")

        # Fallback to iTunes API with strict language verification
        if len(verified_tracks) < limit:
            itunes_tracks = self._fetch_itunes_tracks(target_lang, therapy_category, genre, limit)
            for it in itunes_tracks:
                t_key = (it["title"].lower(), it["artist"].lower())
                if t_key not in seen_keys and LanguageVerifier.verify_track_language(it, target_lang):
                    seen_keys.add(t_key)
                    verified_tracks.append(it)

        _track_search_cache[cache_key] = (now, verified_tracks)
        return verified_tracks

    def _fetch_itunes_tracks(self, language: str, therapy_category: str, genre: str, limit: int) -> List[Dict[str, Any]]:
        """Fetch iTunes tracks with strict language validation."""
        query_str = f"{language} {genre} {therapy_category}".strip()
        verified = []
        try:
            url = "https://itunes.apple.com/search"
            params = {"term": query_str, "media": "music", "entity": "song", "limit": limit}
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                for item in results:
                    t_name = item.get("trackName", "")
                    t_artist = item.get("artistName", "Unknown Artist")
                    artwork = item.get("artworkUrl100", "").replace("100x100bb.jpg", "500x500bb.jpg")
                    millis = item.get("trackTimeMillis", 0)
                    minutes = millis // 60000
                    seconds = (millis % 60000) // 1000
                    dur_str = f"{minutes}:{seconds:02d}"

                    sp_url = f"https://open.spotify.com/search/{requests.utils.quote(f'{t_name} {t_artist}')}"
                    candidate = {
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
                        "play_url": sp_url,
                        "spotify_search_url": sp_url,
                        "youtube_search_url": make_yt_url(t_name, t_artist),
                        "embed_url": make_yt_embed_url(t_name, t_artist),
                        "popularity": 60,
                        "audio_features": estimate_audio_features(therapy_category, genre)
                    }

                    if LanguageVerifier.verify_track_language(candidate, language):
                        verified.append(candidate)
        except Exception as e:
            print(f"iTunes search error: {e}")
        return verified
