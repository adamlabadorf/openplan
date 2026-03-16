# Proposal: `openplan gather` — Reverse-Engineering a New Plan from Current Codebase

## Why

After `openplan archive` marks a completed cycle, the next planning iteration
requires reconstructing current state: what was implemented, what was deferred,
what emerged from post-plan development. There is no automated way to do this
today — users must manually write a new vision and roadmap from scratch.

`openplan gather` is the inverse of `openplan implement`: it analyses the
existing codebase + history and synthesises a new vision and roadmap ready for
the next cycle.

## What Changes

- New CLI command `openplan gather` in `openplan/cli/main.py`
- New `openplan/core/gather.py` — `GatherAnalyser` class: codebase analysis,
  gap synthesis, artifact generation
- `tests/test_gather.py` (new) — unit tests for `GatherAnalyser` with fixture
  project dirs

## Capabilities

- gather-command
- gather-analyser
- gap-synthesis

## CLI Signature

```
openplan gather [OPTIONS]

Options:
  --project-dir PATH     Project root (default: .)
  --design-dir PATH      Design docs directory (default: ./design)
  --src-dir PATH         Source directory to analyse (default: ./src)
  --tests-dir PATH       Test directory (default: ./tests)
  --model TEXT           Model for AI generation
  --output-vision TEXT   Vision ID to create (default: <project>-vision-v2)
  --decompose            Also generate epics and features from new roadmap
  --dry-run              Write GATHER.md analysis only, no vision/roadmap files
```

## What `gather` Does

1. **Analyse current state:**
   - Reads design docs (`design/`) for intended architecture
   - Reads `openplan/HISTORY.md` for previously planned/deferred items
   - Scans `src/` module structure to infer what currently exists
   - Reads `openspec/changes/` for post-initial-implementation additions
   - Runs `pytest --collect-only` for test coverage shape
2. **Synthesise a gap analysis:** what exists, what was deferred, what's
   emerged from post-plan development
3. **Generate new planning artifacts:**
   - `openplan/visions/<vision-id>.yaml`
   - `openplan/roadmaps/<roadmap-id>.yaml`
   - Optionally decompose into epics/features (`--decompose`)
4. **Write `openplan/GATHER.md`** — human-readable gap analysis for review
   before proceeding

## Affected Files

- `openplan/cli/main.py`
- `openplan/core/gather.py` (new)
- `tests/test_gather.py` (new)
