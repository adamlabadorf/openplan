# Design: `openplan implement` Command

## Architecture

### Decision 1 — `ImplementationPipeline` is a pure orchestrator
It does not generate planning artifacts (that's `PlanningEngine`).
It loads existing feature YAML files, calls ACPClient per feature,
and runs pytest as a gate. It owns no AI/LLM calls directly.

### Decision 2 — `EpicStatus` enum lives in `pipeline.py`
Keeps status concern co-located with the pipeline. `engine.py` stays
focused on AI-assisted generation. No circular dependency.

### Decision 3 — Feature discovery via glob
`Path(project_dir).glob(f"openplan/features/{epic.id}-*.yaml")`
Simple, convention-based, no registry needed. Files created by
`decompose_epic` already follow this naming convention.

### Decision 4 — ACPClient factory injection
```python
class ImplementationPipeline:
    def __init__(self, ..., acp_client_factory=None):
        self._client_factory = acp_client_factory or OpenCodeClient
```
Default is the real `OpenCodeClient`. Tests pass a mock factory.
No monkey-patching required.

### Decision 5 — `PipelineError` is a new exception in `pipeline.py`
Does not extend `PlanningError` — these are different failure modes
(planning vs. CI/test gate). Keeps error hierarchy clean.

### Decision 6 — `--from-epic` by ID, not index
Avoids fragility when epic order changes. The pipeline skips epics
until it finds the matching ID in the resolved order.

### Decision 7 — Typer for CLI, Rich for output
`openplan implement` is a new `typer` command added to the existing
`app` in `cli/main.py`. Uses `rich.console.Console` and
`rich.table.Table` for the live status display, consistent with
the rest of the CLI.

### Decision 8 — `run_pipeline.py` becomes a thin wrapper
```python
from openplan.core.pipeline import ImplementationPipeline
pipeline = ImplementationPipeline(project_dir=project_dir, ...)
pipeline.run(roadmap)
```
All generic logic moves to `core/pipeline.py`. The example script
keeps only its roadmap-loading and arg-parsing boilerplate.

## Module Structure

```
openplan/
  cli/
    main.py              ← add `implement` command
  core/
    pipeline.py (new)    ← ImplementationPipeline, EpicStatus, PipelineResult, PipelineError
    engine.py            ← no change needed (ordering already done)
    ordering.py          ← used by pipeline
    schemas.py           ← used by pipeline
tests/
  test_pipeline.py (new) ← unit tests with mocked ACPClient
examples/pubwatch/
  run_pipeline.py        ← thin wrapper
```

## `ImplementationPipeline` sketch

```python
@dataclass
class PipelineResult:
    epic_statuses: dict[str, EpicStatus]
    features_total: int
    features_implemented: int
    failed_epic: str | None = None

class PipelineError(Exception):
    pass

class ImplementationPipeline:
    def __init__(self, project_dir, openspec_dir=None, model=None,
                 skip_tests=False, from_epic=None, acp_client_factory=None):
        ...

    def run(self, roadmap: Roadmap) -> PipelineResult:
        ordered = resolve_epic_order(roadmap.epics)
        # skip, implement, gate loop
        ...
        self._write_report(result)
        return result

    def dry_run(self, roadmap: Roadmap) -> None:
        ordered = resolve_epic_order(roadmap.epics)
        # print table only
        ...

    def _run_pytest(self) -> bool:
        result = subprocess.run(["python", "-m", "pytest"],
                                cwd=self.project_dir,
                                capture_output=True, text=True)
        return result.returncode in (0, 5)

    def _write_report(self, result: PipelineResult) -> None:
        # write openplan/implementation_report.md
        ...
```

## CLI sketch

```python
@app.command()
def implement(
    project_dir: Path = typer.Option(Path("."), help="Project root"),
    openspec_dir: Optional[Path] = typer.Option(None),
    model: Optional[str] = typer.Option(None),
    skip_tests: bool = typer.Option(False, "--skip-tests"),
    from_epic: Optional[str] = typer.Option(None, "--from-epic"),
    dry_run: bool = typer.Option(False, "--dry-run"),
):
    ...
```

## Non-Goals
- Parallel epic implementation (sequential first)
- Feature-level test gates (epic-level is sufficient for 1.x)
- Resuming a partially-completed pipeline run from disk
