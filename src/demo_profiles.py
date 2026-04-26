"""
Demo user profiles for testing and demonstration purposes.
"""

from .recommender import UserProfile

# Your taste profile - Radiohead & The Weeknd enthusiast
# Prefers chill, moody songs like "No Surprise", "Let Down", "Save Your Tears"
your_taste_profile = UserProfile(
    favorite_genre="alternative rock",
    favorite_mood="moody",
    target_energy=0.45,
    likes_acoustic=True,
    target_popularity=72,
    target_decade=2010,
    target_instrumentalness=0.30,
    target_lyrical_sentiment=-0.40,
    target_production_complexity=0.75,
)

# Additional example profiles for testing
pop_fan = UserProfile(
    favorite_genre="pop",
    favorite_mood="happy",
    target_energy=0.8,
    likes_acoustic=False,
    target_popularity=90,
    target_decade=2010,
    target_instrumentalness=0.08,
    target_lyrical_sentiment=0.70,
    target_production_complexity=0.82,
)

lofi_chill = UserProfile(
    favorite_genre="lofi",
    favorite_mood="chill",
    target_energy=0.4,
    likes_acoustic=True,
    target_popularity=62,
    target_decade=2010,
    target_instrumentalness=0.75,
    target_lyrical_sentiment=0.12,
    target_production_complexity=0.42,
)

indie_melancholic = UserProfile(
    favorite_genre="indie rock",
    favorite_mood="melancholic",
    target_energy=0.65,
    likes_acoustic=True,
    target_popularity=82,
    target_decade=2000,
    target_instrumentalness=0.15,
    target_lyrical_sentiment=-0.48,
    target_production_complexity=0.72,
)

# CONFLICT PROFILE - Tests contradictory preferences
# User wants sad mood but extremely high energy (opposing signals)
conflicting_mood_energy = UserProfile(
    favorite_genre="pop",
    favorite_mood="sad",
    target_energy=0.95,
    likes_acoustic=False,
    target_popularity=88,
    target_decade=2010,
    target_instrumentalness=0.05,
    target_lyrical_sentiment=-0.60,
    target_production_complexity=0.85,
)
