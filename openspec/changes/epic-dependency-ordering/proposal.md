# Proposal: Epic Dependency Ordering + Pipeline Test Gate

## Problem

OpenPlan's pipeline treats all features as a flat sequence:
decompose all epics → stabilize all → export all → implement all.

It has no concept of epic-level dependencies. For layered systems
(e.g. a project where a Storage epic must exist before a Validation epic
can import it), the pipeline tries to implement later-stage features before
earlier-stage code exists, fails silently, and continues anyway.

Three specific gaps:

1. **No `depends_on` on `Epic`** — the schema has no field to declare
   "epic-003 requires epic-002". The pipeline has nothing to order by.

2. **No topological sort** — the pipeline iterates `roadmap.epics` in
   declaration order. Even if `depends_on` existed there is no graph
   traversal to enforce it.

3. **No test gate between epics** — after implementing an epic's features
   there is no `pytest` run to verify correctness before proceeding.
   Failures are logged but the loop continues unchecked.

## Proposed Solution

Three additive, backwards-compatible changes:

### 1. `Epic.depends_on: list[str]`
Add a `depends_on` field (defaults to `[]`) to the `Epic` schema.
Validate at `Roadmap` construction that:
- All referenced IDs exist in the same roadmap.
- No cycles exist (raise `PlanningError` with both IDs named).

Existing roadmaps (e.g. pubwatch) keep working unchanged.

### 2. `resolve_epic_order(epics) -> list[Epic]` utility
New `openplan/core/ordering.py` module.
Standard Kahn's algorithm over the `depends_on` graph.
Raises `PlanningError` on cycle detection.
`PlanningEngine` calls this before the implementation loop.

### 3. Epic-level test gate in the pipeline
After implementing all features in an epic, run `pytest` in the
project directory.
- Tests pass → mark epic complete, proceed.
- Tests fail → halt with a clear error; mark downstream epics `blocked`.
- `--skip-tests` flag disables gating for rapid iteration.

`openplan status` output should reflect epic states:
`not_started` / `in_progress` / `passing` / `failed` / `blocked`.

## Capabilities

- epic-dependency-schema
- epic-ordering
- pipeline-test-gate

## Affected Files

- `openplan/core/schemas.py`
- `openplan/core/ordering.py` (new)
- `openplan/core/engine.py`
- `examples/pubwatch/run_pipeline.py`
- `tests/test_schemas.py`
- `tests/test_ordering.py` (new)
- `tests/test_integration.py`
