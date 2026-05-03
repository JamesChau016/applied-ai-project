from src.recommender import recommend_songs, score_song


def make_small_catalog():
    return [
        {
            "id": 1,
            "title": "Test Pop Track",
            "artist": "Test Artist",
            "genre": "pop",
            "mood": "happy",
            "energy": 0.8,
            "tempo_bpm": 120,
            "valence": 0.9,
            "danceability": 0.8,
            "acousticness": 0.2,
            "popularity": 85,
            "release_year": 2018,
            "instrumentalness": 0.2,
            "lyrical_sentiment": 0.6,
            "production_complexity": 0.7,
        },
        {
            "id": 2,
            "title": "Chill Lofi Loop",
            "artist": "Test Artist",
            "genre": "lofi",
            "mood": "chill",
            "energy": 0.4,
            "tempo_bpm": 80,
            "valence": 0.6,
            "danceability": 0.5,
            "acousticness": 0.9,
            "popularity": 55,
            "release_year": 2014,
            "instrumentalness": 0.8,
            "lyrical_sentiment": 0.1,
            "production_complexity": 0.4,
        },
    ]


def test_recommend_returns_songs_sorted_by_score():
    user = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "likes_acoustic": False,
    }
    songs = make_small_catalog()
    results = recommend_songs(user, songs, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0][0]["genre"] == "pop"
    assert results[0][0]["mood"] == "happy"


def test_score_song_returns_non_empty_explanation():
    user = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "likes_acoustic": False,
    }
    song = make_small_catalog()[0]

    _, explanation = score_song(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""
