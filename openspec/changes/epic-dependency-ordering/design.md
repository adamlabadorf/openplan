# Design: Epic Dependency Ordering + Pipeline Test Gate

## Architecture

### Decision 1 — `depends_on` as a simple `list[str]` of epic IDs
Rationale: mirrors the existing `Feature.dependencies` pattern; avoids
introducing a `DependencyRef` wrapper that would break existing YAML.

### Decision 2 — Cycle detection in two places
1. At `Roadmap` model construction (Pydantic `model_validator`) — catches
   bad input early regardless of how the roadmap is loaded.
2. Inside `resolve_epic_order` — defensive, for callers that construct
   an Epic list outside a Roadmap.

### Decision 3 — Kahn's algorithm (BFS, FIFO queue)
Rationale: O(V+E), naturally preserves insertion order for independent
epics, well-understood, easy to test. `collections.deque` as queue.

### Decision 4 — `ordering.py` is a pure function module
No class needed. Single public function `resolve_epic_order`.
Zero dependencies on `engine.py` or `schemas.py` internals beyond
the `Epic` type. Keeps the module independently testable.

### Decision 5 — Test gate runs `subprocess.run(["pytest"], cwd=project_dir)`
`pytest` is already a dev dependency. `cwd` is set to the project root.
`capture_output=True` so pipeline output stays clean; test output is
printed only on failure.
Exit code 5 ("no tests collected") is treated as success (R7).

### Decision 6 — Epic status tracked in `run_pipeline.py`, not in Engine
`PlanningEngine` is a generation/planning tool, not a CI runner.
`run_pipeline.py` (or any host script) owns epic lifecycle state.
A simple `dict[str, str]` (`epic_id → status`) is sufficient for now.

### Decision 7 — `--skip-tests` as an argparse flag on `run_pipeline.py`
`run_pipeline.py` is a demo script, not a library. `argparse` is fine.
Library users who call `PlanningEngine` directly are not affected.

## Module Changes

### `openplan/core/schemas.py`
- Add `depends_on: list[str] = Field(default_factory=list)` to `Epic`.
- Add `@model_validator(mode='after')` on `Roadmap` that:
  1. Builds a set of all epic IDs.
  2. Checks every `depends_on` reference exists → `PlanningError`.
  3. Runs cycle detection (DFS colour map) → `PlanningError`.

### `openplan/core/ordering.py` (new)
```python
from collections import deque
from openplan.core.schemas import Epic
from openplan.core.engine import PlanningError

def resolve_epic_order(epics: list[Epic]) -> list[Epic]:
    ...  # Kahn's algorithm
```

### `openplan/core/engine.py`
- Import `resolve_epic_order` from `ordering`.
- In `decompose_epic` loop / wherever the pipeline iterates epics: call
  `resolve_epic_order(roadmap.epics)` to get the ordered list before
  iterating.

### `examples/pubwatch/run_pipeline.py`
- Add `--skip-tests` argparse flag (default `False`).
- After implementing each epic's features, call test gate:
  ```python
  result = subprocess.run(["pytest"], cwd=project_dir, capture_output=True)
  if result.returncode not in (0, 5) and not args.skip_tests:
      # mark failed + blocked, halt
  ```
- Track `epic_status: dict[str, str]` and print in summary.

### New test files
- `tests/test_ordering.py` — unit tests for `resolve_epic_order`
- `tests/test_schemas.py` — extend with `depends_on` + cycle validation tests
- `tests/test_integration.py` — extend with dependency ordering integration test

## Non-Goals
- Persistent epic status across pipeline runs (out of scope for 1.0).
- Parallel epic implementation (sequential-first; parallelism later).
- Feature-level dependency ordering (already handled by `Feature.dependencies`).
