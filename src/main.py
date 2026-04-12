"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs
from demo_profiles import (
    your_taste_profile,
    pop_fan,
    lofi_chill,
    indie_melancholic,
    conflicting_mood_energy,
)


# Easy switch between ranking modes:
# - "mood_priority": baseline strategy
# - "genre_priority": genre-focused strategy
RANKING_MODE = "genre_priority"


def main() -> None:
    songs = load_songs("data/songs.csv")

    profiles = [
        ("Your Taste Profile", your_taste_profile),
        ("Pop Fan", pop_fan),
        ("Lo-Fi Chill", lofi_chill),
        ("Indie Melancholic", indie_melancholic),
        ("Conflicting Mood-Energy", conflicting_mood_energy),
    ]

    for profile_name, profile in profiles:
        # Convert UserProfile to dict for recommend_songs, including advanced preferences.
        user_prefs = {
            "favorite_genre": profile.favorite_genre,
            "favorite_mood": profile.favorite_mood,
            "target_energy": profile.target_energy,
            "likes_acoustic": profile.likes_acoustic,
            "target_popularity": profile.target_popularity,
            "target_decade": profile.target_decade,
            "target_instrumentalness": profile.target_instrumentalness,
            "target_lyrical_sentiment": profile.target_lyrical_sentiment,
            "target_production_complexity": profile.target_production_complexity,
        }

        recommendations = recommend_songs(user_prefs, songs, k=5, scoring_mode=RANKING_MODE)

        print("\n" + "=" * 60)
        print(f" {profile_name.upper()}")
        print("=" * 60)
        print(f" Ranking Mode: {RANKING_MODE}")
        print(f" Genre: {profile.favorite_genre} | Mood: {profile.favorite_mood}")
        print(f" Target Energy: {profile.target_energy} | Likes Acoustic: {profile.likes_acoustic}")
        print(
            " Targets -> "
            f"Popularity: {profile.target_popularity}, "
            f"Decade: {profile.target_decade}s, "
            f"Instr: {profile.target_instrumentalness}, "
            f"Lyrical: {profile.target_lyrical_sentiment}, "
            f"Complexity: {profile.target_production_complexity}"
        )
        print("=" * 60 + "\n")

        for i, rec in enumerate(recommendations, 1):
            song, score, reasons = rec
            print(f"  {i}. {song['title']} - {song['artist']}")
            print(f"     Score: {score:.2f}")
            print(f"     Reasons: {reasons}")
            print()


if __name__ == "__main__":
    main()
