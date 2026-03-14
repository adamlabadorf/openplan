# Spec: Pipeline Test Gate

## ADDED
- `--skip-tests` flag on `run_pipeline.py`
- Epic status tracking (`not_started` / `in_progress` / `passing` / `failed` / `blocked`)
- Pytest gate after each epic's features are implemented
- Blocked-dependency propagation on test failure
- Epic status column in pipeline summary output and `pipeline_result.md`

## Requirements

### R1 — Test gate after epic implementation
After all features in an epic have been implemented, the pipeline MUST
run `pytest` in the project directory before proceeding to the next epic.

### R2 — Pass behaviour
If `pytest` exits with code 0, the epic MUST be marked `passing` and
implementation proceeds to the next epic in resolved order.

### R3 — Fail behaviour
If `pytest` exits with non-zero, the pipeline MUST:
- Mark the failed epic as `failed`.
- Mark all epics that (transitively) depend on the failed epic as `blocked`.
- Halt immediately with a clear error message naming the failed epic.

### R4 — `--skip-tests` flag
`run_pipeline.py` MUST accept a `--skip-tests` boolean flag.
When set, test gates are skipped entirely; epics are still implemented
in resolved dependency order.

### R5 — Epic status tracking
Each epic MUST have a status tracked during the pipeline run:
`not_started` | `in_progress` | `passing` | `failed` | `blocked`.

### R6 — Status in output
The pipeline results summary MUST include each epic's final status.

### R7 — No test directory assumption
The test gate MUST discover tests using `pytest`'s default discovery
(i.e. `pytest` with no path argument) executed from the project root.
It MUST NOT hard-code a test directory path.

## Scenarios

### Scenario A — All tests pass
Given epic-001 features are implemented and `pytest` returns exit 0,
When the pipeline evaluates the gate,
Then epic-001 is `passing` and epic-002 implementation begins.

### Scenario B — Tests fail
Given epic-001 features are implemented and `pytest` returns exit 1,
When the pipeline evaluates the gate,
Then epic-001 is `failed`, epic-002 (which depends on epic-001) is `blocked`,
and the pipeline halts with an error naming epic-001.

### Scenario C — No tests present
Given no test files exist in the project directory and `pytest` exits 5
(no tests collected), When the pipeline evaluates the gate,
Then the epic is treated as `passing` (exit 5 is not a failure).

### Scenario D — `--skip-tests` flag
Given `--skip-tests` is passed to the pipeline,
When the pipeline runs,
Then no `pytest` invocations occur, epics are implemented in resolved
dependency order, and all epics are marked `passing` on completion.
