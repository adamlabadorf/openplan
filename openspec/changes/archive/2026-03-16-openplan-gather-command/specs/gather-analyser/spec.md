# Spec: gather-analyser

## ADDED

### R1 — `GatherAnalyser` class
A class `GatherAnalyser` MUST exist in `openplan/core/gather.py`.
Constructor: `GatherAnalyser(project_dir: Path, model: Optional[str] = None)`.

### R2 — `analyse() -> GatherContext` method
`GatherAnalyser.analyse()` MUST read and synthesise:
1. `openplan/HISTORY.md` — previously planned/deferred items
2. `openplan/archived/` — prior roadmap artifacts
3. `design/` directory — design documents (markdown files)
4. `src/` module structure — inferred from `__init__.py` and top-level dirs
5. `openspec/changes/` — post-initial-implementation additions
6. Test shape — via `pytest --collect-only -q` (gracefully skipped if pytest unavailable)

### R3 — `GatherContext` dataclass
A `GatherContext` dataclass (or TypedDict) MUST be returned by `analyse()` with fields:
- `existing_modules: list[str]`
- `deferred_items: list[str]` (from HISTORY.md)
- `post_plan_changes: list[str]` (from openspec/changes since last archive)
- `test_count: int`
- `design_docs: list[str]` (filenames found)
- `prior_roadmap_ids: list[str]`

### R4 — Graceful degradation
If any source directory does not exist (e.g. no `design/`), `analyse()` MUST
log a warning and continue rather than raising.

### R5 — `generate(context: GatherContext) -> tuple[Vision, Roadmap]` method
`GatherAnalyser.generate()` MUST use the `PlanningEngine` (or `OpenCodeClient`
directly) to produce a new `Vision` and `Roadmap` from the `GatherContext`.

#### Scenario: missing src dir
Given `--src-dir` points to a non-existent directory,
When `GatherAnalyser.analyse()` runs,
Then a warning is logged and `existing_modules` is `[]` (no error raised).

#### Scenario: HISTORY.md present with deferred items
Given `HISTORY.md` contains a note mentioning deferred features,
When `GatherAnalyser.analyse()` runs,
Then `deferred_items` is non-empty.
