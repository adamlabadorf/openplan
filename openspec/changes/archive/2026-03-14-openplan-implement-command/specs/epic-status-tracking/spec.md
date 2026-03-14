# Spec: Epic Status Tracking

## ADDED
- `EpicStatus` enum in `openplan/core/pipeline.py`
- Status propagation logic in `ImplementationPipeline`

## Requirements

### R1 — `EpicStatus` enum values
MUST have exactly these members:
`PENDING`, `IN_PROGRESS`, `PASSING`, `FAILED`, `BLOCKED`, `SKIPPED`

### R2 — Initial state
All epics in a roadmap MUST start as `PENDING` when the pipeline is initialised.

### R3 — `SKIPPED` for `--from-epic`
All epics that precede `--from-epic` in the resolved order MUST be marked
`SKIPPED` without any ACPClient calls or pytest invocations.

### R4 — `BLOCKED` propagation
When an epic is marked `FAILED`, all epics that (directly or transitively)
depend on it MUST be marked `BLOCKED` without any ACPClient calls.

### R5 — Status in report
`implementation_report.md` MUST include all six status values with their
counts and per-epic breakdown.

### R6 — Status in CLI output
The `openplan implement` command MUST display live status updates as epics
transition from `PENDING` → `IN_PROGRESS` → `PASSING`/`FAILED`/`BLOCKED`.

## Scenarios

### Scenario A — Happy path statuses
Given a 3-epic roadmap with no failures,
When `pipeline.run()` completes,
Then all epics have status `PASSING`.

### Scenario B — Blocked propagation
Given epic-003 depends on epic-002 which depends on epic-001,
When epic-001 fails,
Then epic-001 is `FAILED`, epic-002 and epic-003 are `BLOCKED`.

### Scenario C — Skipped epics
Given `--from-epic epic-002` and a roadmap [epic-001, epic-002, epic-003],
When the pipeline runs,
Then epic-001 is `SKIPPED`, epic-002 and epic-003 are implemented normally.
