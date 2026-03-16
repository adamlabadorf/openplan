# Spec: archive-manager

## ADDED

### R1 — `ArchiveManager` class
A class `ArchiveManager` MUST exist in `openplan/core/archive.py`.
Constructor: `ArchiveManager(project_dir: Path)`.

### R2 — `archive(roadmap_id, note)` method
`ArchiveManager.archive(roadmap_id: str, note: str = "")` MUST:
1. Create `openplan/archived/<roadmap-id>/`
2. Move `openplan/roadmaps/<roadmap-id>.yaml` into it
3. Move all `openplan/epics/epic-*.yaml` files into it
4. Move all `openplan/features/epic-*-feature-*.yaml` files into it
5. Move the vision YAML referenced by the roadmap into it
6. Move `openplan/implementation_report.md` into it if it exists

### R3 — `ArchiveManager` does not delete, only moves
All operations MUST use `shutil.move` (or equivalent). No files are deleted.

### R4 — Idempotency guard
If `openplan/archived/<roadmap-id>/` already exists,
`archive()` MUST raise `ArchiveError` rather than overwriting.

### R5 — `list_archived()` method
`ArchiveManager.list_archived() -> list[str]` MUST return a sorted list of
archived roadmap IDs (directory names under `openplan/archived/`).

#### Scenario: successful archive
Given a project with roadmap, epics, features, and implementation_report.md,
When `ArchiveManager.archive("road-map-001")` is called,
Then all artifacts are in `openplan/archived/road-map-001/` and
`openplan/roadmaps/` is empty.

#### Scenario: idempotency guard
Given `openplan/archived/road-map-001/` already exists,
When `ArchiveManager.archive("road-map-001")` is called again,
Then `ArchiveError` is raised.
