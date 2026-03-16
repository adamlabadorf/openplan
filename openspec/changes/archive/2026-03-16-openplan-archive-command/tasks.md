# Tasks: `openplan archive`

## openplan/core/archive.py (new file)

- [ ] Create `openplan/core/archive.py`
- [ ] Define `ArchiveError(Exception)` with a `message` attribute
- [ ] Define `ArchiveManager(project_dir: Path)` class
- [ ] Implement `archive(roadmap_id: str, note: str = "") -> None`:
  - [ ] Resolve roadmap YAML path; raise `ArchiveError` if not found
  - [ ] Raise `ArchiveError` if `openplan/archived/<roadmap-id>/` already exists
  - [ ] Create `openplan/archived/<roadmap-id>/` directory
  - [ ] Move `openplan/roadmaps/<roadmap-id>.yaml` into archive dir
  - [ ] Move all `openplan/epics/epic-*.yaml` files into archive dir
  - [ ] Move all `openplan/features/epic-*-feature-*.yaml` files into archive dir
  - [ ] Resolve vision YAML from roadmap `vision_id` field and move it
  - [ ] Move `openplan/implementation_report.md` if it exists
  - [ ] Call `_write_history(roadmap_id, roadmap_data, note)`
- [ ] Implement `list_archived() -> list[str]`: return sorted list of dir names under `openplan/archived/`
- [ ] Implement `_write_history(roadmap_id, roadmap_data, note)`: prepend entry to `openplan/HISTORY.md`
- [ ] Implement `_parse_implementation_report() -> dict`: best-effort parse of `implementation_report.md`; return `{}` if absent or unparseable

## openplan/cli/main.py

- [ ] Add `archive` command with options: `--roadmap-id`, `--note`, `--project-dir`, `--force`, `--dry-run`
- [ ] Auto-detect single roadmap when `--roadmap-id` is omitted; error on zero or multiple
- [ ] Check for `implementation_report.md`; warn and exit non-zero if missing and `--force` not set
- [ ] Instantiate `ArchiveManager` and call `.archive()`
- [ ] Print confirmation summary on success (roadmap ID, artifacts moved, HISTORY.md updated)

## openplan/core/engine.py

- [ ] Add `get_history(project_dir: Path) -> list[dict]` helper that reads `openplan/HISTORY.md` and returns structured entries (keys: `roadmap_id`, `title`, `date`, `epics`, `features`, `note`)
- [ ] Add `list_archived_roadmaps(project_dir: Path) -> list[str]` that delegates to `ArchiveManager.list_archived()`

## tests/test_archive.py (new file)

- [ ] Create `tests/test_archive.py`
- [ ] Fixture: `archive_project_dir` — tmp_path with full artifact tree (roadmap, epics, features, vision, implementation_report.md)
- [ ] Test: `ArchiveManager.archive()` moves all artifacts to `archived/<roadmap-id>/`
- [ ] Test: `openplan/roadmaps/` is empty after archive
- [ ] Test: `HISTORY.md` is created with correct entry
- [ ] Test: `HISTORY.md` is appended on second archive call
- [ ] Test: `--note` content appears in `HISTORY.md`
- [ ] Test: `ArchiveError` raised when archive dir already exists
- [ ] Test: `list_archived()` returns correct sorted list
- [ ] Test: CLI `--force` bypasses `implementation_report.md` guard
- [ ] Test: CLI exits non-zero when no `implementation_report.md` and no `--force`
