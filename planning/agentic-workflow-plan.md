# Agentic Workflow Plan

Implement the agentic workflow as a Plan -> Execute -> Observe -> Re-plan controller rather than a free-running autonomous agent. The first version should be local to the repo, deterministic enough to test, and isolated from the existing recommender demo so `python -m src.main` keeps working as-is.

## Phases

1. Define the workflow contract first: inputs, outputs, success criteria, retry budget, and what counts as "done".
2. Extract an orchestration layer that owns the Plan -> Execute -> Observe -> Re-plan state machine and keeps each phase separate and testable.
3. Build the Plan phase so it produces a structured plan with target scope, risks, and the narrowest useful verification strategy.
4. Build the Execute phase so it applies only bounded changes in the planned slice and reports exactly what it touched.
5. Build the Observe phase so it runs the cheapest relevant validation first, captures outputs, and classifies failures as actionable or ambiguous.
6. Build the Re-plan phase so it adjusts strategy using observation results and retries once when failure is local and actionable.
7. Add orchestration policies for retry, stop, and escalation so behavior stays predictable.
8. Wire the workflow into the CLI without changing the existing demo recommender path.
9. Add tests for successful runs, failed observations, re-plan behavior, and regression coverage for the current CLI path.
10. Update the README if needed so the new mode and its limits are clear to a user.

## Relevant Files

- [src/main.py](../src/main.py) for the CLI entry point and new workflow mode.
- [src/recommender.py](../src/recommender.py) to keep the current demo logic stable.
- [tests/test_recommender.py](../tests/test_recommender.py) for regression coverage.
- [README.md](../README.md) for user-facing instructions.

## Verification

1. Run a focused test suite for the workflow controller once it exists.
2. Run the existing recommender tests to confirm the demo behavior stays unchanged.
3. Run a narrow CLI invocation for the new agentic mode and confirm it prints Plan, Execute output, Observe result, and Re-plan decision.
4. Deliberately trigger a local failure once to verify the Observe -> Re-plan path before expanding scope.

## Decisions

- The workflow must follow Plan -> Execute -> Observe -> Re-plan on every run.
- The first version should allow only one retry.
- The workflow stays local to the repo and does not depend on external services.
- The current recommender demo remains the default path.
