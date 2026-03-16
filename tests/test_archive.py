"""Tests for openplan.core.archive (ArchiveManager) and the CLI archive command."""

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from openplan.cli.main import app
from openplan.core.archive import ArchiveError, ArchiveManager
from openplan.core.engine import get_history, list_archived_roadmaps


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_project(tmp_path: Path, roadmap_id: str = "road-map-001", with_report: bool = True) -> Path:
    """Build a minimal fake OpenPlan project tree under *tmp_path*."""
    openplan = tmp_path / "openplan"

    # Roadmap
    roadmaps_dir = openplan / "roadmaps"
    roadmaps_dir.mkdir(parents=True)
    roadmap_data = {
        "id": roadmap_id,
        "title": "Test Project",
        "vision_id": "vision-001",
        "epics": [
            {"id": "epic-001", "title": "Core Epic", "description": "First epic"},
        ],
    }
    (roadmaps_dir / f"{roadmap_id}.yaml").write_text(yaml.dump(roadmap_data))

    # Epic
    epics_dir = openplan / "epics"
    epics_dir.mkdir(parents=True)
    (epics_dir / "epic-001.yaml").write_text(
        yaml.dump({"id": "epic-001", "title": "Core Epic", "description": "desc"})
    )

    # Feature
    features_dir = openplan / "features"
    features_dir.mkdir(parents=True)
    (features_dir / "epic-001-feature-001.yaml").write_text(
        yaml.dump({"id": "epic-001-feature-001", "title": "Feature One"})
    )

    # Vision
    visions_dir = openplan / "visions"
    visions_dir.mkdir(parents=True)
    (visions_dir / "vision-001.yaml").write_text(
        yaml.dump({"id": "vision-001", "title": "Vision One"})
    )

    # Implementation report (optional)
    if with_report:
        (openplan / "implementation_report.md").write_text("# Implementation Report\nAll done.")

    return tmp_path


# ---------------------------------------------------------------------------
# ArchiveManager unit tests
# ---------------------------------------------------------------------------

class TestArchiveManager:
    def test_archive_moves_all_artifacts(self, tmp_path):
        project = make_project(tmp_path)
        manager = ArchiveManager(project)
        manager.archive("road-map-001")

        dest = project / "openplan" / "archived" / "road-map-001"
        assert dest.is_dir()
        assert (dest / "road-map-001.yaml").exists(), "roadmap not archived"
        assert (dest / "epic-001.yaml").exists(), "epic not archived"
        assert (dest / "epic-001-feature-001.yaml").exists(), "feature not archived"
        assert (dest / "vision-001.yaml").exists(), "vision not archived"
        assert (dest / "implementation_report.md").exists(), "report not archived"

    def test_roadmaps_dir_empty_after_archive(self, tmp_path):
        project = make_project(tmp_path)
        manager = ArchiveManager(project)
        manager.archive("road-map-001")

        roadmap_files = list((project / "openplan" / "roadmaps").glob("*.yaml"))
        assert roadmap_files == [], "roadmaps/ should be empty after archive"

    def test_history_created_with_correct_entry(self, tmp_path):
        project = make_project(tmp_path)
        manager = ArchiveManager(project)
        manager.archive("road-map-001")

        history = project / "openplan" / "HISTORY.md"
        assert history.exists(), "HISTORY.md should be created"
        content = history.read_text()
        assert "road-map-001" in content
        assert "Test Project" in content

    def test_history_prepended_on_second_archive(self, tmp_path):
        """After two archives the file should have two entries, newer first."""
        project = make_project(tmp_path)
        manager = ArchiveManager(project)
        manager.archive("road-map-001")

        # Create a second roadmap for the second archive
        second_id = "road-map-002"
        roadmaps_dir = project / "openplan" / "roadmaps"
        roadmap_data2 = {
            "id": second_id,
            "title": "Second Project",
            "vision_id": "vision-002",
            "epics": [],
        }
        (roadmaps_dir / f"{second_id}.yaml").write_text(yaml.dump(roadmap_data2))
        visions_dir = project / "openplan" / "visions"
        (visions_dir / "vision-002.yaml").write_text(
            yaml.dump({"id": "vision-002", "title": "Vision Two"})
        )
        # recreate implementation_report for second archive
        (project / "openplan" / "implementation_report.md").write_text("done again")

        manager.archive(second_id)

        content = (project / "openplan" / "HISTORY.md").read_text()
        pos1 = content.find("road-map-001")
        pos2 = content.find("road-map-002")
        assert pos1 != -1 and pos2 != -1, "Both entries should be present"
        assert pos2 < pos1, "Newer entry (road-map-002) should appear first"

    def test_note_appears_in_history(self, tmp_path):
        project = make_project(tmp_path)
        manager = ArchiveManager(project)
        manager.archive("road-map-001", note="shipped to production")

        content = (project / "openplan" / "HISTORY.md").read_text()
        assert "shipped to production" in content

    def test_archive_error_if_dest_exists(self, tmp_path):
        project = make_project(tmp_path)
        dest = project / "openplan" / "archived" / "road-map-001"
        dest.mkdir(parents=True)

        manager = ArchiveManager(project)
        with pytest.raises(ArchiveError):
            manager.archive("road-map-001")

    def test_list_archived_returns_sorted(self, tmp_path):
        project = make_project(tmp_path)
        archived = project / "openplan" / "archived"
        archived.mkdir(parents=True)
        (archived / "zebra-roadmap").mkdir()
        (archived / "alpha-roadmap").mkdir()
        (archived / "beta-roadmap").mkdir()

        manager = ArchiveManager(project)
        result = manager.list_archived()
        assert result == ["alpha-roadmap", "beta-roadmap", "zebra-roadmap"]


# ---------------------------------------------------------------------------
# Engine helper tests
# ---------------------------------------------------------------------------

class TestEngineHelpers:
    def test_get_history_returns_entries(self, tmp_path):
        project = make_project(tmp_path)
        manager = ArchiveManager(project)
        manager.archive("road-map-001", note="my note")

        entries = get_history(project)
        assert len(entries) == 1
        e = entries[0]
        assert e["roadmap_id"] == "road-map-001"
        assert e["title"] == "Test Project"
        assert e["note"] == "my note"
        import re
        assert re.match(r"\d{4}-\d{2}-\d{2}", e["date"])

    def test_get_history_empty_when_no_file(self, tmp_path):
        project = make_project(tmp_path)
        assert get_history(project) == []

    def test_list_archived_roadmaps_delegates(self, tmp_path):
        project = make_project(tmp_path)
        manager = ArchiveManager(project)
        manager.archive("road-map-001")

        result = list_archived_roadmaps(project)
        assert "road-map-001" in result


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------

runner = CliRunner()


class TestArchiveCLI:
    def test_cli_force_bypasses_missing_report(self, tmp_path):
        project = make_project(tmp_path, with_report=False)
        result = runner.invoke(
            app,
            ["archive", "--project-dir", str(project), "--force"],
        )
        assert result.exit_code == 0, result.output
        assert (project / "openplan" / "archived" / "road-map-001").exists()

    def test_cli_exits_nonzero_without_report_and_no_force(self, tmp_path):
        project = make_project(tmp_path, with_report=False)
        result = runner.invoke(
            app,
            ["archive", "--project-dir", str(project)],
        )
        assert result.exit_code != 0

    def test_cli_dry_run_does_not_move_files(self, tmp_path):
        project = make_project(tmp_path)
        result = runner.invoke(
            app,
            ["archive", "--project-dir", str(project), "--dry-run"],
        )
        assert result.exit_code == 0, result.output
        # Files should still be in place
        assert (project / "openplan" / "roadmaps" / "road-map-001.yaml").exists()
        assert not (project / "openplan" / "archived" / "road-map-001").exists()

    def test_cli_archive_with_note(self, tmp_path):
        project = make_project(tmp_path)
        result = runner.invoke(
            app,
            ["archive", "--project-dir", str(project), "--note", "all tests green"],
        )
        assert result.exit_code == 0, result.output
        content = (project / "openplan" / "HISTORY.md").read_text()
        assert "all tests green" in content

    def test_cli_multiple_roadmaps_requires_id(self, tmp_path):
        project = make_project(tmp_path)
        # Add a second roadmap
        roadmaps_dir = project / "openplan" / "roadmaps"
        (roadmaps_dir / "road-map-002.yaml").write_text(
            yaml.dump({"id": "road-map-002", "title": "Second", "vision_id": "v2", "epics": []})
        )
        result = runner.invoke(
            app,
            ["archive", "--project-dir", str(project), "--force"],
        )
        assert result.exit_code != 0
        assert "Multiple roadmaps" in result.output or "roadmap-id" in result.output.lower()
