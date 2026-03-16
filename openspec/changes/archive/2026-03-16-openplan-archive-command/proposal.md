# Proposal: `openplan archive` — Plan Lifecycle Completion

## Why

Once `openplan implement` completes and normal development begins, the OpenPlan
artifacts become stale archaeology: epics and features describe intent, not
reality. Running `openplan implement` again would be destructive. There is no
record of what was delivered vs. deferred, and starting a v2 planning cycle
requires manually reconstructing what v1 delivered.

The OpenSpec `archive` command is the right model: completed work gets marked,
moved out of the active workspace, and leaves a clean state for the next cycle.

## What Changes

- New CLI command `openplan archive` in `openplan/cli/main.py`
- New `openplan/core/archive.py` — `ArchiveManager` class: moves artifacts,
  writes/appends `HISTORY.md`
- `openplan/core/engine.py` — add `list_archived_roadmaps()` and
  `get_history()` helpers
- `tests/test_archive.py` (new) — unit tests for `ArchiveManager`

## Capabilities

- archive-command
- archive-manager
- history-tracking

## CLI Signature

```
openplan archive [OPTIONS]

Options:
  --roadmap-id TEXT    Roadmap to archive (default: only roadmap in roadmaps/)
  --note TEXT          Optional summary note to include in HISTORY.md
  --project-dir PATH   Project root (default: .)
  --force              Archive even if implementation_report.md is absent
```

## Affected Files

- `openplan/cli/main.py`
- `openplan/core/archive.py` (new)
- `openplan/core/engine.py`
- `tests/test_archive.py` (new)
