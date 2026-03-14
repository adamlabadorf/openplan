# Tasks: Epic Dependency Ordering + Pipeline Test Gate

## openplan/core/schemas.py

- [ ] Add `depends_on: list[str] = Field(default_factory=list)` to `Epic`
- [ ] Add `@model_validator(mode='after')` to `Roadmap` that validates all `depends_on` IDs exist among sibling epic IDs (raises `PlanningError` on unknown ID, naming the referencing epic and missing ID)
- [ ] Extend `Roadmap` model validator to detect cycles using DFS colour map (raises `PlanningError` naming both epic IDs in the cycle)

## openplan/core/ordering.py (new file)

- [ ] Create `openplan/core/ordering.py`
- [ ] Implement `resolve_epic_order(epics: list[Epic]) -> list[Epic]` using Kahn's algorithm (BFS with `collections.deque`)
- [ ] Return epics in topological order; preserve declaration order for independent epics
- [ ] Raise `PlanningError` if a cycle is detected (should not happen if Roadmap validator ran, but defensive)
- [ ] Add module docstring and function docstring

## openplan/core/engine.py

- [ ] Import `resolve_epic_order` from `openplan.core.ordering`
- [ ] In `decompose_epic` and any pipeline loop that iterates epics, obtain ordered list via `resolve_epic_order(roadmap.epics)` before iterating

## examples/pubwatch/run_pipeline.py

- [ ] Add `--skip-tests` argparse flag (type `bool`, action `store_true`, default `False`)
- [ ] Add `epic_status: dict[str, str]` tracking dict initialised with `"not_started"` for all epics
- [ ] After implementing each epic's features, run `subprocess.run(["pytest"], cwd=project_dir, capture_output=True, text=True)` (skip if `--skip-tests`)
- [ ] Treat pytest exit codes 0 and 5 as pass; all others as fail
- [ ] On pass: set epic status to `"passing"`, continue
- [ ] On fail: set epic status to `"failed"`, mark all transitively dependent epics as `"blocked"`, print stderr from pytest, halt pipeline with non-zero exit
- [ ] Apply `resolve_epic_order` to the epic list before the implementation loop
- [ ] Include epic status column in the final results summary printed to stdout and written to `pipeline_result.md`

## tests/test_schemas.py

- [ ] Add test: `Epic` with no `depends_on` key deserialises with `depends_on == []`
- [ ] Add test: `Roadmap` with valid `depends_on` references constructs without error
- [ ] Add test: `Roadmap` with unknown `depends_on` reference raises `PlanningError` (or `ValidationError` wrapping it)
- [ ] Add test: `Roadmap` with cycle in `depends_on` raises `PlanningError` (or `ValidationError` wrapping it)

## tests/test_ordering.py (new file)

- [ ] Create `tests/test_ordering.py`
- [ ] Test: empty list returns empty list
- [ ] Test: single epic returns `[epic]`
- [ ] Test: linear chain A→B→C declared as [A, B, C] returns [A, B, C]
- [ ] Test: linear chain declared in reverse [C, B, A] returns [A, B, C]
- [ ] Test: diamond dependency (B depends A, C depends A, D depends B+C) — A first, D last, B/C in declaration order
- [ ] Test: no dependencies — returns input order unchanged
- [ ] Test: cycle raises `PlanningError`

## tests/test_integration.py

- [ ] Add integration test: roadmap with `depends_on` declarations is loaded, `resolve_epic_order` is called, epics appear in correct order
