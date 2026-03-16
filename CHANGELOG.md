# Changelog

## 1.0.0 (2026-03-08)

### Added
- End-to-end PubWatch example pipeline (vision → epic decomposition → feature stabilization → OpenSpec export → implementation).
- PubWatch demo package (`examples/pubwatch/pubwatch`) with CLI entrypoint and SQLite persistence.

### Changed
- PubWatch PubMed fetching now parses real `efetch` XML responses (replaces earlier stub/sample paper data).

### Fixed
- OpenPlan integration/test fixes leading to a fully passing test suite.

## 1.1.0 (2026-03-14)

### Added
- `openplan implement` CLI command — runs the full planning-to-implementation pipeline for any OpenPlan project
- `openplan/core/pipeline.py` — `ImplementationPipeline` class with `EpicStatus` enum, `PipelineResult`, and `PipelineError`
- Options: `--project-dir`, `--openspec-dir`, `--model`, `--skip-tests`, `--from-epic`, `--dry-run`
- Epic status tracking throughout pipeline run (`pending` / `in_progress` / `passing` / `failed` / `blocked` / `skipped`)
- 20 new pipeline tests (103 total)

### Changed
- `examples/pubwatch/run_pipeline.py` refactored to thin wrapper over `ImplementationPipeline`

## 1.2.0 (2026-03-16)

### Added
- `openplan archive` CLI command — marks a completed roadmap as done, moves all artifacts to `openplan/archived/<roadmap-id>/`, writes/appends `openplan/HISTORY.md`
- `openplan/core/archive.py` — `ArchiveManager` class with `archive()`, `list_archived()`, history writing
- `get_history()` and `list_archived_roadmaps()` helpers in `engine.py`
- 15 new tests (118 total)

## 1.3.0 (2026-03-16)

### Added
- `openplan gather` CLI command — analyses current codebase + history and synthesises a new vision/roadmap for the next planning cycle
- `openplan/core/gather.py` — `GatherAnalyser` class with `GatherContext` dataclass; analyses src modules, HISTORY.md, openspec changes, design docs, and test shape
- `--dry-run` writes `GATHER.md` analysis only; `--decompose` triggers full epic/feature generation
- 9 new tests (127 total)
