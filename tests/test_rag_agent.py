"""Tests for the RAG recommendation agent."""

import json
import numpy as np
from unittest.mock import MagicMock, patch
from src.rag_agent import (
    ProfileAnalyzer,
    SongRetriever,
    EmbeddingModel,
    RAGRecommender,
    _song_to_text,
    _profile_to_text,
    _generate_reason,
    _load_json,
)


PLAYLIST_PATH = "data/playlist.json"
SONGS_CSV_PATH = "data/songs.csv"


class TestProfileAnalyzer:
    def test_extracts_artists(self):
        profile = ProfileAnalyzer.from_playlist(PLAYLIST_PATH, SONGS_CSV_PATH)
        assert "LoRoom" in profile["artists"]
        assert "Paper Lanterns" in profile["artists"]
        assert "Arctic Monkeys" in profile["artists"]

    def test_extracts_top_genres(self):
        profile = ProfileAnalyzer.from_playlist(PLAYLIST_PATH, SONGS_CSV_PATH)
        assert "lofi" in profile["genres"]

    def test_extracts_top_moods(self):
        profile = ProfileAnalyzer.from_playlist(PLAYLIST_PATH, SONGS_CSV_PATH)
        assert "chill" in profile["moods"]

    def test_computes_avg_energy(self):
        profile = ProfileAnalyzer.from_playlist(PLAYLIST_PATH, SONGS_CSV_PATH)
        # Playlist energies: 0.42, 0.35, 0.28, 0.65, 0.89 -> avg = 0.518
        assert 0.4 < profile["avg_energy"] < 0.6

    def test_likes_acoustic(self):
        profile = ProfileAnalyzer.from_playlist(PLAYLIST_PATH, SONGS_CSV_PATH)
        # Acousticness: 0.71, 0.86, 0.92, 0.35, 0.08 -> avg = 0.584 > 0.5
        assert profile["likes_acoustic"] is True

    def test_generates_summary(self):
        profile = ProfileAnalyzer.from_playlist(PLAYLIST_PATH, SONGS_CSV_PATH)
        assert "Favorite artists:" in profile["summary"]
        assert "Top genres:" in profile["summary"]

    def test_empty_playlist(self):
        with patch("src.rag_agent._load_json", return_value=[]):
            profile = ProfileAnalyzer.from_playlist("nonexistent.json")
            assert profile["artists"] == []
            assert profile["avg_energy"] == 0.5


class TestSongToText:
    def test_basic_song(self):
        song = {"title": "Test Song", "artist": "Test Artist", "genre": "rock", "mood": "happy"}
        text = _song_to_text(song)
        assert "Test Song" in text
        assert "Test Artist" in text
        assert "rock" in text
        assert "happy" in text

    def test_with_energy(self):
        song = {"title": "X", "artist": "Y", "energy": 0.2}
        assert "low" in _song_to_text(song)

        song["energy"] = 0.5
        assert "medium" in _song_to_text(song)

        song["energy"] = 0.8
        assert "high" in _song_to_text(song)

    def test_acoustic_label(self):
        song = {"title": "X", "artist": "Y", "acousticness": 0.8}
        assert "acoustic" in _song_to_text(song)

        song["acousticness"] = 0.3
        assert "acoustic" not in _song_to_text(song)


class TestProfileToText:
    def test_basic_profile(self):
        profile = {"genres": ["lofi"], "moods": ["chill"], "avg_energy": 0.4, "likes_acoustic": True}
        text = _profile_to_text(profile)
        assert "lofi" in text
        assert "chill" in text
        assert "acoustic" in text

    def test_with_query(self):
        profile = {"genres": [], "moods": [], "avg_energy": 0.5, "likes_acoustic": False}
        text = _profile_to_text(profile, "something for studying")
        assert "something for studying" in text


class TestGenerateReason:
    def test_genre_match(self):
        song = {"genre": "lofi", "mood": "happy", "artist": "X"}
        profile = {"genres": ["lofi"], "moods": ["chill"], "artists": []}
        reason = _generate_reason(song, profile)
        assert "lofi" in reason

    def test_mood_match(self):
        song = {"genre": "rock", "mood": "chill", "artist": "X"}
        profile = {"genres": ["pop"], "moods": ["chill"], "artists": []}
        reason = _generate_reason(song, profile)
        assert "chill" in reason

    def test_artist_match(self):
        song = {"genre": "rock", "mood": "happy", "artist": "LoRoom"}
        profile = {"genres": ["pop"], "moods": ["sad"], "artists": ["LoRoom"]}
        reason = _generate_reason(song, profile)
        assert "favorite artists" in reason

    def test_fallback_reason(self):
        song = {"genre": "metal", "mood": "aggressive", "artist": "X"}
        profile = {"genres": ["lofi"], "moods": ["chill"], "artists": []}
        reason = _generate_reason(song, profile)
        assert "semantically similar" in reason


class TestSongRetriever:
    def test_retrieves_and_deduplicates(self):
        mock_audiodb = MagicMock()
        mock_audiodb.get_top_tracks.return_value = [
            {"title": "Track A", "artist": "Artist X", "genre": "rock", "mood": "happy"},
            {"title": "Track B", "artist": "Artist X", "genre": "rock", "mood": "sad"},
        ]

        retriever = SongRetriever(audiodb=mock_audiodb, songs_csv_path=SONGS_CSV_PATH)
        profile = {"artists": ["Artist X"]}
        candidates = retriever.retrieve(profile, favorite_ids=set())

        assert len(candidates) >= 2
        mock_audiodb.get_top_tracks.assert_called_once_with("Artist X")

    def test_excludes_favorites_from_local(self):
        mock_audiodb = MagicMock()
        mock_audiodb.get_top_tracks.return_value = []

        retriever = SongRetriever(audiodb=mock_audiodb, songs_csv_path=SONGS_CSV_PATH)
        profile = {"artists": []}
        candidates = retriever.retrieve(profile, favorite_ids={1, 2})

        local_ids = [c["id"] for c in candidates if c.get("source") == "local"]
        assert 1 not in local_ids
        assert 2 not in local_ids


class TestEmbeddingModel:
    def test_encode_returns_embeddings(self):
        mock_st_model = MagicMock()
        mock_st_model.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])

        model = EmbeddingModel(model=mock_st_model)
        result = model.encode(["hello", "world"])
        assert result.shape == (2, 2)
        mock_st_model.encode.assert_called_once()

    def test_similarity_scores(self):
        model = EmbeddingModel()
        query = np.array([1.0, 0.0])
        corpus = np.array([[1.0, 0.0], [0.0, 1.0], [0.707, 0.707]])
        scores = model.similarity(query, corpus)
        assert len(scores) == 3
        assert scores[0] > scores[1]  # identical vector scores higher than orthogonal


class TestRAGRecommender:
    def _make_mock_embedding_model(self):
        """Create a mock embedding model that returns deterministic embeddings."""
        mock = MagicMock()
        # Return different embeddings so similarity varies
        def fake_encode(texts, **kwargs):
            n = len(texts)
            rng = np.random.RandomState(42)
            emb = rng.randn(n, 8)
            norms = np.linalg.norm(emb, axis=1, keepdims=True)
            return emb / norms
        mock.encode = fake_encode
        return EmbeddingModel(model=mock)

    def test_end_to_end_with_mocks(self):
        mock_audiodb = MagicMock()
        mock_audiodb.get_top_tracks.return_value = [
            {"title": "API Song", "artist": "API Artist", "genre": "pop", "mood": "happy"},
        ]

        mock_embedding = self._make_mock_embedding_model()

        agent = RAGRecommender(
            songs_csv_path=SONGS_CSV_PATH,
            playlist_path=PLAYLIST_PATH,
            audiodb=mock_audiodb,
            embedding_model=mock_embedding,
        )
        result = agent.recommend()

        assert "recommendations" in result
        assert len(result["recommendations"]) <= 5
        assert "overall_explanation" in result
        for rec in result["recommendations"]:
            assert "title" in rec
            assert "artist" in rec
            assert "similarity" in rec
            assert "reason" in rec

    def test_with_query(self):
        mock_audiodb = MagicMock()
        mock_audiodb.get_top_tracks.return_value = []

        mock_embedding = self._make_mock_embedding_model()

        agent = RAGRecommender(
            songs_csv_path=SONGS_CSV_PATH,
            playlist_path=PLAYLIST_PATH,
            audiodb=mock_audiodb,
            embedding_model=mock_embedding,
        )
        result = agent.recommend(user_query="upbeat workout music")

        assert "recommendations" in result
        assert len(result["recommendations"]) > 0

    def test_no_candidates(self):
        mock_audiodb = MagicMock()
        mock_audiodb.get_top_tracks.return_value = []

        mock_embedding = self._make_mock_embedding_model()

        # Use a nonexistent CSV so local songs are empty too
        agent = RAGRecommender(
            songs_csv_path="nonexistent.csv",
            playlist_path=PLAYLIST_PATH,
            audiodb=mock_audiodb,
            embedding_model=mock_embedding,
        )
        result = agent.recommend()
        assert result["recommendations"] == []
