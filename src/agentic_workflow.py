from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import ast
import re
from typing import List, Optional


class ObservationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"


class FailureKind(str, Enum):
    NONE = "none"
    ACTIONABLE = "actionable"
    AMBIGUOUS = "ambiguous"


@dataclass
class WorkflowContract:
    success_criteria: str
    done_definition: str
    retry_budget: int = 1


@dataclass
class WorkflowInput:
    objective: str
    scope: List[str]
    contract: WorkflowContract


@dataclass
class PlanStep:
    phase: str
    action: str
    target: str
    verification: str
    risk: str


@dataclass
class PlanOutput:
    target_scope: List[str]
    steps: List[PlanStep]
    verification_strategy: str
    risks: List[str]


@dataclass
class ExecutionOutput:
    touched_targets: List[str]
    actions_taken: List[str]


@dataclass
class ObservationOutput:
    status: ObservationStatus
    failure_kind: FailureKind
    summary: str
    details: List[str] = field(default_factory=list)


@dataclass
class ReplanOutput:
    did_replan: bool
    reason: str
    updated_scope: List[str]


@dataclass
class WorkflowRunResult:
    plan: PlanOutput
    execution: ExecutionOutput
    observation: ObservationOutput
    replan: ReplanOutput
    attempts_used: int


class AgenticWorkflowController:
    """Deterministic Plan -> Execute -> Observe -> Re-plan controller."""

    def run(
        self,
        workflow_input: WorkflowInput,
        simulate_observation: Optional[FailureKind] = None,
    ) -> WorkflowRunResult:
        current_scope = list(workflow_input.scope)
        attempts_used = 0
        had_replan = False

        while True:
            attempts_used += 1
            plan = self.plan(workflow_input.objective, current_scope)
            execution = self.execute(plan)
            observation = self.observe(plan, simulate_observation)

            if observation.status == ObservationStatus.PASSED:
                reason = "Observation passed; no re-plan needed."
                if had_replan:
                    reason = "Observation passed after one local re-plan attempt."
                replan = ReplanOutput(
                    did_replan=had_replan,
                    reason=reason,
                    updated_scope=current_scope,
                )
                return WorkflowRunResult(plan, execution, observation, replan, attempts_used)

            can_retry = attempts_used <= workflow_input.contract.retry_budget
            should_replan = (
                can_retry
                and observation.failure_kind == FailureKind.ACTIONABLE
                and self._has_local_failure(observation)
            )

            if not should_replan:
                reason = "Retry stopped: failure was ambiguous or retry budget exhausted."
                replan = ReplanOutput(
                    did_replan=had_replan,
                    reason=reason,
                    updated_scope=current_scope,
                )
                return WorkflowRunResult(plan, execution, observation, replan, attempts_used)

            current_scope = self.replan(current_scope, observation)
            had_replan = True
            if not current_scope:
                replan = ReplanOutput(
                    did_replan=had_replan,
                    reason="Re-plan removed all targets; stopping to avoid unbounded execution.",
                    updated_scope=current_scope,
                )
                return WorkflowRunResult(plan, execution, observation, replan, attempts_used)

    def plan(self, objective: str, scope: List[str]) -> PlanOutput:
        normalized_scope = scope or ["src", "tests"]
        risks = [
            "Scope too broad can hide root causes.",
            "Validation gaps can let regressions pass.",
        ]
        steps = [
            PlanStep(
                phase="Plan",
                action=f"Define the smallest safe change slice for objective: {objective}",
                target=", ".join(normalized_scope),
                verification="Confirm all targets exist locally",
                risk="Missing files can cause invalid execution scope",
            ),
            PlanStep(
                phase="Execute",
                action="Apply bounded changes only in planned targets",
                target=", ".join(normalized_scope),
                verification="Record exactly what was touched",
                risk="Unbounded edits create hard-to-debug side effects",
            ),
            PlanStep(
                phase="Observe",
                action="Run cheapest relevant validation first",
                target="Python syntax checks for .py targets",
                verification="Classify failures as actionable or ambiguous",
                risk="Ambiguous failures can waste retry budget",
            ),
        ]
        return PlanOutput(
            target_scope=normalized_scope,
            steps=steps,
            verification_strategy="Existence check then Python AST parse for .py files",
            risks=risks,
        )

    def execute(self, plan: PlanOutput) -> ExecutionOutput:
        touched_targets = []
        actions_taken = []
        for target in plan.target_scope:
            touched_targets.append(target)
            actions_taken.append(f"Bounded change set prepared for: {target}")
        return ExecutionOutput(touched_targets=touched_targets, actions_taken=actions_taken)

    def observe(
        self,
        plan: PlanOutput,
        simulate_observation: Optional[FailureKind] = None,
    ) -> ObservationOutput:
        if simulate_observation == FailureKind.ACTIONABLE:
            return ObservationOutput(
                status=ObservationStatus.FAILED,
                failure_kind=FailureKind.ACTIONABLE,
                summary="Simulated local actionable failure.",
                details=["Missing target: simulated/local-scope.py"],
            )

        if simulate_observation == FailureKind.AMBIGUOUS:
            return ObservationOutput(
                status=ObservationStatus.FAILED,
                failure_kind=FailureKind.AMBIGUOUS,
                summary="Simulated ambiguous failure.",
                details=["Validation output is inconclusive."],
            )

        if simulate_observation == FailureKind.NONE:
            return ObservationOutput(
                status=ObservationStatus.PASSED,
                failure_kind=FailureKind.NONE,
                summary="Simulated pass.",
                details=["Validation passed."],
            )

        details: List[str] = []
        failures = []

        for target in plan.target_scope:
            target_path = Path(target)
            if not target_path.exists():
                failures.append((FailureKind.ACTIONABLE, f"Missing target: {target}"))
                continue

            candidate_files: List[Path] = []
            if target_path.is_file() and target_path.suffix == ".py":
                candidate_files.append(target_path)
            elif target_path.is_dir():
                candidate_files.extend(target_path.rglob("*.py"))

            for py_file in candidate_files:
                try:
                    source = py_file.read_text(encoding="utf-8")
                    ast.parse(source)
                except SyntaxError as exc:
                    failures.append(
                        (
                            FailureKind.ACTIONABLE,
                            f"SyntaxError in {py_file}: {exc.msg} line {exc.lineno}",
                        )
                    )
                except OSError as exc:
                    failures.append(
                        (
                            FailureKind.AMBIGUOUS,
                            f"Unable to read {py_file}: {exc}",
                        )
                    )

        if not failures:
            return ObservationOutput(
                status=ObservationStatus.PASSED,
                failure_kind=FailureKind.NONE,
                summary="Validation passed for planned targets.",
                details=["All planned targets passed existence and syntax checks."],
            )

        for _, detail in failures:
            details.append(detail)

        failure_kind = (
            FailureKind.ACTIONABLE
            if all(kind == FailureKind.ACTIONABLE for kind, _ in failures)
            else FailureKind.AMBIGUOUS
        )

        return ObservationOutput(
            status=ObservationStatus.FAILED,
            failure_kind=failure_kind,
            summary="Validation failed in Observe phase.",
            details=details,
        )

    def replan(self, scope: List[str], observation: ObservationOutput) -> List[str]:
        # Re-plan by narrowing to the smallest local actionable scope.
        existing_scope = [target for target in scope if Path(target).exists()]
        if not existing_scope:
            return []

        syntax_targets: List[str] = []
        missing_targets = set()

        for detail in observation.details:
            parsed = self._parse_failure_target(detail)
            if not parsed:
                continue
            kind, target = parsed
            if kind == "syntax":
                syntax_targets.append(target)
            elif kind == "missing":
                missing_targets.add(target)

        # Syntax failures are the tightest local scope; retry those files first.
        if syntax_targets:
            narrowed: List[str] = []
            for target in syntax_targets:
                if target not in narrowed:
                    narrowed.append(target)
            return narrowed

        # Otherwise drop missing targets and keep the remaining local scope.
        if missing_targets:
            filtered = [target for target in existing_scope if target not in missing_targets]
            return filtered

        return existing_scope

    @staticmethod
    def _parse_failure_target(detail: str) -> Optional[tuple[str, str]]:
        missing_prefix = "Missing target: "
        if detail.startswith(missing_prefix):
            target = detail[len(missing_prefix):].strip()
            return ("missing", target)

        syntax_match = re.match(r"^SyntaxError in (.+?):", detail)
        if syntax_match:
            target = syntax_match.group(1).strip()
            return ("syntax", target)

        return None

    @staticmethod
    def _has_local_failure(observation: ObservationOutput) -> bool:
        return any(
            "Missing target" in detail or "SyntaxError" in detail
            for detail in observation.details
        )


def format_workflow_result(result: WorkflowRunResult) -> str:
    lines = []
    lines.append("Agentic Workflow Run")
    lines.append("=" * 60)

    lines.append("PLAN")
    for step in result.plan.steps:
        lines.append(f"- {step.phase}: {step.action}")
        lines.append(f"  Target: {step.target}")
        lines.append(f"  Verify: {step.verification}")
    lines.append("")

    lines.append("EXECUTE")
    for action in result.execution.actions_taken:
        lines.append(f"- {action}")
    lines.append("")

    lines.append("OBSERVE")
    lines.append(f"- Status: {result.observation.status.value}")
    lines.append(f"- Failure kind: {result.observation.failure_kind.value}")
    lines.append(f"- Summary: {result.observation.summary}")
    for detail in result.observation.details:
        lines.append(f"- Detail: {detail}")
    lines.append("")

    lines.append("RE-PLAN")
    lines.append(f"- Did re-plan: {result.replan.did_replan}")
    lines.append(f"- Reason: {result.replan.reason}")
    lines.append(f"- Updated scope: {', '.join(result.replan.updated_scope) if result.replan.updated_scope else '(empty)'}")
    lines.append(f"- Attempts used: {result.attempts_used}")

    return "\n".join(lines)
