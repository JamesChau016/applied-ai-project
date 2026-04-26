# External Agent Execution Packet

Use this entire packet as the prompt for Claude Code or another external coding agent.

## Injection Command

EXTERNAL AGENT EXECUTION COMMAND (PASTE INTO CLAUDE CODE OR OTHER AGENTS)

You are implementing one feature in this repository.
Follow this protocol strictly:
1) planning/external-agent/protocol.md
2) planning/external-agent/job.example.json

Execution rules:
- Follow Plan -> Execute -> Observe -> Re-plan exactly once per attempt.
- Respect scope and constraints from the job file.
- Retry only if failure is local/actionable and within retry_budget.
- Stop on ambiguous failures.

Output format required after completion:
- PLAN: scope, risks, verification strategy
- EXECUTE: files changed and why
- OBSERVE: commands run, pass/fail, failure classification
- RE-PLAN: whether retried, narrowed scope, stop/escalation reason
- FINAL: concise summary and validation evidence

If the feature request changes, keep this command file the same and only replace the job file content.

## Protocol

# External Agent Workflow Protocol

Purpose: provide a strict, portable workflow for external coding agents (for example Claude Code) to follow when implementing features in this repository.

## 1. Setup

1. Workspace root must be this repository root.
2. Default runtime is local only; no external services are required.
3. The default project entrypoints must keep working:
   - `python -m src.main`
   - `python -m pytest -q`
4. All work must use the Plan -> Execute -> Observe -> Re-plan lifecycle.

## 2. Required Inputs

The agent must receive the following inputs before starting:

1. Objective: clear feature goal in one sentence.
2. Scope: allow-listed files or folders the agent may change.
3. Retry budget: default `1` retry after first failed observation.
4. Success criteria: concrete checks that define success.
5. Done definition: what must be true before stopping.

If any required input is missing, the agent must stop and request clarification.

## 3. Rules

1. Apply bounded edits only inside scope.
2. Do not modify unrelated files.
3. Do not use destructive git operations.
4. Prefer smallest possible change set.
5. Keep behavior deterministic and testable.
6. Observe phase must run cheapest validation first.
7. Failures must be classified as:
   - `actionable`: local and fixable in current scope
   - `ambiguous`: unclear root cause or outside local scope
8. Re-plan only on actionable failures and only within retry budget.
9. Stop and escalate on ambiguous failures.

## 4. Constraints

1. Local repository only.
2. No hidden long-running autonomous loop.
3. Max retries: 1 by default unless explicitly overridden.
4. Re-plan must narrow scope, not broaden it.
5. Every run must produce a phase log (Plan, Execute, Observe, Re-plan).

## 5. Phase Contract

## Plan

Output must include:

1. Target scope
2. Risks
3. Verification strategy
4. Minimal change slice

## Execute

Output must include:

1. Touched files
2. What changed
3. Why each change was needed

## Observe

Output must include:

1. Commands/checks executed
2. Pass/fail result
3. Failure classification (`actionable` or `ambiguous`)
4. Evidence snippets for failures

## Re-plan

Output must include:

1. Whether re-plan occurred
2. Updated narrowed scope
3. Retry decision
4. Escalation reason when stopping

## 6. Stop Conditions

The agent must stop when any of the following is true:

1. Success criteria are met and done definition is satisfied.
2. Failure is ambiguous.
3. Retry budget is exhausted.
4. No valid scope remains after re-plan.

## 7. Acceptance Checklist

A run is complete only when all checks pass:

1. Scope boundaries were respected.
2. Existing project behavior was not regressed.
3. Validation evidence is present.
4. Final summary states what changed and why.

## Job Configuration

```json
{
  "job_name": "tempo-bias-feature",
  "objective": "Add tempo-bias scoring to recommendations and validate behavior with tests",
  "scope": [
    "src/recommender.py",
    "tests"
  ],
  "retry_budget": 1,
  "success_criteria": [
    "Tempo-bias is integrated into score computation",
    "Existing recommender tests still pass",
    "New or updated tests cover tempo-bias behavior"
  ],
  "done_definition": [
    "Plan/Execute/Observe/Re-plan steps are reported",
    "All changed files are listed with intent",
    "Validation output is summarized"
  ],
  "constraints": [
    "Edit only scoped files",
    "Avoid unrelated refactors",
    "Stop on ambiguous failures and report blockers"
  ],
  "validation_commands": [
    "python -m pytest -q"
  ],
  "deliverables": [
    "Updated scoring logic",
    "Updated tests",
    "Run summary"
  ]
}
```
