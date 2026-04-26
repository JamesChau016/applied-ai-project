from src.agentic_workflow import (
    AgenticWorkflowController,
    FailureKind,
    ObservationOutput,
    ObservationStatus,
    WorkflowContract,
    WorkflowInput,
)


def _workflow_input(scope=None, retry_budget=1):
    return WorkflowInput(
        objective="Fix a local failure",
        scope=scope or ["src", "tests"],
        contract=WorkflowContract(
            success_criteria="Observe passes",
            done_definition="All phases completed",
            retry_budget=retry_budget,
        ),
    )


def test_run_stops_on_ambiguous_failure_without_replan():
    controller = AgenticWorkflowController()
    result = controller.run(
        workflow_input=_workflow_input(),
        simulate_observation=FailureKind.AMBIGUOUS,
    )

    assert result.observation.status == ObservationStatus.FAILED
    assert result.replan.did_replan is False
    assert result.attempts_used == 1


def test_run_retries_once_on_actionable_failure():
    controller = AgenticWorkflowController()
    result = controller.run(
        workflow_input=_workflow_input(retry_budget=1),
        simulate_observation=FailureKind.ACTIONABLE,
    )

    assert result.observation.status == ObservationStatus.FAILED
    assert result.replan.did_replan is True
    assert result.attempts_used == 2


def test_replan_prefers_syntax_file_scope():
    controller = AgenticWorkflowController()
    observation = ObservationOutput(
        status=ObservationStatus.FAILED,
        failure_kind=FailureKind.ACTIONABLE,
        summary="syntax failure",
        details=["SyntaxError in src/main.py: invalid syntax line 1"],
    )

    narrowed_scope = controller.replan(["src", "tests"], observation)

    assert narrowed_scope == ["src/main.py"]


def test_replan_removes_missing_targets():
    controller = AgenticWorkflowController()
    observation = ObservationOutput(
        status=ObservationStatus.FAILED,
        failure_kind=FailureKind.ACTIONABLE,
        summary="missing target",
        details=["Missing target: tests"],
    )

    narrowed_scope = controller.replan(["src", "tests"], observation)

    assert narrowed_scope == ["src"]
