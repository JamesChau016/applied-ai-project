from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import csv
import os

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
    
def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, str]:
    """Score a song against user preferences and return (score, explanation) tuple."""
    score = 0
    reasons = []
    
    # 1. MOOD MATCH (0-4 points) - Highest weight
    if song['mood'].lower() == user_prefs['favorite_mood'].lower():
        score += 4.0
        reasons.append(f"Mood match: {song['mood']} ({4.0} pts)")
    elif _is_mood_similar(song['mood'], user_prefs['favorite_mood']):
        score += 2.0
        reasons.append(f"Similar mood: {song['mood']} vs {user_prefs['favorite_mood']} ({2.0} pts)")
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
    
    # 3. GENRE MATCH (0-1.5 points)
    if song['genre'].lower() == user_prefs['favorite_genre'].lower():
        score += 1.5
        reasons.append(f"Genre match: {song['genre']} ({1.5} pts)")
    elif _is_genre_related(song['genre'], user_prefs['favorite_genre']):
        score += 0.75
        reasons.append(f"Related genre: {song['genre']} ({0.75} pts)")
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


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score all songs and return top k recommendations sorted by score (highest first)."""
    # Score all songs using list comprehension
    scored_songs = [
        (song, *score_song(user_prefs, song))
        for song in songs
    ]
    
    # Sort by score (descending) and return top k
    return sorted(scored_songs, key=lambda x: x[1], reverse=True)[:k]


