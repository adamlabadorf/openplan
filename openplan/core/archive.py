"""ArchiveManager — moves completed roadmap artifacts into openplan/archived/."""

import shutil
from datetime import date
from pathlib import Path
from typing import Optional


class ArchiveError(Exception):
    """Raised when an archive operation fails."""


class ArchiveManager:
    """Manages archival of completed roadmap artifacts."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = Path(project_dir)
        self.openplan_dir = self.project_dir / "openplan"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def archive(self, roadmap_id: str, note: str = "") -> None:
        """Move all artifacts for *roadmap_id* into openplan/archived/<roadmap-id>/.

        Moves:
        - openplan/roadmaps/<roadmap-id>.yaml
        - openplan/epics/epic-*.yaml
        - openplan/features/epic-*-feature-*.yaml
        - vision YAML (resolved from roadmap's vision_id field)
        - openplan/implementation_report.md  (if present)

        Raises:
            ArchiveError: if the archive destination already exists.
        """
        import yaml

        roadmap_path = self.openplan_dir / "roadmaps" / f"{roadmap_id}.yaml"
        if not roadmap_path.exists():
            raise ArchiveError(f"Roadmap file not found: {roadmap_path}")

        with open(roadmap_path) as f:
            roadmap_data = yaml.safe_load(f) or {}

        dest = self.openplan_dir / "archived" / roadmap_id
        if dest.exists():
            raise ArchiveError(
                f"Archive destination already exists: {dest}. "
                "Remove or rename it before archiving again."
            )
        dest.mkdir(parents=True, exist_ok=False)

        # Collect files to move
        files_to_move: list[Path] = []

        # 1. Roadmap itself
        files_to_move.append(roadmap_path)

        # 2. Epics
        epics_dir = self.openplan_dir / "epics"
        if epics_dir.exists():
            files_to_move.extend(sorted(epics_dir.glob("epic-*.yaml")))

        # 3. Features
        features_dir = self.openplan_dir / "features"
        if features_dir.exists():
            files_to_move.extend(sorted(features_dir.glob("epic-*-feature-*.yaml")))

        # 4. Vision YAML (resolved from roadmap vision_id)
        vision_id = roadmap_data.get("vision_id")
        if vision_id:
            vision_path = self.openplan_dir / "visions" / f"{vision_id}.yaml"
            if vision_path.exists():
                files_to_move.append(vision_path)

        # 5. implementation_report.md (optional)
        impl_report = self.openplan_dir / "implementation_report.md"
        if impl_report.exists():
            files_to_move.append(impl_report)

        # Move everything
        for src in files_to_move:
            shutil.move(str(src), str(dest / src.name))

        # Write HISTORY.md entry
        self._write_history(roadmap_id, roadmap_data, note)

    def list_archived(self) -> list[str]:
        """Return sorted list of directory names under openplan/archived/."""
        archived_dir = self.openplan_dir / "archived"
        if not archived_dir.exists():
            return []
        return sorted(p.name for p in archived_dir.iterdir() if p.is_dir())

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _write_history(self, roadmap_id: str, roadmap_data: dict, note: str) -> None:
        """Prepend a HISTORY.md entry for *roadmap_id*."""
        title = roadmap_data.get("title", roadmap_id)
        today = date.today().isoformat()

        # Count epics and features from roadmap_data
        epics = roadmap_data.get("epics", []) or []
        epic_count = len(epics)

        # Count features from archived dir
        archived_features_dir = self.openplan_dir / "archived" / roadmap_id
        feature_count = len(list(archived_features_dir.glob("epic-*-feature-*.yaml"))) if archived_features_dir.exists() else 0

        lines = [
            f"## {roadmap_id} — {title} (archived {today})\n",
            f"**Epics:** {epic_count}  \n",
            f"**Features:** {feature_count}  \n",
        ]
        if note:
            lines.append(f"**Note:** {note}  \n")
        lines.append("\n")

        entry = "".join(lines)

        history_path = self.openplan_dir / "HISTORY.md"
        if history_path.exists():
            existing = history_path.read_text()
            history_path.write_text(entry + existing)
        else:
            history_path.write_text(entry)

    def _parse_implementation_report(self) -> dict:
        """Parse openplan/implementation_report.md into a summary dict.

        Returns a dict with whatever metadata can be extracted (best-effort).
        """
        impl_report = self.openplan_dir / "implementation_report.md"
        if not impl_report.exists():
            return {}
        content = impl_report.read_text()
        return {"content": content, "exists": True}
