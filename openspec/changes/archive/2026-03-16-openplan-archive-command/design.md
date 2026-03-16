# Design: `openplan archive`

## Decisions

### D1 — `ArchiveManager` is a plain class, not part of `PlanningEngine`
`PlanningEngine` generates planning artifacts; `ArchiveManager` manipulates
the filesystem. Keeping them separate maintains single responsibility and makes
`ArchiveManager` independently testable without an ACP client.

### D2 — Move, never delete
All artifact moves use `shutil.move`. This is safe on both same-filesystem
(rename) and cross-filesystem (copy+delete) scenarios. Destructive ops are
explicitly out of scope for 1.x.

### D3 — `ArchiveError` is a new exception in `archive.py`
Rather than reusing `PlanningError` (which carries `validation_errors`), a
simple `ArchiveError(message)` is cleaner for filesystem/state errors.

### D4 — Vision YAML is found via roadmap `vision_id` field
The roadmap YAML contains `vision_id`; `ArchiveManager` resolves
`openplan/visions/<vision_id>.yaml` from it. No glob needed.

### D5 — `HISTORY.md` entries are prepended (newest first)
Matches convention of changelogs and git logs. Implementation reads existing
content, prepends new entry, rewrites file.

### D6 — Typer for CLI, consistent with existing commands
The `archive` command follows the same Typer pattern as `implement`.
Options use `typer.Option` with `Path` type for directory arguments.

## Module Layout

```
openplan/core/archive.py
  ArchiveError(Exception)
  ArchiveManager
    __init__(project_dir: Path)
    archive(roadmap_id: str, note: str = "") -> None
    list_archived() -> list[str]
    _write_history(roadmap_id, roadmap, note) -> None
    _parse_implementation_report() -> dict   # best-effort, returns {} if absent
```

```
openplan/cli/main.py
  @app.command()
  def archive(
      roadmap_id: Optional[str] = ...,
      note: str = ...,
      project_dir: Path = ...,
      force: bool = ...,
  )
```
