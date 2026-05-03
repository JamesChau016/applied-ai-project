"""Tests for TheAudioDB API client."""

import json
from unittest.mock import patch, MagicMock
from src.audiodb_client import AudioDBClient, _safe_int, _safe_float


SAMPLE_TRACK_RAW = {
    "idTrack": "34329073",
    "strTrack": "Fix You",
    "strArtist": "Coldplay",
    "strGenre": "Alternative Rock",
    "strMood": "Sad",
    "strStyle": "Rock/Pop",
    "strTheme": "Heartbreak",
    "intDuration": "277400",
    "intTotalPlays": "25213430",
    "intTotalListeners": "2521477",
    "intScore": "9.8",
    "intLoved": "5",
    "strMusicVid": "https://www.youtube.com/watch?v=k4V3Mo61fJM",
}

SAMPLE_ARTIST_RAW = {
    "idArtist": "111239",
    "strArtist": "Coldplay",
    "strGenre": "Alternative Rock",
    "strMood": "Happy",
    "strStyle": "Rock/Pop",
}


class TestNormalizeTrack:
    def test_maps_all_fields(self):
        result = AudioDBClient._normalize_track(SAMPLE_TRACK_RAW)
        assert result["id"] == "34329073"
        assert result["title"] == "Fix You"
        assert result["artist"] == "Coldplay"
        assert result["genre"] == "Alternative Rock"
        assert result["mood"] == "Sad"
        assert result["style"] == "Rock/Pop"
        assert result["theme"] == "Heartbreak"
        assert result["duration_ms"] == 277400
        assert result["total_plays"] == 25213430
        assert result["total_listeners"] == 2521477
        assert result["score"] == 9.8
        assert result["loved"] == 5
        assert result["source"] == "audiodb"

    def test_handles_missing_fields(self):
        result = AudioDBClient._normalize_track({})
        assert result["title"] == "Unknown"
        assert result["artist"] == "Unknown"
        assert result["genre"] == ""
        assert result["mood"] == ""
        assert result["duration_ms"] == 0
        assert result["source"] == "audiodb"

    def test_handles_none_values(self):
        raw = {"strTrack": "Test", "intDuration": None, "intScore": None}
        result = AudioDBClient._normalize_track(raw)
        assert result["duration_ms"] == 0
        assert result["score"] == 0.0


class TestSafeConversions:
    def test_safe_int_valid(self):
        assert _safe_int("42") == 42
        assert _safe_int(42) == 42

    def test_safe_int_invalid(self):
        assert _safe_int(None) == 0
        assert _safe_int("abc") == 0

    def test_safe_float_valid(self):
        assert _safe_float("9.8") == 9.8
        assert _safe_float(9.8) == 9.8

    def test_safe_float_invalid(self):
        assert _safe_float(None) == 0.0
        assert _safe_float("abc") == 0.0


class TestSearchArtist:
    @patch("src.audiodb_client.urllib.request.urlopen")
    def test_returns_artist_on_success(self, mock_urlopen):
        response_data = json.dumps({"artists": [SAMPLE_ARTIST_RAW]}).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = response_data
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        client = AudioDBClient()
        client._last_request_time = 0
        result = client.search_artist("Coldplay")
        assert result is not None
        assert result["strArtist"] == "Coldplay"

    @patch("src.audiodb_client.urllib.request.urlopen")
    def test_returns_none_on_empty(self, mock_urlopen):
        response_data = json.dumps({"artists": None}).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = response_data
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        client = AudioDBClient()
        client._last_request_time = 0
        result = client.search_artist("NonexistentArtist")
        assert result is None


class TestGetTopTracks:
    @patch("src.audiodb_client.urllib.request.urlopen")
    def test_returns_normalized_tracks(self, mock_urlopen):
        response_data = json.dumps({"track": [SAMPLE_TRACK_RAW]}).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = response_data
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        client = AudioDBClient()
        client._last_request_time = 0
        tracks = client.get_top_tracks("Coldplay")
        assert len(tracks) == 1
        assert tracks[0]["title"] == "Fix You"
        assert tracks[0]["source"] == "audiodb"

    @patch("src.audiodb_client.urllib.request.urlopen")
    def test_returns_empty_on_no_tracks(self, mock_urlopen):
        response_data = json.dumps({"track": None}).encode()
        mock_resp = MagicMock()
        mock_resp.read.return_value = response_data
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        client = AudioDBClient()
        client._last_request_time = 0
        tracks = client.get_top_tracks("Unknown")
        assert tracks == []
