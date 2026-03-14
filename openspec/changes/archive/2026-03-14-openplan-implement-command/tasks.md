# Tasks: `openplan implement` Command

## openplan/core/pipeline.py (new file)

- [ ] Create `openplan/core/pipeline.py`
- [ ] Define `EpicStatus` enum: `PENDING`, `IN_PROGRESS`, `PASSING`, `FAILED`, `BLOCKED`, `SKIPPED`
- [ ] Define `PipelineError(Exception)` with a message that names the failing epic
- [ ] Define `PipelineResult` dataclass: `epic_statuses: dict[str, EpicStatus]`, `features_total: int`, `features_implemented: int`, `failed_epic: str | None = None`
- [ ] Define `ImplementationPipeline.__init__(self, project_dir, openspec_dir=None, model=None, skip_tests=False, from_epic=None, acp_client_factory=None)`
- [ ] Implement `ImplementationPipeline.run(self, roadmap) -> PipelineResult`:
  - Call `resolve_epic_order(roadmap.epics)`
  - Initialise `epic_statuses` with `EpicStatus.PENDING` for all epics
  - For each epic in resolved order:
    - If `from_epic` set and epic not yet reached → mark `SKIPPED`, continue
    - Mark `IN_PROGRESS`
    - Discover features via `Path(project_dir).glob(f"openplan/features/{epic.id}-*.yaml")`
    - For each feature: open ACPClient (via factory), run `/opsx-ff <feature-id>` then `/opsx-apply <feature-id>`
    - Unless `skip_tests`: call `_run_pytest()`; on fail → mark `FAILED`, propagate `BLOCKED`, raise `PipelineError`
    - On pass: mark `PASSING`
  - Call `_write_report(result)`
  - Return `PipelineResult`
- [ ] Implement `ImplementationPipeline.dry_run(self, roadmap) -> None`:
  - Call `resolve_epic_order(roadmap.epics)`
  - Print resolved order with dependency arrows using `rich`
  - Print feature list per epic (glob discovery, same as `run`)
  - Print "Dry run — no code will be executed"
- [ ] Implement `ImplementationPipeline._run_pytest(self) -> bool`:
  - `subprocess.run(["python", "-m", "pytest"], cwd=self.project_dir, capture_output=True, text=True)`
  - Return `True` if returncode in `(0, 5)`, else `False`
  - Store stdout/stderr on self for report writing
- [ ] Implement `ImplementationPipeline._propagate_blocked(self, failed_epic_id, epic_statuses, roadmap)`:
  - Mark all epics that (directly or transitively) depend on `failed_epic_id` as `BLOCKED`
- [ ] Implement `ImplementationPipeline._write_report(self, result, roadmap)`:
  - Write `<project_dir>/openplan/implementation_report.md`
  - Include: timestamp, per-epic status + feature count + pytest summary, totals

## openplan/cli/main.py

- [ ] Import `ImplementationPipeline`, `PipelineError`, `EpicStatus` from `openplan.core.pipeline`
- [ ] Add `implement` typer command with options: `--project-dir`, `--openspec-dir`, `--model`, `--skip-tests`, `--from-epic`, `--dry-run`
- [ ] In `implement`: load roadmap YAML from `<project-dir>/openplan/roadmaps/*.yaml` (first match)
- [ ] If `--dry-run`: call `pipeline.dry_run(roadmap)`, exit 0
- [ ] Otherwise: call `pipeline.run(roadmap)`, print rich status table, exit 0 on success / exit 1 on `PipelineError`
- [ ] Use `rich.console.Console` for all output; display live epic status updates

## examples/pubwatch/run_pipeline.py

- [ ] Import `ImplementationPipeline` from `openplan.core.pipeline`
- [ ] Replace the inline epic loop, pytest gate, and status tracking with `ImplementationPipeline(project_dir=..., skip_tests=args.skip_tests)`
- [ ] Keep pubwatch-specific setup (roadmap loading, arg parsing) as the thin wrapper
- [ ] Verify the script still runs end-to-end after refactor

## tests/test_pipeline.py (new file)

- [ ] Create `tests/test_pipeline.py`
- [ ] Test: `EpicStatus` has all 6 members
- [ ] Test: `ImplementationPipeline` initialises with all epics `PENDING`
- [ ] Test: `dry_run()` prints epic order without calling acp_client_factory
- [ ] Test: `run()` with mocked ACPClient + pytest exit 0 → all epics `PASSING`, `PipelineResult.failed_epic is None`
- [ ] Test: `run()` with mocked pytest exit 1 → epic marked `FAILED`, dependents marked `BLOCKED`, `PipelineError` raised
- [ ] Test: `--from-epic` → earlier epics marked `SKIPPED`, later implemented
- [ ] Test: `--skip-tests` → pytest never called, all epics `PASSING`
- [ ] Test: `_write_report()` creates `openplan/implementation_report.md` with correct content
- [ ] Test: feature discovery globs correct files for a given epic ID
