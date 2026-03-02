"""Tests for CLI commands."""

import os
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from openplan.cli.main import app

runner = CliRunner()


class TestInitCommand:
    """Tests for openplan init command."""

    def test_init_creates_structure(self):
        """Init should create correct directory structure."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = runner.invoke(app, ["init", tmp_dir])

            assert result.exit_code == 0
            assert "Initialized OpenPlan" in result.stdout
            assert (Path(tmp_dir) / "openplan" / "epics").exists()
            assert (Path(tmp_dir) / "openplan" / "features").exists()
            assert (Path(tmp_dir) / "openplan" / "campaigns").exists()
            assert (Path(tmp_dir) / "openplan" / "adrs").exists()

    def test_init_current_directory(self):
        """Init should work with current directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = runner.invoke(app, ["init", "."], env={"PWD": tmp_dir})

            assert result.exit_code == 0
            assert "Initialized OpenPlan" in result.stdout


class TestValidateCommand:
    """Tests for openplan validate command."""

    def test_validate_requires_all_or_type_id(self):
        """Validate should require --all or --type with --id."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = runner.invoke(app, ["validate"], env={"PWD": tmp_dir})

            assert result.exit_code == 1
            assert "Specify --all" in result.stdout or "Error" in result.stdout

    def test_validate_all_with_no_artifacts(self):
        """Validate --all should succeed with no artifacts."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = runner.invoke(app, ["validate", "--all"], env={"PWD": tmp_dir})

            assert result.exit_code == 0
            assert "validated successfully" in result.stdout

    def test_validate_specific_artifact_not_found(self):
        """Validate specific artifact should handle not found."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = runner.invoke(
                app,
                ["validate", "--type", "vision", "--id", "nonexistent"],
                env={"PWD": tmp_dir},
            )

            assert result.exit_code == 1

    def test_validate_reports_errors(self):
        """Validate should report validation errors."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            vision_file = Path(tmp_dir) / "openplan" / "visions" / "test.yaml"
            vision_file.parent.mkdir(parents=True)
            vision_file.write_text(
                "id: test\n"
                "problem_statement: improve performance\n"
                "target_users: users\n"
                "objectives: []\n"
                "success_metrics: []\n"
            )

            result = runner.invoke(app, ["validate", "--all", tmp_dir])

            assert result.exit_code == 1
