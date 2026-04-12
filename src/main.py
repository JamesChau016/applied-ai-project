"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs
import textwrap
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


def _print_recommendations_table(recommendations) -> None:
    """Print recommendations in a readable ASCII table including scoring reasons."""
    headers = ["#", "Song", "Artist", "Score", "Reasons"]
    rows = []

    for i, rec in enumerate(recommendations, 1):
        song, score, reasons = rec
        # Put each scoring category on its own line for readability.
        reason_items = [item.strip() for item in reasons.split("|") if item.strip()]
        display_reasons = "\n".join(reason_items)
        rows.append([
            str(i),
            song["title"],
            song["artist"],
            f"{score:.2f}",
            display_reasons,
        ])

    # Column caps keep output readable while wrapping long text inside each column.
    max_widths = [3, 20, 20, 7, 72]
    col_widths = []
    for col_idx, header in enumerate(headers):
        max_cell = max(len(str(row[col_idx])) for row in rows)
        col_widths.append(min(max(max_cell, len(header)), max_widths[col_idx]))

    def sep(char: str = "-") -> str:
        return "+" + "+".join(char * (w + 2) for w in col_widths) + "+"

    def format_row(cells) -> str:
        lines_per_cell = []
        for col_idx, cell in enumerate(cells):
            wrapped_lines = []
            for raw_line in str(cell).splitlines() or [""]:
                wrapped = textwrap.wrap(
                    raw_line,
                    width=col_widths[col_idx],
                    break_long_words=False,
                    break_on_hyphens=False,
                )
                wrapped_lines.extend(wrapped or [""])
            lines_per_cell.append(wrapped_lines or [""])
        max_lines = max(len(lines) for lines in lines_per_cell)
        normalized = []
        for lines in lines_per_cell:
            padded = lines + [""] * (max_lines - len(lines))
            normalized.append(padded)

        out_lines = []
        for line_idx in range(max_lines):
            out = "|"
            for col_idx, lines in enumerate(normalized):
                out += f" {lines[line_idx].ljust(col_widths[col_idx])} |"
            out_lines.append(out)
        return "\n".join(out_lines)

    print(sep("-"))
    print(format_row(headers))
    print(sep("="))
    for row in rows:
        print(format_row(row))
        print(sep("-"))


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

        _print_recommendations_table(recommendations)
        print()


if __name__ == "__main__":
    main()
