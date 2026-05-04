"""RAG (Retrieval-Augmented Generation) agent for music recommendations.

Uses TheAudioDB for song retrieval and sentence-transformers (all-MiniLM-L6-v2)
for semantic similarity-based ranking.
"""

import json
import os
from collections import Counter
from typing import Dict, List, Optional

try:
    from .audiodb_client import AudioDBClient, get_genre_artists, resolve_artist_name
    from .recommender import load_songs
except ImportError:
    from audiodb_client import AudioDBClient, get_genre_artists, resolve_artist_name
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
                  include_local: bool = True,
                  pref_artists: list | None = None,
                  max_artists: int = 10) -> List[dict]:
        """Fetch candidate songs based on user profile.

        When pref_artists is given, only those artists are fetched.
        Otherwise, fetches playlist artists + genre-related artists up
        to max_artists total.
        """
        candidates = []
        seen_keys = set()
        tried_artists = set()
        fetch_count = 0

        def _fetch_artist(artist: str, allow_correction: bool = True) -> int:
            nonlocal fetch_count
            if artist in tried_artists or fetch_count >= max_artists:
                return 0
            tried_artists.add(artist)
            fetch_count += 1
            print(f"  Fetching tracks for '{artist}' from TheAudioDB...")
            tracks = self.audiodb.get_top_tracks(artist)

            # If no results and name might be misspelled, try fuzzy correction
            if not tracks and allow_correction:
                corrected = resolve_artist_name(artist)
                if corrected != artist and corrected not in tried_artists:
                    tried_artists.add(corrected)
                    tracks = self.audiodb.get_top_tracks(corrected)

            added = 0
            for track in tracks:
                key = (track["title"].lower(), track["artist"].lower())
                if key not in seen_keys:
                    seen_keys.add(key)
                    candidates.append(track)
                    added += 1
            return added

        if pref_artists:
            # Only fetch the user's explicitly preferred artists
            for artist in pref_artists:
                _fetch_artist(artist)
        else:
            # 1. Fetch top tracks for each playlist artist
            for artist in profile.get("artists", []):
                if fetch_count >= max_artists:
                    break
                _fetch_artist(artist)

            # 2. Broaden with genre-related artists up to the cap
            for genre in profile.get("genres", []):
                if fetch_count >= max_artists:
                    break
                related = get_genre_artists(genre, exclude=tried_artists)
                for artist in related:
                    if fetch_count >= max_artists:
                        break
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
    if profile.get("energy_min") is not None and profile.get("energy_max") is not None:
        parts.append(
            f"energy range {profile['energy_min']:.2f}-{profile['energy_max']:.2f}"
        )
    else:
        energy = profile.get("avg_energy", 0.5)
        energy_label = (
            "low energy" if energy < 0.4 else "medium energy" if energy < 0.7 else "high energy"
        )
        parts.append(energy_label)
    if profile.get("popularity_min") is not None and profile.get("popularity_max") is not None:
        parts.append(
            f"popularity range {profile['popularity_min']:.0f}-{profile['popularity_max']:.0f}"
        )
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


    def discover(self, playlist: List[dict], k: int = 10, preferences: Optional[dict] = None) -> dict:
        """Discover new songs NOT in the local 20-song catalog.

        Accepts the user's current playlist directly (from the frontend) rather
        than reading from disk.  Uses the full RAG pipeline: profile analysis,
        broad retrieval (favorite + genre-related artists via AudioDB), semantic
        embedding, and similarity ranking.
        """
        if not playlist:
            return {"recommendations": [], "overall_explanation": "Playlist is empty."}

        preferences = preferences or {}

        # Build profile from the supplied playlist
        artists = list({s["artist"] for s in playlist if "artist" in s})
        genres = [s["genre"] for s in playlist if "genre" in s]
        moods = [s["mood"] for s in playlist if "mood" in s]
        genre_counts = Counter(genres)
        mood_counts = Counter(moods)
        playlist_top_genres = [g for g, _ in genre_counts.most_common(3)]
        playlist_top_moods = [m for m, _ in mood_counts.most_common(3)]

        pref_artists = [resolve_artist_name(a) for a in _normalize_list(preferences.get("artists"))]
        pref_genres = _normalize_list(preferences.get("genres"))
        pref_moods = _normalize_list(preferences.get("moods"))

        if pref_artists:
            artists = _merge_unique(pref_artists, artists)
        if pref_genres:
            genres = _merge_unique(pref_genres, genres)
        if pref_moods:
            moods = _merge_unique(pref_moods, moods)

        profile_genres = _merge_unique(pref_genres, playlist_top_genres, limit=6)
        profile_moods = _merge_unique(pref_moods, playlist_top_moods, limit=6)

        profile = {
            "artists": artists,
            "genres": profile_genres,
            "moods": profile_moods,
            "avg_energy": _avg([s.get("energy", 0.5) for s in playlist]),
            "likes_acoustic": _avg([s.get("acousticness", 0.5) for s in playlist]) > 0.5,
        }

        energy_min = _coerce_float(preferences.get("energy_min"))
        energy_max = _coerce_float(preferences.get("energy_max"))
        if energy_min is not None or energy_max is not None:
            energy_min = 0.0 if energy_min is None else max(0.0, min(1.0, energy_min))
            energy_max = 1.0 if energy_max is None else max(0.0, min(1.0, energy_max))
            if energy_min > energy_max:
                energy_min, energy_max = energy_max, energy_min
            profile["energy_min"] = energy_min
            profile["energy_max"] = energy_max
            profile["avg_energy"] = (energy_min + energy_max) / 2

        popularity_min = _coerce_float(preferences.get("popularity_min"))
        popularity_max = _coerce_float(preferences.get("popularity_max"))
        if popularity_min is not None or popularity_max is not None:
            popularity_min = 0.0 if popularity_min is None else max(0.0, min(100.0, popularity_min))
            popularity_max = 100.0 if popularity_max is None else max(0.0, min(100.0, popularity_max))
            if popularity_min > popularity_max:
                popularity_min, popularity_max = popularity_max, popularity_min
            profile["popularity_min"] = popularity_min
            profile["popularity_max"] = popularity_max

        print("\n[RAG Agent – Discover] Profile:", profile)

        # Retrieve candidates — skip local catalog songs entirely
        favorite_ids = {s["id"] for s in playlist if "id" in s}
        candidates = self.retriever.retrieve(
            profile, favorite_ids, include_local=False,
            pref_artists=pref_artists or None,
        )

        # Also exclude anything that's in the local 20-song catalog by (title, artist)
        local_songs = load_songs(self.songs_csv_path)
        local_keys = {(s["title"].lower(), s["artist"].lower()) for s in local_songs}
        candidates = [
            c for c in candidates
            if (c["title"].lower(), c["artist"].lower()) not in local_keys
        ]

        preferences_relaxed = False
        if pref_genres or pref_moods or pref_artists:
            filtered_candidates = [
                c
                for c in candidates
                if _candidate_matches_preferences(
                    c,
                    pref_genres,
                    pref_moods,
                    pref_artists,
                    energy_min,
                    energy_max,
                    popularity_min,
                    popularity_max,
                )
            ]
            if filtered_candidates and len(filtered_candidates) >= k:
                candidates = filtered_candidates
            elif filtered_candidates:
                preferences_relaxed = True
            else:
                preferences_relaxed = True

        if not candidates:
            return {
                "recommendations": [],
                "overall_explanation": "No external songs found. Try adding more songs to your playlist.",
            }

        _hydrate_candidate_popularity(candidates)

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

        pref_genre_set = {g.lower() for g in pref_genres}
        pref_mood_set = {m.lower() for m in pref_moods}
        pref_artist_set = {a.lower() for a in pref_artists}

        def _preference_boost(song: dict) -> float:
            boost = 0.0
            song_genre = (song.get("genre") or "").lower()
            song_mood = (song.get("mood") or "").lower()
            song_artist = (song.get("artist") or "").lower()

            if pref_genre_set and _matches_any(song_genre, pref_genre_set):
                boost += 0.12
            if pref_mood_set and _matches_any(song_mood, pref_mood_set):
                boost += 0.08
            if pref_artist_set and song_artist in pref_artist_set:
                boost += 0.25
            return boost

        scored = [
            (song, score + _preference_boost(song)) for song, score in zip(candidates, scores)
        ]
        scored.sort(key=lambda x: x[1], reverse=True)

        # Build top-k with artist diversity (max 3 songs per artist)
        artist_count: Dict[str, int] = {}
        top_k = []
        seen_keys = set()

        def _add(song, score) -> bool:
            key = (song.get("title", "").lower(), song.get("artist", "").lower())
            if key in seen_keys:
                return False
            a = song.get("artist", "")
            if artist_count.get(a, 0) >= 3:
                return False
            seen_keys.add(key)
            artist_count[a] = artist_count.get(a, 0) + 1
            top_k.append((song, score))
            return True

        # Seed with top match for each preferred artist
        if pref_artists:
            for artist in pref_artists:
                artist_lower = artist.lower()
                for song, score in scored:
                    if song.get("artist", "").lower() == artist_lower:
                        _add(song, score)
                        break

        # Fill remaining slots from ranked list
        for song, score in scored:
            if len(top_k) >= k:
                break
            _add(song, score)

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

        preference_note = ""
        if pref_genres or pref_moods or pref_artists:
            if preferences_relaxed:
                preference_note = (
                    " Preferences were relaxed because no candidates matched; "
                    "ranking still favors your selections."
                )
            else:
                preference_note = " Preferences were applied during retrieval and ranking."

        return {
            "recommendations": recommendations,
            "overall_explanation": (
                f"Discovered {len(recommendations)} songs from {len(artist_count)} artists. "
                f"Ranked {len(candidates)} AudioDB candidates by semantic similarity to your "
                f"taste profile ({', '.join(profile['genres'])}, {', '.join(profile['moods'])}) "
                f"using all-MiniLM-L6-v2 embeddings.{preference_note}"
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


def _normalize_list(value) -> list:
    """Normalize string/list values into a clean list of strings."""
    if not value:
        return []
    if isinstance(value, str):
        parts = value.split(",")
    elif isinstance(value, list):
        parts = value
    else:
        return []
    return [str(item).strip() for item in parts if str(item).strip()]


def _coerce_float(value) -> float | None:
    """Best-effort float coercion."""
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _merge_unique(primary: list, secondary: list, limit: int | None = None) -> list:
    """Merge lists, keeping order and uniqueness, optionally limiting size."""
    merged = []
    for item in primary + secondary:
        if item not in merged:
            merged.append(item)
        if limit is not None and len(merged) >= limit:
            break
    return merged


def _matches_any(text: str, options: set) -> bool:
    """Return True if text matches any option (exact or substring)."""
    if not text:
        return False
    return any(option in text or text in option for option in options)


def _hydrate_candidate_popularity(candidates: list) -> None:
    """Attach a 0-100 popularity estimate for AudioDB tracks when missing."""
    scores = [c.get("score") for c in candidates if isinstance(c.get("score"), (int, float))]
    plays = [c.get("total_plays") for c in candidates if isinstance(c.get("total_plays"), int)]
    listeners = [
        c.get("total_listeners") for c in candidates if isinstance(c.get("total_listeners"), int)
    ]
    loved = [c.get("loved") for c in candidates if isinstance(c.get("loved"), int)]

    score_max = max(scores) if scores else 0
    play_max = max(plays) if plays else 0
    listener_max = max(listeners) if listeners else 0
    loved_max = max(loved) if loved else 0

    for candidate in candidates:
        if candidate.get("popularity") is not None:
            continue
        score = candidate.get("score") or 0
        total_plays = candidate.get("total_plays") or 0
        total_listeners = candidate.get("total_listeners") or 0
        total_loved = candidate.get("loved") or 0

        components = []
        if score_max:
            components.append(score / score_max)
        if play_max:
            components.append(total_plays / play_max)
        if listener_max:
            components.append(total_listeners / listener_max)
        if loved_max:
            components.append(total_loved / loved_max)

        if components:
            candidate["popularity"] = _clamp(round(max(components) * 100, 1), 0, 100)


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _candidate_matches_preferences(
    song: dict,
    pref_genres: list,
    pref_moods: list,
    pref_artists: list,
    energy_min: float | None,
    energy_max: float | None,
    popularity_min: float | None,
    popularity_max: float | None,
) -> bool:
    """Return True if a candidate aligns with preferences when metadata is present.

    Genre, mood, and artist use OR logic — matching ANY one dimension is enough.
    Energy and popularity use AND logic as hard numeric range filters.
    """
    # Energy and popularity are hard range filters (AND)
    if energy_min is not None or energy_max is not None:
        energy = song.get("energy")
        if isinstance(energy, (int, float)):
            if energy_min is not None and energy < energy_min:
                return False
            if energy_max is not None and energy > energy_max:
                return False
    if popularity_min is not None or popularity_max is not None:
        popularity = song.get("popularity")
        if isinstance(popularity, (int, float)):
            if popularity_min is not None and popularity < popularity_min:
                return False
            if popularity_max is not None and popularity > popularity_max:
                return False

    # Genre, mood, artist use OR logic — match ANY dimension to pass
    has_taste_prefs = bool(pref_genres or pref_moods or pref_artists)
    if not has_taste_prefs:
        return True

    if pref_genres:
        song_genre = (song.get("genre") or "").lower()
        if song_genre and _matches_any(song_genre, {g.lower() for g in pref_genres}):
            return True
    if pref_moods:
        song_mood = (song.get("mood") or "").lower()
        if song_mood and _matches_any(song_mood, {m.lower() for m in pref_moods}):
            return True
    if pref_artists:
        song_artist = (song.get("artist") or "").lower()
        if song_artist and song_artist in {a.lower() for a in pref_artists}:
            return True

    # Song has metadata but didn't match any preference dimension
    song_has_metadata = bool(
        (song.get("genre") or "").strip()
        or (song.get("mood") or "").strip()
        or (song.get("artist") or "").strip()
    )
    if song_has_metadata:
        return False

    # No metadata to judge — let it through for embedding-based ranking
    return True
