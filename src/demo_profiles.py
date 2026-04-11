"""
Demo user profiles for testing and demonstration purposes.
"""

from recommender import UserProfile

# Your taste profile - Radiohead & The Weeknd enthusiast
# Prefers chill, moody songs like "No Surprise", "Let Down", "Save Your Tears"
your_taste_profile = UserProfile(
    favorite_genre="alternative rock",
    favorite_mood="moody",
    target_energy=0.45,
    likes_acoustic=True
)

# Additional example profiles for testing
pop_fan = UserProfile(
    favorite_genre="pop",
    favorite_mood="happy",
    target_energy=0.8,
    likes_acoustic=False
)

lofi_chill = UserProfile(
    favorite_genre="lofi",
    favorite_mood="chill",
    target_energy=0.4,
    likes_acoustic=True
)

indie_melancholic = UserProfile(
    favorite_genre="indie rock",
    favorite_mood="melancholic",
    target_energy=0.65,
    likes_acoustic=True
)

# CONFLICT PROFILE - Tests contradictory preferences
# User wants sad mood but extremely high energy (opposing signals)
conflicting_mood_energy = UserProfile(
    favorite_genre="pop",
    favorite_mood="sad",
    target_energy=0.95,
    likes_acoustic=False
)
