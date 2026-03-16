"""Tests for GatherAnalyser and the gather CLI command."""

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from openplan.cli.main import app
from openplan.core.gather import GatherAnalyser, GatherContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_project(tmp_path: Path) -> Path:
    """Create a minimal fake project tree."""
    (tmp_path / "openplan").mkdir()
    (tmp_path / "openspec" / "changes").mkdir(parents=True)
    return tmp_path


# ---------------------------------------------------------------------------
# _infer_modules
# ---------------------------------------------------------------------------

def test_infer_modules_returns_packages(tmp_path: Path) -> None:
    """_infer_modules returns dirs that contain __init__.py."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "alpha").mkdir()
    (src / "alpha" / "__init__.py").write_text("")
    (src / "beta").mkdir()
    (src / "beta" / "__init__.py").write_text("")
    (src / "not_a_package").mkdir()  # no __init__.py

    analyser = GatherAnalyser(tmp_path)
    result = analyser._infer_modules(src)
    assert result == ["alpha", "beta"]


def test_infer_modules_absent_src(tmp_path: Path) -> None:
    """_infer_modules returns [] without error when src_dir does not exist."""
    analyser = GatherAnalyser(tmp_path)
    result = analyser._infer_modules(tmp_path / "nonexistent_src")
    assert result == []


# ---------------------------------------------------------------------------
# _read_history
# ---------------------------------------------------------------------------

def test_read_history_note_lines(tmp_path: Path) -> None:
    """_read_history returns lines that start with Note: or contain defer."""
    (tmp_path / "openplan").mkdir()
    history = tmp_path / "openplan" / "HISTORY.md"
    history.write_text(
        "## roadmap-1 — My Project (archived 2025-01-01)\n"
        "**Epics:** 3  \n"
        "**Note:** Deferred the auth module to next cycle  \n"
        "Some normal line\n"
        "We should defer the analytics feature\n"
    )
    analyser = GatherAnalyser(tmp_path)
    result = analyser._read_history()
    assert any("Note:" in item or "defer" in item.lower() for item in result)
    assert len(result) >= 2


def test_read_history_absent(tmp_path: Path) -> None:
    """_read_history returns [] when HISTORY.md does not exist."""
    (tmp_path / "openplan").mkdir()
    analyser = GatherAnalyser(tmp_path)
    assert analyser._read_history() == []


# ---------------------------------------------------------------------------
# _read_post_plan_changes
# ---------------------------------------------------------------------------

def test_read_post_plan_changes_excludes_archive(tmp_path: Path) -> None:
    """_read_post_plan_changes lists change dirs and excludes 'archive'."""
    changes = tmp_path / "openspec" / "changes"
    changes.mkdir(parents=True)
    (changes / "feature-a").mkdir()
    (changes / "feature-b").mkdir()
    (changes / "archive").mkdir()  # should be excluded

    analyser = GatherAnalyser(tmp_path)
    result = analyser._read_post_plan_changes()
    assert "archive" not in result
    assert "feature-a" in result
    assert "feature-b" in result


def test_read_post_plan_changes_absent(tmp_path: Path) -> None:
    """_read_post_plan_changes returns [] when openspec/changes/ does not exist."""
    analyser = GatherAnalyser(tmp_path)
    assert analyser._read_post_plan_changes() == []


# ---------------------------------------------------------------------------
# analyse()
# ---------------------------------------------------------------------------

def test_analyse_returns_populated_context(tmp_path: Path) -> None:
    """analyse() returns GatherContext with correct fields populated."""
    # src packages
    src = tmp_path / "src"
    src.mkdir()
    (src / "mymodule").mkdir()
    (src / "mymodule" / "__init__.py").write_text("")

    # openplan dir + history
    (tmp_path / "openplan").mkdir()
    history = tmp_path / "openplan" / "HISTORY.md"
    history.write_text("**Note:** defer the dashboard\n")

    # openspec changes
    changes = tmp_path / "openspec" / "changes"
    changes.mkdir(parents=True)
    (changes / "some-change").mkdir()

    # archived roadmap
    archived = tmp_path / "openplan" / "archived" / "roadmap-1"
    archived.mkdir(parents=True)

    # design doc
    design = tmp_path / "design"
    design.mkdir()
    (design / "overview.md").write_text("# Overview\n")

    analyser = GatherAnalyser(tmp_path)
    # mock test collection to avoid running pytest
    with patch.object(analyser, "_collect_test_count", return_value=42):
        context = analyser.analyse()

    assert "mymodule" in context.existing_modules
    assert any("defer" in item.lower() or "Note:" in item for item in context.deferred_items)
    assert "some-change" in context.post_plan_changes
    assert context.test_count == 42
    assert "overview.md" in context.design_docs
    assert "roadmap-1" in context.prior_roadmap_ids


# ---------------------------------------------------------------------------
# write_gather_doc()
# ---------------------------------------------------------------------------

def test_write_gather_doc_sections(tmp_path: Path) -> None:
    """write_gather_doc() creates GATHER.md with all required sections."""
    (tmp_path / "openplan").mkdir()
    analyser = GatherAnalyser(tmp_path)
    context = GatherContext(
        existing_modules=["core", "cli"],
        deferred_items=["defer auth"],
        post_plan_changes=["change-x"],
        test_count=10,
        design_docs=["arch.md"],
        prior_roadmap_ids=["roadmap-2024"],
    )
    analyser.write_gather_doc(context, gaps=["Missing API layer"])

    gather_path = tmp_path / "openplan" / "GATHER.md"
    assert gather_path.exists()
    content = gather_path.read_text()

    assert "## What Exists" in content
    assert "## What Was Planned" in content
    assert "## What Was Deferred" in content
    assert "## Post-Plan Changes" in content
    assert "## Gaps Identified" in content
    assert "## Human Review Required" in content

    # Spot-check values
    assert "core" in content
    assert "roadmap-2024" in content
    assert "defer auth" in content
    assert "change-x" in content
    assert "Missing API layer" in content


# ---------------------------------------------------------------------------
# CLI --dry-run
# ---------------------------------------------------------------------------

def test_cli_dry_run_writes_gather_no_generate(tmp_path: Path) -> None:
    """--dry-run writes GATHER.md but does not attempt vision/roadmap generation."""
    (tmp_path / "openplan").mkdir()
    (tmp_path / "openspec" / "changes").mkdir(parents=True)

    runner = CliRunner()

    generate_called = []

    def mock_generate(context: GatherContext) -> tuple:
        generate_called.append(True)
        raise NotImplementedError("should not be called in dry-run")

    with patch.object(GatherAnalyser, "generate", mock_generate):
        result = runner.invoke(app, ["gather", "--project-dir", str(tmp_path), "--dry-run"])

    # GATHER.md should exist
    gather_path = tmp_path / "openplan" / "GATHER.md"
    assert gather_path.exists(), f"GATHER.md not written. CLI output:\n{result.output}"

    # generate should NOT have been called
    assert not generate_called, "generate() was called despite --dry-run"
