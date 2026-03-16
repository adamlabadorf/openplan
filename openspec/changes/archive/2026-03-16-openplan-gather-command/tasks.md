# Tasks: `openplan gather`

## openplan/core/gather.py (new file)

- [ ] Create `openplan/core/gather.py`
- [ ] Define `GatherContext` dataclass with fields: `existing_modules`, `deferred_items`, `post_plan_changes`, `test_count`, `design_docs`, `prior_roadmap_ids`
- [ ] Define `GatherAnalyser(project_dir: Path, model: Optional[str] = None)` class
- [ ] Implement `_infer_modules(src_dir: Path) -> list[str]`: list top-level dirs in src_dir containing `__init__.py`; return `[]` with warning if dir absent
- [ ] Implement `_read_history() -> list[str]`: parse `openplan/HISTORY.md` for notes/deferred items; return `[]` if absent
- [ ] Implement `_read_post_plan_changes() -> list[str]`: list change names from `openspec/changes/` (excluding `archive/`); return `[]` if absent
- [ ] Implement `_collect_test_count(tests_dir: Path) -> int`: run `pytest --collect-only -q`, count collected tests; return 0 on failure with warning
- [ ] Implement `analyse() -> GatherContext`: call all `_*` helpers, populate and return `GatherContext`
- [ ] Implement `write_gather_doc(context: GatherContext, gaps: list[str]) -> None`: write `openplan/GATHER.md` with sections: What Exists, What Was Planned, What Was Deferred, Post-Plan Changes, Gaps Identified, Human Review Required
- [ ] Implement `generate(context: GatherContext) -> tuple[Vision, Roadmap]`: build LLM prompt from context (including prior roadmap IDs, deferred items, modules), call `PlanningEngine` to generate vision and roadmap, return both
- [ ] Persist generated vision YAML to `openplan/visions/`
- [ ] Persist generated roadmap YAML to `openplan/roadmaps/`

## openplan/cli/main.py

- [ ] Add `gather` command with all options: `--project-dir`, `--design-dir`, `--src-dir`, `--tests-dir`, `--model`, `--output-vision`, `--decompose`, `--dry-run`
- [ ] Instantiate `GatherAnalyser` and call `.analyse()`
- [ ] Always call `.write_gather_doc()` (dry-run and normal)
- [ ] If not `--dry-run`: call `.generate()` and persist vision + roadmap
- [ ] If `--decompose` and not `--dry-run`: iterate new roadmap epics and call `PlanningEngine.decompose_epic()` for each
- [ ] Print summary: `GATHER.md` location, vision/roadmap IDs created (if any), gaps count

## tests/test_gather.py (new file)

- [ ] Create `tests/test_gather.py`
- [ ] Fixture: `gather_project_dir` — tmp_path with `src/`, `tests/`, `design/`, `openplan/HISTORY.md`, `openspec/changes/`
- [ ] Test: `_infer_modules()` returns correct list of modules with `__init__.py`
- [ ] Test: `_infer_modules()` returns `[]` (no error) when src_dir absent
- [ ] Test: `_read_history()` returns deferred items from `HISTORY.md`
- [ ] Test: `_read_history()` returns `[]` when `HISTORY.md` absent
- [ ] Test: `_read_post_plan_changes()` returns change names from `openspec/changes/` excluding `archive/`
- [ ] Test: `analyse()` returns populated `GatherContext`
- [ ] Test: `write_gather_doc()` creates `GATHER.md` with all required sections
- [ ] Test: `--dry-run` writes `GATHER.md` but does not create vision/roadmap YAMLs
- [ ] Test: `GatherContext.deferred_items` non-empty when `HISTORY.md` has notes
