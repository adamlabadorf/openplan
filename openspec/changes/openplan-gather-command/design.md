# Design: `openplan gather`

## Decisions

### D1 — `GatherAnalyser` is a separate class from `PlanningEngine`
`PlanningEngine` generates artifacts from structured inputs; `GatherAnalyser`
collects unstructured signals (source tree, history, test output) and synthesises
them into `PlanningEngine`-compatible inputs. Keeping them separate maintains
clean boundaries and independent testability.

### D2 — `GatherContext` is a dataclass (not Pydantic)
`GatherContext` is an internal data carrier, not a user-facing schema. A plain
`dataclass` avoids Pydantic validation overhead and keeps the gather module
dependency-light.

### D3 — `pytest --collect-only -q` for test shape
Running pytest in collect-only mode is non-destructive and fast. Output is
parsed for test count by counting lines matching `<module>::<test>`. If pytest
is not available or exits non-zero, `test_count` is set to 0 with a warning.

### D4 — Source module inference via directory scan
Rather than full AST analysis, `GatherAnalyser` infers modules by listing
top-level directories in `src/` that contain an `__init__.py`. This is fast,
reliable, and sufficient for roadmap generation prompts.

### D5 — LLM prompt for `generate()` includes full `GatherContext`
`GatherAnalyser.generate()` constructs a prompt that includes:
- Prior roadmap IDs and titles (from archived/)
- Deferred items list
- Existing module list
- Post-plan OpenSpec changes
This prevents the LLM from re-generating already-delivered work.

### D6 — `GATHER.md` is always written (even `--dry-run`)
`GATHER.md` is an analysis document, not a planning artifact. It should always
be written so the user can review what `gather` found before committing to a
new vision/roadmap.

### D7 — `--decompose` reuses existing `PlanningEngine.decompose_epic()`
No new decomposition logic needed. After `generate()` produces a roadmap,
`--decompose` iterates epics and calls the existing `decompose_epic()` method.

## Module Layout

```
openplan/core/gather.py
  GatherContext(dataclass)
    existing_modules: list[str]
    deferred_items: list[str]
    post_plan_changes: list[str]
    test_count: int
    design_docs: list[str]
    prior_roadmap_ids: list[str]

  GatherAnalyser
    __init__(project_dir: Path, model: Optional[str] = None)
    analyse() -> GatherContext
    generate(context: GatherContext) -> tuple[Vision, Roadmap]
    write_gather_doc(context: GatherContext, gaps: list[str]) -> None
    _infer_modules(src_dir: Path) -> list[str]
    _read_history() -> list[str]          # deferred items
    _read_post_plan_changes() -> list[str]
    _collect_test_count(tests_dir: Path) -> int
```
