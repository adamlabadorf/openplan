# Spec: history-tracking

## ADDED

### R1 — `HISTORY.md` file
After `ArchiveManager.archive()` completes, `openplan/HISTORY.md` MUST be
created (if absent) or appended to with an entry for the archived roadmap.

### R2 — Entry format
Each entry MUST include:
- Roadmap ID and title
- Archive date (ISO-8601)
- Epic count and status summary (from `implementation_report.md` if present)
- Feature count
- Optional note (from `--note`)

Example:
```markdown
## road-map-001 — My Project v0.1 (archived 2026-03-16)
**Epics:** 3 (all passing)
**Features:** 14/14
**Note:** Auth deferred to v0.2.
```

### R3 — Append-only
`HISTORY.md` MUST never be overwritten; new entries MUST be prepended (newest
first) or appended (oldest first — either is acceptable, but consistent).

### R4 — `engine.get_history()` helper
`PlanningEngine` (or a standalone helper in `archive.py`) MUST expose
`get_history(project_dir) -> list[dict]` that parses `HISTORY.md` and returns
structured dicts with keys `roadmap_id`, `title`, `date`, `epics`, `features`,
`note`.

#### Scenario: first archive
Given no `HISTORY.md` exists,
When `ArchiveManager.archive("road-map-001", note="Auth deferred")` runs,
Then `HISTORY.md` is created with one entry containing the note.

#### Scenario: second archive appends
Given `HISTORY.md` already contains one entry,
When a second roadmap is archived,
Then `HISTORY.md` contains two entries and the original is unchanged.
