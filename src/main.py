"""Command line runner for the music recommender and local agentic workflow."""

import textwrap
import argparse
import json
from pathlib import Path
from typing import Any, Dict

try:
    from .recommender import load_songs, recommend_songs
    from .demo_profiles import (
        your_taste_profile,
        pop_fan,
        lofi_chill,
        indie_melancholic,
        conflicting_mood_energy,
    )
    from .agentic_workflow import (
        AgenticWorkflowController,
        FailureKind,
        WorkflowContract,
        WorkflowInput,
        format_workflow_result,
    )
except ImportError:
    # Supports running from src/ as a script while keeping module mode functional.
    from recommender import load_songs, recommend_songs
    from demo_profiles import (
        your_taste_profile,
        pop_fan,
        lofi_chill,
        indie_melancholic,
        conflicting_mood_energy,
    )
    from agentic_workflow import (  # type: ignore
        AgenticWorkflowController,
        FailureKind,
        WorkflowContract,
        WorkflowInput,
        format_workflow_result,
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


def run_demo() -> None:
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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Music recommender and agentic workflow runner")
    parser.add_argument(
        "--mode",
        choices=["demo", "agentic"],
        default="demo",
        help="Run recommender demo or the Plan->Execute->Observe->Re-plan workflow",
    )
    parser.add_argument(
        "--goal",
        default="Implement a small, testable repository change",
        help="Objective for agentic workflow mode",
    )
    parser.add_argument(
        "--scope",
        nargs="*",
        default=["src", "tests"],
        help="Workflow target scope paths (space separated)",
    )
    parser.add_argument(
        "--retry-budget",
        type=int,
        default=1,
        help="Maximum Observe->Re-plan retries (default: 1)",
    )
    parser.add_argument(
        "--simulate-observation",
        choices=["pass", "actionable", "ambiguous"],
        default=None,
        help="Deterministic simulation mode for workflow testing",
    )
    parser.add_argument(
        "--workflow-file",
        default=None,
        help="Path to JSON workflow config (compose-style) for agentic mode",
    )
    return parser.parse_args()


def _load_workflow_file(file_path: str) -> Dict[str, Any]:
    config_path = Path(file_path)
    if not config_path.exists():
        raise ValueError(f"Workflow file not found: {file_path}")
    try:
        raw = config_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in workflow file {file_path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Workflow file must contain a top-level JSON object")
    return data


def _resolve_agentic_settings(args: argparse.Namespace) -> Dict[str, Any]:
    settings: Dict[str, Any] = {
        "goal": args.goal,
        "scope": args.scope,
        "retry_budget": args.retry_budget,
        "simulate_observation": args.simulate_observation,
        "success_criteria": "Validation passes for planned targets",
        "done_definition": "Plan, execute log, observation outcome, and re-plan decision printed",
    }

    if args.workflow_file:
        file_settings = _load_workflow_file(args.workflow_file)
        settings.update(file_settings)

    if not isinstance(settings.get("scope"), list):
        raise ValueError("Workflow setting 'scope' must be a list of paths")

    simulate_value = settings.get("simulate_observation")
    valid_simulations = {None, "pass", "actionable", "ambiguous"}
    if simulate_value not in valid_simulations:
        raise ValueError(
            "Workflow setting 'simulate_observation' must be one of: pass, actionable, ambiguous"
        )

    try:
        settings["retry_budget"] = max(0, int(settings.get("retry_budget", 1)))
    except (TypeError, ValueError) as exc:
        raise ValueError("Workflow setting 'retry_budget' must be an integer") from exc

    return settings


def _run_agentic_mode(args: argparse.Namespace) -> None:
    simulation_map = {
        "pass": FailureKind.NONE,
        "actionable": FailureKind.ACTIONABLE,
        "ambiguous": FailureKind.AMBIGUOUS,
        None: None,
    }
    settings = _resolve_agentic_settings(args)
    controller = AgenticWorkflowController()
    workflow_input = WorkflowInput(
        objective=str(settings["goal"]),
        scope=[str(item) for item in settings["scope"]],
        contract=WorkflowContract(
            success_criteria=str(settings["success_criteria"]),
            done_definition=str(settings["done_definition"]),
            retry_budget=settings["retry_budget"],
        ),
    )
    result = controller.run(
        workflow_input=workflow_input,
        simulate_observation=simulation_map[settings["simulate_observation"]],
    )
    print(format_workflow_result(result))


def main() -> None:
    args = _parse_args()
    if args.mode == "agentic":
        _run_agentic_mode(args)
        return
    run_demo()


if __name__ == "__main__":
    main()
