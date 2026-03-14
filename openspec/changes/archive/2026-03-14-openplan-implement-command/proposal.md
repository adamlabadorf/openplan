# Proposal: `openplan implement` — Generic Pipeline Command

## Why

The implementation pipeline currently only exists as `examples/pubwatch/run_pipeline.py`
— a project-specific script every new project must copy and adapt. There is no
generic `openplan implement` CLI command. This means:

1. Every project reimplements the same boilerplate (load roadmap, loop epics,
   call ACPClient, run pytest gate).
2. The pubwatch script mixes hardcoded paths and project-specific logic with
   generic pipeline logic.
3. New OpenPlan users have no path from "fully planned project" to "start
   implementing" — the CLI dead-ends at `export-to-openspec`.

## What Changes

- New CLI command `openplan implement` wired into `openplan/cli/main.py`
- New `openplan/core/pipeline.py` — `ImplementationPipeline` class extracted
  from `run_pipeline.py`, made generic (no project-specific paths)
- `openplan/core/engine.py` — add `EpicStatus` enum and status tracking
- `examples/pubwatch/run_pipeline.py` — refactored to thin wrapper over
  `ImplementationPipeline`
- `tests/test_pipeline.py` (new) — unit tests with mocked ACPClient + pytest

## Capabilities

- implement-command
- implementation-pipeline
- epic-status-tracking

## Affected Files

- `openplan/cli/main.py`
- `openplan/core/pipeline.py` (new)
- `openplan/core/engine.py`
- `examples/pubwatch/run_pipeline.py`
- `tests/test_pipeline.py` (new)
