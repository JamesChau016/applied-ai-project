import json
from argparse import Namespace

import pytest

from src.main import _resolve_agentic_settings


def _base_args(workflow_file=None):
    return Namespace(
        mode="agentic",
        goal="Default goal",
        scope=["src", "tests"],
        retry_budget=1,
        simulate_observation=None,
        workflow_file=workflow_file,
    )


def test_resolve_agentic_settings_from_workflow_file(tmp_path):
    workflow_path = tmp_path / "workflow.json"
    workflow_path.write_text(
        json.dumps(
            {
                "goal": "Implement feature X",
                "scope": ["src/recommender.py", "tests"],
                "retry_budget": 2,
                "simulate_observation": "pass",
                "success_criteria": "Feature tests pass",
                "done_definition": "Feature implemented and validated",
            }
        ),
        encoding="utf-8",
    )

    settings = _resolve_agentic_settings(_base_args(str(workflow_path)))

    assert settings["goal"] == "Implement feature X"
    assert settings["scope"] == ["src/recommender.py", "tests"]
    assert settings["retry_budget"] == 2
    assert settings["simulate_observation"] == "pass"


def test_resolve_agentic_settings_rejects_bad_simulate_value(tmp_path):
    workflow_path = tmp_path / "workflow.json"
    workflow_path.write_text(
        json.dumps(
            {
                "simulate_observation": "unknown",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="simulate_observation"):
        _resolve_agentic_settings(_base_args(str(workflow_path)))
