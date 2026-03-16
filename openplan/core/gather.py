"""GatherAnalyser — scans a project directory and produces a GATHER.md context document."""

import subprocess
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class GatherContext:
    existing_modules: list[str] = field(default_factory=list)
    deferred_items: list[str] = field(default_factory=list)
    post_plan_changes: list[str] = field(default_factory=list)
    test_count: int = 0
    design_docs: list[str] = field(default_factory=list)
    prior_roadmap_ids: list[str] = field(default_factory=list)


class GatherAnalyser:
    """Analyses a project directory and gathers context for re-planning."""

    def __init__(self, project_dir: Path, model: Optional[str] = None) -> None:
        self.project_dir = Path(project_dir)
        self.model = model
        self.openplan_dir = self.project_dir / "openplan"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyse(self) -> GatherContext:
        """Gather context from the project directory and return a GatherContext."""
        src_dir = self.project_dir / "src"
        tests_dir = self.project_dir / "tests"

        existing_modules = self._infer_modules(src_dir)
        deferred_items = self._read_history()
        post_plan_changes = self._read_post_plan_changes()
        test_count = self._collect_test_count(tests_dir)

        # Read design docs
        design_dir = self.project_dir / "design"
        design_docs: list[str] = []
        if design_dir.exists():
            design_docs = sorted(
                p.name for p in design_dir.iterdir() if p.suffix.lower() == ".md"
            )

        # Read prior roadmap IDs from openplan/archived/
        prior_roadmap_ids: list[str] = []
        archived_dir = self.openplan_dir / "archived"
        if archived_dir.exists():
            prior_roadmap_ids = sorted(
                p.name for p in archived_dir.iterdir() if p.is_dir()
            )

        return GatherContext(
            existing_modules=existing_modules,
            deferred_items=deferred_items,
            post_plan_changes=post_plan_changes,
            test_count=test_count,
            design_docs=design_docs,
            prior_roadmap_ids=prior_roadmap_ids,
        )

    def write_gather_doc(self, context: GatherContext, gaps: list[str]) -> None:
        """Write openplan/GATHER.md with the gathered context."""
        self.openplan_dir.mkdir(parents=True, exist_ok=True)
        gather_path = self.openplan_dir / "GATHER.md"

        lines = ["# GATHER.md\n\n"]

        lines.append("## What Exists\n\n")
        if context.existing_modules:
            for mod in context.existing_modules:
                lines.append(f"- {mod}\n")
        else:
            lines.append("_(no modules found)_\n")
        lines.append("\n")

        lines.append("## What Was Planned\n\n")
        if context.prior_roadmap_ids:
            for rid in context.prior_roadmap_ids:
                lines.append(f"- {rid}\n")
        else:
            lines.append("_(no prior roadmaps)_\n")
        lines.append("\n")

        lines.append("## What Was Deferred\n\n")
        if context.deferred_items:
            for item in context.deferred_items:
                lines.append(f"- {item}\n")
        else:
            lines.append("_(nothing deferred)_\n")
        lines.append("\n")

        lines.append("## Post-Plan Changes\n\n")
        if context.post_plan_changes:
            for change in context.post_plan_changes:
                lines.append(f"- {change}\n")
        else:
            lines.append("_(no post-plan changes)_\n")
        lines.append("\n")

        lines.append("## Gaps Identified\n\n")
        if gaps:
            for gap in gaps:
                lines.append(f"- {gap}\n")
        else:
            lines.append("_(no gaps identified)_\n")
        lines.append("\n")

        lines.append("## Human Review Required\n\n")
        lines.append(
            "AI-generated content in this document requires human review before acting on it. "
            "Verify module lists, deferred items, and gaps against the actual project state.\n"
        )

        gather_path.write_text("".join(lines))

    def generate(self, context: GatherContext) -> tuple:
        """Generate a new Vision and Roadmap from the gathered context.

        Raises:
            NotImplementedError: Always raised until ACP session wiring is in place.
        """
        raise NotImplementedError(
            "generate() requires an ACP session — use openplan gather with --model"
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _infer_modules(self, src_dir: Path) -> list[str]:
        """List top-level packages (dirs containing __init__.py) in src_dir."""
        if not src_dir.exists():
            warnings.warn(f"Source directory not found: {src_dir}", stacklevel=2)
            return []
        return sorted(
            p.name
            for p in src_dir.iterdir()
            if p.is_dir() and (p / "__init__.py").exists()
        )

    def _read_history(self) -> list[str]:
        """Parse openplan/HISTORY.md for deferred items and Note: lines."""
        history_path = self.openplan_dir / "HISTORY.md"
        if not history_path.exists():
            return []
        lines = history_path.read_text().splitlines()
        deferred: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            lower = stripped.lower()
            if "defer" in lower or stripped.startswith("**Note:**") or stripped.lower().startswith("note:"):
                deferred.append(stripped)
        return deferred

    def _read_post_plan_changes(self) -> list[str]:
        """List dir names in openspec/changes/ excluding 'archive'."""
        changes_dir = self.project_dir / "openspec" / "changes"
        if not changes_dir.exists():
            return []
        return sorted(
            p.name
            for p in changes_dir.iterdir()
            if p.is_dir() and p.name.lower() != "archive"
        )

    def _collect_test_count(self, tests_dir: Path) -> int:
        """Run pytest --collect-only and count test items."""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "--collect-only", "-q"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )
            count = sum(1 for line in result.stdout.splitlines() if "::test_" in line)
            return count
        except Exception as e:
            warnings.warn(f"Could not collect test count: {e}", stacklevel=2)
            return 0
