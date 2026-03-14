from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable
import subprocess
import datetime
import yaml

from openplan.core.schemas import Roadmap, Epic
from openplan.core.ordering import resolve_epic_order


class EpicStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSING = "passing"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class PipelineError(Exception):
    pass


@dataclass
class PipelineResult:
    epic_statuses: dict  # epic_id -> EpicStatus
    features_total: int
    features_implemented: int
    failed_epic: Optional[str] = None


class ImplementationPipeline:
    def __init__(self, project_dir, openspec_dir=None, model=None,
                 skip_tests=False, from_epic=None, acp_client_factory=None):
        self.project_dir = Path(project_dir)
        self.openspec_dir = Path(openspec_dir) if openspec_dir else self.project_dir / "openspec"
        self.model = model
        self.skip_tests = skip_tests
        self.from_epic = from_epic
        self._pytest_output = {}  # epic_id -> (stdout, stderr)
        # Allow injection for testing
        if acp_client_factory is not None:
            self._client_factory = acp_client_factory
        else:
            from openplan.integrations.acp_client import OpenCodeClient
            self._client_factory = OpenCodeClient

    def run(self, roadmap) -> PipelineResult:
        ordered = resolve_epic_order(roadmap.epics)
        epic_statuses = {e.id: EpicStatus.PENDING for e in ordered}
        features_total = 0
        features_implemented = 0
        failed_epic = None
        reached_from = self.from_epic is None

        for epic in ordered:
            if not reached_from:
                if epic.id == self.from_epic:
                    reached_from = True
                else:
                    epic_statuses[epic.id] = EpicStatus.SKIPPED
                    continue

            epic_statuses[epic.id] = EpicStatus.IN_PROGRESS
            features = self._discover_features(epic.id)
            features_total += len(features)

            for feature_id in features:
                with self._client_factory(project_dir=str(self.project_dir), model=self.model) as client:
                    client.generate(f"/opsx-ff {feature_id}")
                    client.generate(f"/opsx-apply {feature_id}")
                features_implemented += 1

            if not self.skip_tests:
                passed, stdout, stderr = self._run_pytest()
                self._pytest_output[epic.id] = (stdout, stderr)
                if not passed:
                    epic_statuses[epic.id] = EpicStatus.FAILED
                    failed_epic = epic.id
                    self._propagate_blocked(epic.id, epic_statuses, ordered)
                    result = PipelineResult(
                        epic_statuses=epic_statuses,
                        features_total=features_total,
                        features_implemented=features_implemented,
                        failed_epic=failed_epic,
                    )
                    self._write_report(result, roadmap)
                    raise PipelineError(f"Epic '{epic.id}' failed pytest gate.\n{stderr}")
            epic_statuses[epic.id] = EpicStatus.PASSING

        result = PipelineResult(
            epic_statuses=epic_statuses,
            features_total=features_total,
            features_implemented=features_implemented,
            failed_epic=failed_epic,
        )
        self._write_report(result, roadmap)
        return result

    def dry_run(self, roadmap) -> None:
        from rich.console import Console
        from rich.table import Table
        console = Console()
        ordered = resolve_epic_order(roadmap.epics)
        console.print("[bold cyan]OpenPlan Implement — Dry Run[/bold cyan]")
        console.print(f"Project: {self.project_dir}")
        console.print(f"Epics in resolved order ({len(ordered)}):")
        for i, epic in enumerate(ordered, 1):
            deps = f" (depends on: {', '.join(epic.depends_on)})" if epic.depends_on else ""
            features = self._discover_features(epic.id)
            console.print(f"  {i}. [bold]{epic.id}[/bold] — {epic.title}{deps}")
            for f in features:
                console.print(f"       • {f}")
        console.print("\n[yellow]Dry run — no code will be executed.[/yellow]")

    def _discover_features(self, epic_id: str) -> list:
        pattern = f"openplan/features/{epic_id}-*.yaml"
        return sorted(
            p.stem for p in self.project_dir.glob(pattern)
        )

    def _run_pytest(self):
        result = subprocess.run(
            ["python", "-m", "pytest"],
            cwd=str(self.project_dir),
            capture_output=True,
            text=True,
        )
        passed = result.returncode in (0, 5)
        return passed, result.stdout, result.stderr

    def _propagate_blocked(self, failed_id: str, epic_statuses: dict, ordered: list):
        dependents = set()
        def collect(eid):
            for epic in ordered:
                if eid in epic.depends_on and epic.id not in dependents:
                    dependents.add(epic.id)
                    collect(epic.id)
        collect(failed_id)
        for eid in dependents:
            epic_statuses[eid] = EpicStatus.BLOCKED

    def _write_report(self, result: PipelineResult, roadmap) -> None:
        report_dir = self.project_dir / "openplan"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "implementation_report.md"
        ts = datetime.datetime.now().isoformat(timespec="seconds")
        lines = [
            f"# OpenPlan Implementation Report",
            f"",
            f"**Generated:** {ts}  ",
            f"**Project:** {self.project_dir}  ",
            f"**Roadmap:** {roadmap.id} — {roadmap.title}  ",
            f"**Features:** {result.features_implemented}/{result.features_total} implemented  ",
            f"",
            f"## Epic Status",
            f"",
            f"| Epic | Status | Features |",
            f"|------|--------|----------|",
        ]
        for epic in roadmap.epics:
            status = result.epic_statuses.get(epic.id, EpicStatus.PENDING)
            features = self._discover_features(epic.id)
            lines.append(f"| {epic.id} | {status.value} | {len(features)} |")

        if result.failed_epic:
            lines += ["", f"## Failure: {result.failed_epic}", ""]
            stdout, stderr = self._pytest_output.get(result.failed_epic, ("", ""))
            if stderr:
                lines += ["```", stderr[:2000], "```"]

        report_path.write_text("\n".join(lines) + "\n")
