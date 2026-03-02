"""Tests for CLI commands."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from openplan.cli.main import app

runner = CliRunner()


@pytest.fixture
def temp_project():
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_dir = Path(tmp_dir) / "project"
        project_dir.mkdir()
        (project_dir / "openplan").mkdir()
        (project_dir / "openplan" / "features").mkdir()
        (project_dir / "openplan" / "campaigns").mkdir()
        (project_dir / "openplan" / "adrs").mkdir()
        yield project_dir


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


class TestStabilizeFeatureCommand:
    """Tests for stabilize-feature command."""

    def test_stabilize_feature_not_found(self):
        """Stabilize should error if feature not found."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = runner.invoke(app, ["stabilize-feature", "nonexistent", tmp_dir])

            assert result.exit_code == 1
            assert "not found" in result.stdout.lower()

    @patch("openplan.core.engine.OpenCodeClient")
    def test_stabilize_feature_happy_path(self, mock_client_class):
        """Stabilize should work with valid feature."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            feature_file = Path(tmp_dir) / "openplan" / "features" / "feature-1.yaml"
            feature_file.parent.mkdir(parents=True, exist_ok=True)
            feature_file.write_text(
                "id: feature-1\n"
                "title: Test\n"
                "description: Test desc\n"
                "acceptance_criteria:\n"
                "  - criterion 1\n"
                "  - criterion 2\n"
                "  - criterion 3\n"
                "dependencies: []\n"
                "complexity: medium\n"
                "spec_ready: false\n"
            )

            import yaml

            mock_client = MagicMock()
            mock_client.generate.return_value = yaml.dump(
                {
                    "id": "feature-1",
                    "title": "Test",
                    "description": "Test desc",
                    "acceptance_criteria": [
                        "expanded criterion 1",
                        "expanded criterion 2",
                        "expanded criterion 3",
                    ],
                    "dependencies": [],
                    "complexity": "medium",
                    "spec_ready": True,
                }
            )
            mock_client_class.return_value.__enter__.return_value = mock_client

            result = runner.invoke(app, ["stabilize-feature", "feature-1", tmp_dir])

            assert result.exit_code == 0
            assert "stabilized" in result.stdout.lower()


class TestGenerateCampaignCommand:
    """Tests for generate-campaign command."""

    @patch("openplan.core.engine.OpenCodeClient")
    def test_generate_campaign_happy_path(self, mock_client_class):
        """Generate campaign should work."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            import yaml

            mock_client = MagicMock()
            mock_client.generate.return_value = yaml.dump(
                {
                    "id": "campaign-1",
                    "title": "Test Campaign",
                    "description": "Test",
                    "phases": [
                        {"name": "Phase 1", "description": "Desc", "duration_weeks": 1},
                        {"name": "Phase 2", "description": "Desc", "duration_weeks": 2},
                    ],
                    "rollback_strategy": "Revert",
                }
            )
            mock_client_class.return_value.__enter__.return_value = mock_client

            result = runner.invoke(
                app,
                ["generate-campaign", "database", "--debt", "slow queries", tmp_dir],
            )

            assert result.exit_code == 0
            assert "campaign" in result.stdout.lower()

    @patch("openplan.core.engine.OpenCodeClient")
    def test_generate_campaign_with_debt_flag(self, mock_client_class):
        """Generate campaign should accept --debt flag."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            import yaml

            mock_client = MagicMock()
            mock_client.generate.return_value = yaml.dump(
                {
                    "id": "campaign-1",
                    "title": "Test",
                    "description": "Test",
                    "phases": [
                        {"name": "Phase 1", "description": "Desc", "duration_weeks": 1},
                        {"name": "Phase 2", "description": "Desc", "duration_weeks": 2},
                    ],
                    "rollback_strategy": "Revert",
                }
            )
            mock_client_class.return_value.__enter__.return_value = mock_client

            result = runner.invoke(
                app, ["generate-campaign", "api", "--debt", "legacy code", tmp_dir]
            )

            assert result.exit_code == 0


class TestGenerateAdrCommand:
    """Tests for generate-adr command."""

    @patch("openplan.core.engine.OpenCodeClient")
    def test_generate_adr_happy_path(self, mock_client_class):
        """Generate ADR should work."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            import yaml

            mock_client = MagicMock()
            mock_client.generate.return_value = yaml.dump(
                {
                    "id": "adr-0",
                    "title": "Use PostgreSQL",
                    "decision": "Use PostgreSQL",
                    "context": "Need database",
                    "alternatives": ["MySQL"],
                    "consequences": "Manage PostgreSQL",
                    "status": "proposed",
                }
            )
            mock_client_class.return_value.__enter__.return_value = mock_client

            result = runner.invoke(
                app,
                ["generate-adr", "--context", "Need database", tmp_dir],
            )

            assert result.exit_code == 0
            assert "adr" in result.stdout.lower()

    @patch("openplan.core.engine.OpenCodeClient")
    def test_generate_adr_with_context_flag(self, mock_client_class):
        """Generate ADR should accept --context flag."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            import yaml

            mock_client = MagicMock()
            mock_client.generate.return_value = yaml.dump(
                {
                    "id": "adr-0",
                    "title": "Test",
                    "decision": "Test",
                    "context": "Context",
                    "alternatives": [],
                    "consequences": "Consequences",
                    "status": "proposed",
                }
            )
            mock_client_class.return_value.__enter__.return_value = mock_client

            result = runner.invoke(
                app, ["generate-adr", "--context", "Decision context", tmp_dir]
            )

            assert result.exit_code == 0


class TestModelFlag:
    """Tests for --model flag on commands."""

    @patch("openplan.core.engine.OpenCodeClient")
    def test_stabilize_feature_accepts_model_flag(self, mock_client_class):
        """Stabilize should accept --model flag."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            feature_file = Path(tmp_dir) / "openplan" / "features" / "feature-1.yaml"
            feature_file.parent.mkdir(parents=True, exist_ok=True)
            feature_file.write_text(
                "id: feature-1\n"
                "title: Test\n"
                "description: Test desc\n"
                "acceptance_criteria:\n"
                "  - criterion 1\n"
                "  - criterion 2\n"
                "  - criterion 3\n"
                "dependencies: []\n"
                "complexity: medium\n"
                "spec_ready: false\n"
            )

            import yaml

            mock_client = MagicMock()
            mock_client.generate.return_value = yaml.dump(
                {
                    "id": "feature-1",
                    "title": "Test",
                    "description": "Test desc",
                    "acceptance_criteria": ["c1", "c2", "c3"],
                    "dependencies": [],
                    "complexity": "medium",
                    "spec_ready": True,
                }
            )
            mock_client_class.return_value.__enter__.return_value = mock_client

            result = runner.invoke(
                app, ["stabilize-feature", "feature-1", "--model", "gpt-4", tmp_dir]
            )

            assert result.exit_code == 0
            assert "stabilized" in result.stdout.lower()
