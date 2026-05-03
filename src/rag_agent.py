"""RAG (Retrieval-Augmented Generation) agent for music recommendations.

Uses TheAudioDB for song retrieval and sentence-transformers (all-MiniLM-L6-v2)
for semantic similarity-based ranking.
"""

import json
import os
from collections import Counter
from typing import Dict, List, Optional

try:
    from .audiodb_client import AudioDBClient, get_genre_artists
    from .recommender import load_songs
except ImportError:
    from audiodb_client import AudioDBClient, get_genre_artists
    from recommender import load_songs


class ProfileAnalyzer:
    """Analyzes user favorites to derive a taste profile."""

    @staticmethod
    def from_playlist(playlist_path: str, songs_csv_path: str = "data/songs.csv") -> dict:
        """Derive a taste summary from the user's playlist.

        Returns dict with keys: artists, genres, moods, avg_energy,
        likes_acoustic, summary (human-readable).
        """
        playlist = _load_json(playlist_path)
        if not playlist:
            return {
                "artists": [], "genres": [], "moods": [],
                "avg_energy": 0.5, "likes_acoustic": False, "summary": "No favorites found.",
            }

        artists = list({s["artist"] for s in playlist if "artist" in s})
        genres = [s["genre"] for s in playlist if "genre" in s]
        moods = [s["mood"] for s in playlist if "mood" in s]

        genre_counts = Counter(genres)
        mood_counts = Counter(moods)
        top_genres = [g for g, _ in genre_counts.most_common(3)]
        top_moods = [m for m, _ in mood_counts.most_common(3)]

        avg_energy = _avg([s.get("energy", 0.5) for s in playlist])
        avg_acoustic = _avg([s.get("acousticness", 0.5) for s in playlist])

        summary = (
            f"Favorite artists: {', '.join(artists)}. "
            f"Top genres: {', '.join(top_genres)}. "
            f"Top moods: {', '.join(top_moods)}. "
            f"Avg energy: {avg_energy:.2f}. "
            f"{'Prefers acoustic' if avg_acoustic > 0.5 else 'Prefers produced'} sounds."
        )

        return {
            "artists": artists,
            "genres": top_genres,
            "moods": top_moods,
            "avg_energy": avg_energy,
            "likes_acoustic": avg_acoustic > 0.5,
            "summary": summary,
        }


class SongRetriever:
    """Retrieves candidate songs from TheAudioDB and local catalog."""

    def __init__(self, audiodb: Optional[AudioDBClient] = None,
                 songs_csv_path: str = "data/songs.csv"):
        self.audiodb = audiodb or AudioDBClient()
        self.songs_csv_path = songs_csv_path

    def retrieve(self, profile: dict, favorite_ids: set,
                  include_local: bool = True) -> List[dict]:
        """Fetch candidate songs based on user profile.

        Combines TheAudioDB top tracks for favorite artists AND genre-related
        artists with the local catalog.  Excludes songs already in the user's
        favorites.
        """
        candidates = []
        seen_keys = set()
        tried_artists = set()

        def _fetch_artist(artist: str) -> int:
            if artist in tried_artists:
                return 0
            tried_artists.add(artist)
            print(f"  Fetching tracks for '{artist}' from TheAudioDB...")
            tracks = self.audiodb.get_top_tracks(artist)
            added = 0
            for track in tracks:
                key = (track["title"].lower(), track["artist"].lower())
                if key not in seen_keys:
                    seen_keys.add(key)
                    candidates.append(track)
                    added += 1
            return added

        # 1. Fetch top tracks for each favorite artist
        for artist in profile.get("artists", []):
            _fetch_artist(artist)

        # 2. Broaden search: fetch genre-related artists so results aren't
        #    limited to the user's existing favorites.
        for genre in profile.get("genres", []):
            related = get_genre_artists(genre, exclude=tried_artists)
            for artist in related:
                _fetch_artist(artist)

        # 3. Add local catalog songs not already in favorites
        if include_local:
            local_songs = load_songs(self.songs_csv_path)
            for song in local_songs:
                if song["id"] not in favorite_ids:
                    key = (song["title"].lower(), song["artist"].lower())
                    if key not in seen_keys:
                        seen_keys.add(key)
                        song["source"] = "local"
                        candidates.append(song)

        print(f"  Retrieved {len(candidates)} candidate songs total.")
        return candidates


def _song_to_text(song: dict) -> str:
    """Convert a song dict to a descriptive text string for embedding."""
    parts = [f'"{song.get("title", "")}" by {song.get("artist", "")}']
    if song.get("genre"):
        parts.append(f"genre: {song['genre']}")
    if song.get("mood"):
        parts.append(f"mood: {song['mood']}")
    if song.get("style"):
        parts.append(f"style: {song['style']}")
    if song.get("theme"):
        parts.append(f"theme: {song['theme']}")
    if song.get("energy") is not None:
        energy_label = "low" if song["energy"] < 0.4 else "medium" if song["energy"] < 0.7 else "high"
        parts.append(f"energy: {energy_label}")
    if song.get("acousticness") is not None and song["acousticness"] > 0.5:
        parts.append("acoustic")
    return ", ".join(parts)


def _profile_to_text(profile: dict, user_query: str = "") -> str:
    """Convert a taste profile to a descriptive text string for embedding."""
    parts = []
    if user_query:
        parts.append(user_query)
    if profile.get("genres"):
        parts.append(f"genres: {', '.join(profile['genres'])}")
    if profile.get("moods"):
        parts.append(f"moods: {', '.join(profile['moods'])}")
    if profile.get("likes_acoustic"):
        parts.append("acoustic")
    energy = profile.get("avg_energy", 0.5)
    energy_label = "low energy" if energy < 0.4 else "medium energy" if energy < 0.7 else "high energy"
    parts.append(energy_label)
    return ", ".join(parts)


class EmbeddingModel:
    """Wrapper around sentence-transformers for semantic similarity."""

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(self, model=None):
        self._model = model

    def _init_model(self):
        """Lazily load the sentence-transformers model with HF token for faster downloads."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            token = _load_hf_token()
            self._model = SentenceTransformer(self.MODEL_NAME, token=token)

    def encode(self, texts: List[str]):
        """Encode a list of texts into embeddings."""
        self._init_model()
        return self._model.encode(texts, normalize_embeddings=True)

    def similarity(self, query_embedding, corpus_embeddings) -> List[float]:
        """Compute cosine similarities between a query and corpus embeddings."""
        # With normalized embeddings, dot product = cosine similarity
        scores = corpus_embeddings @ query_embedding
        return scores.tolist()


def _generate_reason(song: dict, profile: dict) -> str:
    """Generate a human-readable reason why a song matches the profile."""
    reasons = []
    song_genre = (song.get("genre") or "").lower()
    song_mood = (song.get("mood") or "").lower()

    for g in profile.get("genres", []):
        if g.lower() in song_genre or song_genre in g.lower():
            reasons.append(f"matches your taste for {g}")
            break

    for m in profile.get("moods", []):
        if m.lower() in song_mood or song_mood in m.lower():
            reasons.append(f"{song_mood} mood aligns with your preference")
            break

    if song.get("artist") in profile.get("artists", []):
        reasons.append(f"by one of your favorite artists")

    if not reasons:
        reasons.append("semantically similar to your favorites")

    return "; ".join(reasons)


class RAGRecommender:
    """Main RAG agent: Retrieve -> Embed -> Rank by similarity."""

    def __init__(self, songs_csv_path: str = "data/songs.csv",
                 playlist_path: str = "data/playlist.json",
                 audiodb: Optional[AudioDBClient] = None,
                 embedding_model: Optional[EmbeddingModel] = None):
        self.songs_csv_path = songs_csv_path
        self.playlist_path = playlist_path
        self.favorites = _load_json(playlist_path)
        self.favorite_ids = {s["id"] for s in self.favorites if "id" in s}
        self.profile = ProfileAnalyzer.from_playlist(playlist_path, songs_csv_path)
        self.retriever = SongRetriever(audiodb=audiodb, songs_csv_path=songs_csv_path)
        self.embedding_model = embedding_model or EmbeddingModel()

    def recommend(self, user_query: str = "", k: int = 5) -> dict:
        """Run the full RAG pipeline and return recommendations."""
        print("\n[RAG Agent] Analyzing your taste profile...")
        print(f"  {self.profile['summary']}")

        # RETRIEVE
        print("\n[RAG Agent] Retrieving candidate songs...")
        candidates = self.retriever.retrieve(self.profile, self.favorite_ids)

        if not candidates:
            return {
                "recommendations": [],
                "overall_explanation": "No candidate songs found.",
            }

        # EMBED & RANK
        print("\n[RAG Agent] Computing semantic similarity with all-MiniLM-L6-v2...")

        # Build text representations
        profile_text = _profile_to_text(self.profile, user_query)
        favorite_texts = [_song_to_text(s) for s in self.favorites]
        candidate_texts = [_song_to_text(c) for c in candidates]

        # Combine profile + favorites into a single query embedding
        query_text = profile_text + ". Favorites: " + "; ".join(favorite_texts)

        # Encode everything
        all_texts = [query_text] + candidate_texts
        embeddings = self.embedding_model.encode(all_texts)
        query_embedding = embeddings[0]
        candidate_embeddings = embeddings[1:]

        # Compute similarities
        scores = self.embedding_model.similarity(query_embedding, candidate_embeddings)

        # Rank and pick top-k
        scored = list(zip(candidates, scores))
        scored.sort(key=lambda x: x[1], reverse=True)
        top_k = scored[:k]

        print(f"[RAG Agent] Top {k} recommendations by semantic similarity:\n")

        recommendations = []
        for song, score in top_k:
            reason = _generate_reason(song, self.profile)
            recommendations.append({
                "title": song.get("title", "Unknown"),
                "artist": song.get("artist", "Unknown"),
                "genre": song.get("genre", ""),
                "mood": song.get("mood", ""),
                "similarity": round(score, 4),
                "reason": reason,
                "source": song.get("source", "unknown"),
            })

        return {
            "recommendations": recommendations,
            "overall_explanation": (
                f"Ranked {len(candidates)} candidates by semantic similarity to your "
                f"taste profile ({', '.join(self.profile['genres'])}, "
                f"{', '.join(self.profile['moods'])}) using all-MiniLM-L6-v2 embeddings."
            ),
        }


    def discover(self, playlist: List[dict], k: int = 10) -> dict:
        """Discover new songs NOT in the local 20-song catalog.

        Accepts the user's current playlist directly (from the frontend) rather
        than reading from disk.  Uses the full RAG pipeline: profile analysis,
        broad retrieval (favorite + genre-related artists via AudioDB), semantic
        embedding, and similarity ranking.
        """
        if not playlist:
            return {"recommendations": [], "overall_explanation": "Playlist is empty."}

        # Build profile from the supplied playlist
        artists = list({s["artist"] for s in playlist if "artist" in s})
        genres = [s["genre"] for s in playlist if "genre" in s]
        moods = [s["mood"] for s in playlist if "mood" in s]
        genre_counts = Counter(genres)
        mood_counts = Counter(moods)

        profile = {
            "artists": artists,
            "genres": [g for g, _ in genre_counts.most_common(3)],
            "moods": [m for m, _ in mood_counts.most_common(3)],
            "avg_energy": _avg([s.get("energy", 0.5) for s in playlist]),
            "likes_acoustic": _avg([s.get("acousticness", 0.5) for s in playlist]) > 0.5,
        }

        print("\n[RAG Agent – Discover] Profile:", profile)

        # Retrieve candidates — skip local catalog songs entirely
        favorite_ids = {s["id"] for s in playlist if "id" in s}
        candidates = self.retriever.retrieve(profile, favorite_ids, include_local=False)

        # Also exclude anything that's in the local 20-song catalog by (title, artist)
        local_songs = load_songs(self.songs_csv_path)
        local_keys = {(s["title"].lower(), s["artist"].lower()) for s in local_songs}
        candidates = [
            c for c in candidates
            if (c["title"].lower(), c["artist"].lower()) not in local_keys
        ]

        if not candidates:
            return {
                "recommendations": [],
                "overall_explanation": "No external songs found. Try adding more songs to your playlist.",
            }

        # Embed & rank
        print(f"\n[RAG Agent – Discover] Ranking {len(candidates)} candidates...")
        profile_text = _profile_to_text(profile)
        favorite_texts = [_song_to_text(s) for s in playlist]
        candidate_texts = [_song_to_text(c) for c in candidates]

        query_text = profile_text + ". Favorites: " + "; ".join(favorite_texts)
        all_texts = [query_text] + candidate_texts
        embeddings = self.embedding_model.encode(all_texts)
        query_embedding = embeddings[0]
        candidate_embeddings = embeddings[1:]
        scores = self.embedding_model.similarity(query_embedding, candidate_embeddings)

        scored = list(zip(candidates, scores))
        scored.sort(key=lambda x: x[1], reverse=True)

        # Artist diversity — max 3 songs per artist
        artist_count: Dict[str, int] = {}
        top_k = []
        for song, score in scored:
            if len(top_k) >= k:
                break
            a = song.get("artist", "")
            if artist_count.get(a, 0) < 3:
                artist_count[a] = artist_count.get(a, 0) + 1
                top_k.append((song, score))

        recommendations = []
        for song, score in top_k:
            reason = _generate_reason(song, profile)
            rec = {
                "title": song.get("title", "Unknown"),
                "artist": song.get("artist", "Unknown"),
                "genre": song.get("genre", ""),
                "mood": song.get("mood", ""),
                "style": song.get("style", ""),
                "theme": song.get("theme", ""),
                "similarity": round(float(score), 4),
                "reason": reason,
                "source": song.get("source", "audiodb"),
            }
            recommendations.append(rec)

        return {
            "recommendations": recommendations,
            "overall_explanation": (
                f"Discovered {len(recommendations)} songs from {len(artist_count)} artists. "
                f"Ranked {len(candidates)} AudioDB candidates by semantic similarity to your "
                f"taste profile ({', '.join(profile['genres'])}, {', '.join(profile['moods'])}) "
                f"using all-MiniLM-L6-v2 embeddings."
            ),
        }


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_hf_token() -> str | None:
    """Load HF_TOKEN from .env file or environment for authenticated Hugging Face access."""
    token = os.environ.get("HF_TOKEN")
    if token:
        return token

    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("HF_TOKEN=") and not line.startswith("#"):
                    return line.split("=", 1)[1].strip()
    except FileNotFoundError:
        pass
    return None


def _load_json(path: str) -> list:
    """Load a JSON file, resolving relative paths from the project root."""
    if not os.path.isabs(path):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"Warning: Could not load {path}: {exc}")
        return []


def _avg(values: list) -> float:
    """Compute average of a list, returning 0.0 for empty lists."""
    return sum(values) / len(values) if values else 0.0
