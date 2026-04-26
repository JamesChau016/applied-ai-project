from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import csv
import os


SCORING_MODES = {
    # Baseline: mood is dominant, genre is secondary.
    "mood_priority": {
        "mood_exact": 4.0,
        "mood_similar": 2.0,
        "genre_exact": 1.5,
        "genre_related": 0.75,
    },
    # Alternate strategy: genre is dominant, mood is secondary.
    "genre_priority": {
        "mood_exact": 2.0,
        "mood_similar": 1.0,
        "genre_exact": 4.0,
        "genre_related": 2.0,
    },
}

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    popularity: float = 50.0
    release_year: int = 2015
    instrumentalness: float = 0.3
    lyrical_sentiment: float = 0.0
    production_complexity: float = 0.5

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    target_popularity: Optional[float] = None
    target_decade: Optional[int] = None
    target_instrumentalness: Optional[float] = None
    target_lyrical_sentiment: Optional[float] = None
    target_production_complexity: Optional[float] = None

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """Load songs from a CSV file and return as a list of dictionaries."""
    print(f"Loading songs from {csv_path}...")
    
    # Get the absolute path, handling relative paths from src/ directory
    if not os.path.isabs(csv_path):
        # If relative path, compute relative to this file's location
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(current_dir, "..", csv_path)
    
    songs = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Convert numeric fields to appropriate types
                song = {
                    'id': int(row['id']),
                    'title': row['title'],
                    'artist': row['artist'],
                    'genre': row['genre'],
                    'mood': row['mood'],
                    'energy': float(row['energy']),
                    'tempo_bpm': float(row['tempo_bpm']),
                    'valence': float(row['valence']),
                    'danceability': float(row['danceability']),
                    'acousticness': float(row['acousticness']),
                    'popularity': float(row.get('popularity', 50)),
                    'release_year': int(row.get('release_year', 2015)),
                    'instrumentalness': float(row.get('instrumentalness', 0.3)),
                    'lyrical_sentiment': float(row.get('lyrical_sentiment', 0.0)),
                    'production_complexity': float(row.get('production_complexity', 0.5)),
                }
                songs.append(song)
        
    
    except FileNotFoundError:
        print(f"Error: File not found at {csv_path}")
        return []
    except Exception as e:
        print(f"Error loading songs: {e}")
        return []
    
    print(f"Successfully loaded {len(songs)} songs.")
    return songs
    
def score_song(user_prefs: Dict, song: Dict, scoring_mode: str = "mood_priority") -> Tuple[float, str]:
    """Score a song against user preferences and return (score, explanation) tuple."""
    score = 0
    reasons = []
    weights = SCORING_MODES.get(scoring_mode, SCORING_MODES["mood_priority"])
    
    # 1. MOOD MATCH (weighted by strategy mode)
    if song['mood'].lower() == user_prefs['favorite_mood'].lower():
        score += weights["mood_exact"]
        reasons.append(f"Mood match: {song['mood']} ({weights['mood_exact']} pts)")
    elif _is_mood_similar(song['mood'], user_prefs['favorite_mood']):
        score += weights["mood_similar"]
        reasons.append(f"Similar mood: {song['mood']} vs {user_prefs['favorite_mood']} ({weights['mood_similar']} pts)")
    else:
        reasons.append(f"Mood mismatch: {song['mood']} vs {user_prefs['favorite_mood']} ({0} pts)")
    
    # 2. ENERGY PROXIMITY (0-2.5 points)
    energy_diff = abs(song['energy'] - user_prefs['target_energy'])
    if energy_diff <= 0.1:
        score += 2.5
        reasons.append(f"Energy perfect match: {song['energy']:.2f} ({2.5} pts)")
    elif energy_diff <= 0.2:
        score += 1.5
        reasons.append(f"Energy close: {song['energy']:.2f} vs {user_prefs['target_energy']:.2f} ({1.5} pts)")
    elif energy_diff <= 0.3:
        score += 1.0
        reasons.append(f"Energy acceptable: {song['energy']:.2f} vs {user_prefs['target_energy']:.2f} ({1.0} pts)")
    else:
        reasons.append(f"Energy mismatch: {song['energy']:.2f} vs {user_prefs['target_energy']:.2f} ({0} pts)")
    
    # 3. GENRE MATCH (weighted by strategy mode)
    if song['genre'].lower() == user_prefs['favorite_genre'].lower():
        score += weights["genre_exact"]
        reasons.append(f"Genre match: {song['genre']} ({weights['genre_exact']} pts)")
    elif _is_genre_related(song['genre'], user_prefs['favorite_genre']):
        score += weights["genre_related"]
        reasons.append(f"Related genre: {song['genre']} ({weights['genre_related']} pts)")
    else:
        reasons.append(f"Genre different: {song['genre']} ({0} pts)")
    
    # 4. ACOUSTICNESS BONUS (0-1.2 points)
    if user_prefs['likes_acoustic']:
        if song['acousticness'] > 0.7:
            score += 1.2
            reasons.append(f"High acousticness: {song['acousticness']:.2f} ({1.2} pts)")
        elif song['acousticness'] > 0.4:
            score += 0.6
            reasons.append(f"Moderate acousticness: {song['acousticness']:.2f} ({0.6} pts)")
        else:
            reasons.append(f"Low acousticness: {song['acousticness']:.2f} ({0} pts)")
    else:
        reasons.append(f"Acousticness not prioritized ({0} pts)")
    
    # 5. VALENCE ALIGNMENT (0 to +0.5 or -0.25 points)
    if song['valence'] < 0.3:
        score += 0.5
        reasons.append(f"Low valence (moody): {song['valence']:.2f} ({0.5} pts)")
    elif song['valence'] > 0.6:
        score -= 0.25
        reasons.append(f"High valence (happy): {song['valence']:.2f} ({-0.25} pts)")
    else:
        reasons.append(f"Neutral valence: {song['valence']:.2f} ({0} pts)")
    
    # 6. DANCEABILITY (minimal 0.3 pts, usually 0 for moody)
    # Skipped for moody recommendations
    reasons.append(f"Danceability: ignored for moody aesthetic ({0} pts)")

    # 7. POPULARITY ALIGNMENT (0-1.5 points)
    default_popularity = 70.0 if user_prefs.get('favorite_mood', '').lower() in ['happy', 'upbeat', 'euphoric'] else 50.0
    target_popularity = float(user_prefs.get('target_popularity', default_popularity))
    popularity_diff = abs(song['popularity'] - target_popularity)
    if popularity_diff <= 10:
        score += 1.5
        reasons.append(f"Popularity aligned: {song['popularity']:.0f} vs {target_popularity:.0f} ({1.5} pts)")
    elif popularity_diff <= 20:
        score += 1.0
        reasons.append(f"Popularity close: {song['popularity']:.0f} vs {target_popularity:.0f} ({1.0} pts)")
    elif popularity_diff <= 30:
        score += 0.5
        reasons.append(f"Popularity acceptable: {song['popularity']:.0f} vs {target_popularity:.0f} ({0.5} pts)")
    else:
        reasons.append(f"Popularity mismatch: {song['popularity']:.0f} vs {target_popularity:.0f} ({0} pts)")

    # 8. RELEASE DECADE ALIGNMENT (0-1.0 points)
    target_decade = int(user_prefs.get('target_decade', 2010))
    song_decade = (int(song['release_year']) // 10) * 10
    decade_gap = abs(song_decade - target_decade)
    if decade_gap == 0:
        score += 1.0
        reasons.append(f"Same decade: {song_decade}s ({1.0} pts)")
    elif decade_gap == 10:
        score += 0.6
        reasons.append(f"Adjacent decade: {song_decade}s vs {target_decade}s ({0.6} pts)")
    elif decade_gap == 20:
        score += 0.2
        reasons.append(f"Older/newer decade: {song_decade}s vs {target_decade}s ({0.2} pts)")
    else:
        reasons.append(f"Decade far: {song_decade}s vs {target_decade}s ({0} pts)")

    # 9. INSTRUMENTALNESS ALIGNMENT (0-1.0 points, linear)
    default_instrumentalness = 0.65 if user_prefs.get('likes_acoustic') else 0.30
    target_instrumentalness = float(user_prefs.get('target_instrumentalness', default_instrumentalness))
    instrumentalness_diff = abs(song['instrumentalness'] - target_instrumentalness)
    instrumentalness_points = max(0.0, 1.0 - (2.0 * instrumentalness_diff))
    score += instrumentalness_points
    reasons.append(
        f"Instrumentalness alignment: song={song['instrumentalness']:.2f}, target={target_instrumentalness:.2f} ({instrumentalness_points:.2f} pts)"
    )

    # 10. LYRICAL SENTIMENT ALIGNMENT (0-1.0 points, linear)
    mood_target_sentiment = {
        'moody': -0.45,
        'melancholic': -0.50,
        'sad': -0.60,
        'dark': -0.55,
        'happy': 0.65,
        'upbeat': 0.60,
        'euphoric': 0.75,
        'chill': 0.15,
        'relaxed': 0.10,
        'focused': 0.05,
        'intense': -0.15,
        'aggressive': -0.35,
    }
    default_sentiment = mood_target_sentiment.get(user_prefs.get('favorite_mood', '').lower(), 0.0)
    target_lyrical_sentiment = float(user_prefs.get('target_lyrical_sentiment', default_sentiment))
    lyrical_sentiment_diff = abs(song['lyrical_sentiment'] - target_lyrical_sentiment)
    lyrical_sentiment_points = max(0.0, 1.0 - lyrical_sentiment_diff)
    score += lyrical_sentiment_points
    reasons.append(
        f"Lyrical sentiment alignment: song={song['lyrical_sentiment']:.2f}, target={target_lyrical_sentiment:.2f} ({lyrical_sentiment_points:.2f} pts)"
    )

    # 11. PRODUCTION COMPLEXITY ALIGNMENT (0-0.8 points, linear)
    default_complexity = 0.45 if user_prefs.get('likes_acoustic') else 0.70
    target_production_complexity = float(user_prefs.get('target_production_complexity', default_complexity))
    complexity_diff = abs(song['production_complexity'] - target_production_complexity)
    complexity_points = max(0.0, 0.8 - (1.6 * complexity_diff))
    score += complexity_points
    reasons.append(
        f"Production complexity alignment: song={song['production_complexity']:.2f}, target={target_production_complexity:.2f} ({complexity_points:.2f} pts)"
    )
    
    # Compile explanation
    explanation = " | ".join(reasons)
    
    return score, explanation


def _is_mood_similar(mood1: str, mood2: str) -> bool:
    """Return True if two moods are semantically similar."""
    mood_groups = {
        'moody': ['melancholic', 'sad', 'dark', 'introspective'],
        'melancholic': ['moody', 'sad', 'dark', 'introspective'],
        'chill': ['relaxed', 'focused', 'peaceful', 'calm'],
        'relaxed': ['chill', 'peaceful', 'calm'],
        'happy': ['euphoric', 'upbeat', 'energetic'],
        'energetic': ['happy', 'intense', 'euphoric'],
    }
    
    mood1_lower = mood1.lower()
    mood2_lower = mood2.lower()
    
    return mood1_lower in mood_groups.get(mood2_lower, []) or \
           mood2_lower in mood_groups.get(mood1_lower, [])


def _is_genre_related(genre1: str, genre2: str) -> bool:
    """Return True if two genres are related or adjacent categories."""
    genre_groups = {
        'alternative rock': ['indie rock', 'rock', 'indie pop'],
        'indie rock': ['alternative rock', 'rock', 'indie pop'],
        'synth-pop': ['pop', 'electronic', 'new wave'],
        'pop': ['synth-pop', 'indie pop', 'disco'],
        'lofi': ['ambient', 'chill', 'jazz'],
        'ambient': ['lofi', 'chill', 'classical'],
        'jazz': ['lofi', 'funk', 'soul'],
        'funk': ['disco', 'jazz', 'pop'],
    }
    
    genre1_lower = genre1.lower()
    genre2_lower = genre2.lower()
    
    return genre1_lower in genre_groups.get(genre2_lower, []) or \
           genre2_lower in genre_groups.get(genre1_lower, [])


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    scoring_mode: str = "mood_priority",
) -> List[Tuple[Dict, float, str]]:
    """Score all songs and return top k recommendations sorted by score (highest first)."""
    # Score all songs using list comprehension
    scored_songs = [
        (song, *score_song(user_prefs, song, scoring_mode=scoring_mode))
        for song in songs
    ]

    # Sort by score (descending).
    sorted_songs = sorted(scored_songs, key=lambda x: x[1], reverse=True)

    # Diversity penalty pattern: prioritize distinct artists in top-k.
    # First pass keeps at most one song per artist.
    diverse_results: List[Tuple[Dict, float, str]] = []
    seen_artists = set()
    for item in sorted_songs:
        artist = item[0]["artist"]
        if artist in seen_artists:
            continue
        diverse_results.append(item)
        seen_artists.add(artist)
        if len(diverse_results) == k:
            return diverse_results

    # If there are not enough unique artists in the catalog, backfill by score.
    for item in sorted_songs:
        if item in diverse_results:
            continue
        diverse_results.append(item)
        if len(diverse_results) == k:
            break

    return diverse_results


