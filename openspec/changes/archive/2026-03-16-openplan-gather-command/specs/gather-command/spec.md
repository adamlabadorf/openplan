# Spec: gather-command

## ADDED

### R1 — `openplan gather` CLI command
A new `gather` command MUST be added to `openplan/cli/main.py`.

### R2 — Options
The command MUST accept:
- `--project-dir PATH` (default: `.`)
- `--design-dir PATH` (default: `./design`)
- `--src-dir PATH` (default: `./src`)
- `--tests-dir PATH` (default: `./tests`)
- `--model TEXT` (model for AI generation)
- `--output-vision TEXT` (vision ID; default: `<project-name>-vision-v2`)
- `--decompose` (also generate epics and features)
- `--dry-run` (write `GATHER.md` only, no vision/roadmap files)

### R3 — `GATHER.md` always written
Whether `--dry-run` or not, `openplan/GATHER.md` MUST be written with the
gap analysis (what exists, what was deferred, what emerged).

### R4 — `--dry-run` writes analysis only
When `--dry-run` is passed, `GATHER.md` is written but no vision or roadmap
YAML files are created.

### R5 — `--decompose` triggers full decomposition
When `--decompose` is passed, after writing vision and roadmap, the command
MUST also call epic decomposition and feature stabilization (equivalent to
`openplan decompose-epic` for each epic in the new roadmap).

#### Scenario: dry-run
Given `--dry-run` is passed,
When `openplan gather` runs,
Then `GATHER.md` is written and no vision/roadmap YAMLs are created.

#### Scenario: normal run
Given `--dry-run` is not passed,
When `openplan gather` runs,
Then `GATHER.md`, vision YAML, and roadmap YAML are all written.

#### Scenario: --decompose
Given `--decompose` is passed,
When `openplan gather` runs,
Then vision, roadmap, epics, and features are all generated.
