# Spec: ImplementationPipeline

## ADDED
- `openplan/core/pipeline.py` with `ImplementationPipeline` class

## Requirements

### R1 — Class exists
`openplan.core.pipeline.ImplementationPipeline` MUST exist and be importable.

### R2 — Constructor
`ImplementationPipeline(project_dir, openspec_dir, model, skip_tests, from_epic)`
MUST accept these arguments (all optional except `project_dir`).

### R3 — `run()` method
`pipeline.run(roadmap)` MUST:
1. Call `resolve_epic_order(roadmap.epics)` to get ordered epics
2. For each epic in order:
   a. If epic ID < `from_epic` in resolved order → mark `skipped`, continue
   b. Mark epic `in_progress`
   c. Find all feature YAML files matching `openplan/features/<epic-id>-*.yaml`
   d. For each feature: open ACPClient, run `/opsx-ff <feature-id>`, then `/opsx-apply <feature-id>`
   e. Unless `skip_tests`: run `pytest` in `project_dir`; exit 0 or 5 = pass
   f. Pass → mark `passing`; non-zero → mark `failed`, mark transitive dependents `blocked`, raise `PipelineError`
3. Return `PipelineResult` dataclass

### R4 — `dry_run()` method
`pipeline.dry_run(roadmap)` MUST print resolved order and features without
opening any ACP sessions or running pytest. Returns None.

### R5 — `PipelineResult`
A dataclass with fields:
- `epic_statuses: dict[str, EpicStatus]`
- `features_total: int`
- `features_implemented: int`
- `failed_epic: str | None`

### R6 — `PipelineError`
Raised on test gate failure. Message MUST name the failing epic.

### R7 — ACPClient injection for testing
The `ImplementationPipeline` MUST accept an optional `acp_client_factory`
parameter (callable that returns an ACPClient context manager) to allow
test-time mocking without subprocess calls.

### R8 — No pubwatch-specific logic
`ImplementationPipeline` MUST contain zero references to pubwatch, and
MUST NOT hard-code any path other than the standard OpenPlan directory
layout.

## Scenarios

### Scenario A — Feature discovery
Given `openplan/features/epic-001-feature-001.yaml` exists,
When `pipeline.run(roadmap)` is called for a roadmap with epic-001,
Then `epic-001-feature-001` is included in the feature list for epic-001.

### Scenario B — Test gate pass
Given ACPClient succeeds for all features and pytest exits 0,
When `pipeline.run(roadmap)` returns,
Then result.epic_statuses["epic-001"] == EpicStatus.PASSING.

### Scenario C — Test gate fail
Given pytest exits 1 after implementing epic-001,
When `pipeline.run(roadmap)` is called,
Then a `PipelineError` is raised naming epic-001.

### Scenario D — Mocked ACPClient
Given an `acp_client_factory` that returns a mock,
When `pipeline.run(roadmap)` is called,
Then no real subprocess is spawned and the mock's methods are called.
