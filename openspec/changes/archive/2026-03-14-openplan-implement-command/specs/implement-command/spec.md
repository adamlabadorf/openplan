# Spec: `openplan implement` CLI Command

## ADDED
- `implement` command in `openplan/cli/main.py`

## Requirements

### R1 — Command exists
`openplan implement --help` MUST print usage without error.

### R2 — Options
The command MUST accept:
- `--project-dir PATH` — project root (default: current working directory)
- `--openspec-dir PATH` — OpenSpec changes directory (default: `<project-dir>/openspec`)
- `--model TEXT` — model string passed to ACPClient (default: from `opencode.json` or None)
- `--skip-tests` — boolean flag; when set, skip pytest gate between epics
- `--from-epic TEXT` — start from this epic ID; earlier epics are marked `skipped`
- `--dry-run` — print execution plan without opening any ACP sessions or running pytest

### R3 — Dry-run output
When `--dry-run` is set, the command MUST print:
- The resolved epic order (with dependency arrows)
- All features per epic
- A note that no code will be executed

### R4 — Implementation report
After the pipeline completes (pass or fail), the command MUST write
`<project-dir>/openplan/implementation_report.md` containing:
- Run timestamp
- Per-epic status, feature count, and pytest result summary
- Total features implemented vs. total features

### R5 — Exit code
The command MUST exit with code 0 if all epics reach `passing` status.
It MUST exit with a non-zero code if any epic is `failed` or `blocked`.

### R6 — Rich output
The command SHOULD use `rich` to display a live status table or progress
log during execution (consistent with other openplan CLI output).

## Scenarios

### Scenario A — Dry run
Given a valid project, when `--dry-run` is passed,
Then resolved epic order and features are printed, no ACPClient is opened,
and no pytest is run.

### Scenario B — Normal run, all pass
Given all feature OpenSpec changes exist and pytest passes for all epics,
When `openplan implement` runs,
Then all epics reach `passing`, report is written, exit code 0.

### Scenario C — `--from-epic`
Given `--from-epic epic-002` is passed,
When the pipeline runs,
Then epic-001 is marked `skipped` and implementation starts at epic-002.

### Scenario D — `--skip-tests`
Given `--skip-tests` is passed,
When the pipeline runs,
Then no pytest is invoked and all implemented epics are marked `passing`.
