"""Thin client for TheAudioDB free API (v1)."""

import json
import time
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, List, Optional


class AudioDBClient:
    """Client for TheAudioDB API v1 (free tier, key '123', 30 req/min)."""

    BASE_URL = "https://www.theaudiodb.com/api/v1/json/{api_key}"

    def __init__(self, api_key: str = "123"):
        self.base_url = self.BASE_URL.format(api_key=api_key)
        self._last_request_time = 0.0

    def _rate_limit(self) -> None:
        """Enforce ~2s between requests to stay within 30 req/min."""
        elapsed = time.time() - self._last_request_time
        if elapsed < 2.0:
            time.sleep(2.0 - elapsed)

    def _get(self, endpoint: str, params: Dict[str, str]) -> Optional[dict]:
        """Make a GET request and return parsed JSON, or None on failure."""
        self._rate_limit()
        query = urllib.parse.urlencode(params)
        url = f"{self.base_url}/{endpoint}?{query}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MusicRecommender/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                self._last_request_time = time.time()
                return json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
            print(f"AudioDB API error: {exc}")
            return None

    def search_artist(self, artist_name: str) -> Optional[dict]:
        """Search for an artist by name. Returns artist dict or None."""
        data = self._get("search.php", {"s": artist_name})
        if data and data.get("artists"):
            return data["artists"][0]
        return None

    def get_top_tracks(self, artist_name: str) -> List[dict]:
        """Get top 10 tracks for an artist. Returns list of normalized track dicts."""
        data = self._get("track-top10.php", {"s": artist_name})
        if not data or not data.get("track"):
            return []
        return [self._normalize_track(t) for t in data["track"]]

    def search_track(self, artist: str, track: str) -> Optional[dict]:
        """Search for a specific track by artist and title."""
        data = self._get("searchtrack.php", {"s": artist, "t": track})
        if data and data.get("track"):
            return self._normalize_track(data["track"][0])
        return None

    @staticmethod
    def _normalize_track(raw: dict) -> dict:
        """Map TheAudioDB track fields to our common schema."""
        return {
            "id": raw.get("idTrack"),
            "title": raw.get("strTrack", "Unknown"),
            "artist": raw.get("strArtist", "Unknown"),
            "genre": raw.get("strGenre", ""),
            "mood": raw.get("strMood", ""),
            "style": raw.get("strStyle", ""),
            "theme": raw.get("strTheme", ""),
            "duration_ms": _safe_int(raw.get("intDuration")),
            "total_plays": _safe_int(raw.get("intTotalPlays")),
            "total_listeners": _safe_int(raw.get("intTotalListeners")),
            "score": _safe_float(raw.get("intScore")),
            "loved": _safe_int(raw.get("intLoved")),
            "music_video": raw.get("strMusicVid", ""),
            "source": "audiodb",
        }


def _safe_int(val) -> int:
    """Convert a value to int, returning 0 on failure."""
    try:
        return int(val) if val is not None else 0
    except (ValueError, TypeError):
        return 0


def _safe_float(val) -> float:
    """Convert a value to float, returning 0.0 on failure."""
    try:
        return float(val) if val is not None else 0.0
    except (ValueError, TypeError):
        return 0.0
