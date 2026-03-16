# Spec: archive-command

## ADDED

### R1 — `openplan archive` CLI command
A new `archive` command MUST be added to `openplan/cli/main.py`.

### R2 — Options
The command MUST accept:
- `--roadmap-id TEXT` (default: auto-detect single roadmap in `openplan/roadmaps/`)
- `--note TEXT` (optional, included in `HISTORY.md` entry)
- `--project-dir PATH` (default: `.`)
- `--force` (skip implementation report check)

### R3 — Auto-detect roadmap
If `--roadmap-id` is not provided and exactly one roadmap YAML exists in
`openplan/roadmaps/`, it MUST be selected automatically.
If zero or multiple roadmaps exist and no `--roadmap-id` is given, the command
MUST exit with a clear error.

### R4 — implementation_report.md guard
If `openplan/implementation_report.md` does not exist and `--force` is not
passed, the command MUST warn and exit with a non-zero code.

### R5 — Dry-run output
When `--dry-run` is passed, the command MUST print what would be moved/written
without making any filesystem changes.

#### Scenario: auto-detect single roadmap
Given one roadmap YAML exists and no `--roadmap-id` is given,
When `openplan archive` runs,
Then the single roadmap is selected and archived without error.

#### Scenario: missing implementation report
Given no `implementation_report.md` exists and `--force` is not passed,
When `openplan archive` runs,
Then the command exits non-zero with a message mentioning `openplan implement`.

#### Scenario: --force bypasses guard
Given no `implementation_report.md` exists and `--force` is passed,
When `openplan archive` runs,
Then archiving proceeds without error.
