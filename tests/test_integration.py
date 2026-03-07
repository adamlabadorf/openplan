"""End-to-end integration tests for OpenPlan."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from typer.testing import CliRunner

from openplan.cli.main import app
from openplan.core.schemas import Feature

runner = CliRunner()


@pytest.fixture
def project_dir(tmp_path):
    """Create a temporary project directory with OpenPlan structure."""
    project = tmp_path / "project"
    project.mkdir()
    (project / "openplan").mkdir()
    (project / "openplan" / "visions").mkdir()
    (project / "openplan" / "epics").mkdir()
    (project / "openplan" / "features").mkdir()
    (project / "openplan" / "campaigns").mkdir()
    (project / "openplan" / "adrs").mkdir()
    (project / "openplan" / "roadmaps").mkdir()
    return project


@pytest.fixture
def openspec_dir(tmp_path):
    """Create a temporary OpenSpec directory."""
    openspec = tmp_path / "openspec"
    openspec.mkdir()
    (openspec / "changes").mkdir()
    return openspec


@pytest.fixture
def mock_openplan_client():
    """Mock OpenCodeClient for all LLM generation."""
    with patch("openplan.core.engine.OpenCodeClient") as mock:
        yield mock


def test_full_roadmap_pipeline(project_dir, mock_openplan_client):
    """Test init -> load vision -> generate_roadmap -> assert roadmap.yaml on disk."""
    vision_file = project_dir / "openplan" / "visions" / "vision.yaml"
    vision_file.write_text(
        "id: test-vision\n"
        "problem_statement: Reduce API response time from 500ms to under 100ms for user dashboard\n"
        "target_users: Internal engineering team\n"
        "objectives:\n"
        "  - Reduce latency\n"
        "  - Improve user experience\n"
        "success_metrics:\n"
        "  - name: response_time\n"
        "    target: '100'\n"
        "    unit: milliseconds\n"
    )

    mock_client = MagicMock()
    mock_client.generate.return_value = yaml.dump(
        {
            "id": "roadmap-1",
            "title": "API Performance Roadmap",
            "vision_id": "test-vision",
            "epics": [
                {
                    "id": "epic-1",
                    "title": "Database Optimization",
                    "outcome": "50% reduction in query time",
                    "success_metrics": [
                        {"name": "query_time", "target": "50", "unit": "ms"}
                    ],
                    "architectural_impact": [
                        {
                            "component": "database",
                            "change_type": "indexing",
                            "description": "Add indexes",
                        }
                    ],
                    "features": [],
                }
            ],
        }
    )
    mock_openplan_client.return_value.__enter__.return_value = mock_client

    result = runner.invoke(app, ["generate-roadmap", str(project_dir)])

    assert result.exit_code == 0, result.stdout
    assert "roadmap" in result.stdout.lower()

    roadmap_path = project_dir / "openplan" / "roadmaps" / "roadmap-1.yaml"
    assert roadmap_path.exists()

    with open(roadmap_path) as f:
        roadmap_data = yaml.safe_load(f)

    assert roadmap_data["id"] == "roadmap-1"
    assert len(roadmap_data["epics"]) == 1


def test_full_epic_decomposition(project_dir, mock_openplan_client):
    """Test generate_roadmap -> decompose first epic -> assert feature YAMLs on disk."""
    vision_file = project_dir / "openplan" / "visions" / "vision.yaml"
    vision_file.write_text(
        "id: test-vision\n"
        "problem_statement: Reduce API response time from 500ms to under 100ms for user dashboard\n"
        "target_users: Internal engineering team\n"
        "objectives:\n"
        "  - Reduce latency\n"
        "success_metrics:\n"
        "  - name: response_time\n"
        "    target: '100'\n"
        "    unit: milliseconds\n"
    )

    epic_file = project_dir / "openplan" / "epics" / "epic-1.yaml"
    epic_file.parent.mkdir(exist_ok=True)
    epic_file.write_text(
        "id: epic-1\n"
        "title: Database Optimization\n"
        "outcome: 50% reduction in query time\n"
        "success_metrics:\n"
        "  - name: query_time\n"
        "    target: '50'\n"
        "    unit: ms\n"
        "architectural_impact:\n"
        "  - component: database\n"
        "    change_type: indexing\n"
        "    description: Add indexes\n"
    )

    mock_client = MagicMock()
    mock_client.generate.return_value = yaml.dump(
        [
            {
                "id": "epic-1-feature-1",
                "title": "Add Database Indexes",
                "description": "Add indexes on frequently queried columns",
                "acceptance_criteria": [
                    "Create index on user_id column",
                    "Create composite index on (user_id, created_at)",
                    "Verify query performance improvement",
                ],
                "dependencies": [],
                "complexity": "low",
                "spec_ready": False,
            },
            {
                "id": "epic-1-feature-2",
                "title": "Query Optimization",
                "description": "Optimize slow queries",
                "acceptance_criteria": [
                    "Identify slow queries",
                    "Rewrite queries for performance",
                    "Add query caching",
                ],
                "dependencies": ["epic-1-feature-1"],
                "complexity": "medium",
                "spec_ready": False,
            },
        ]
    )
    mock_openplan_client.return_value.__enter__.return_value = mock_client

    result = runner.invoke(app, ["decompose-epic", "epic-1", str(project_dir)])

    assert result.exit_code == 0, result.stdout
    assert "feature" in result.stdout.lower()

    feature1_path = project_dir / "openplan" / "features" / "epic-1-feature-1.yaml"
    feature2_path = project_dir / "openplan" / "features" / "epic-1-feature-2.yaml"

    assert feature1_path.exists()
    assert feature2_path.exists()

    with open(feature1_path) as f:
        feature1_data = yaml.safe_load(f)

    assert feature1_data["id"] == "epic-1-feature-1"
    assert len(feature1_data["acceptance_criteria"]) >= 3


def test_feature_stabilization_pipeline(project_dir, mock_openplan_client):
    """Test decompose -> stabilize -> assert spec_ready=True in persisted YAML."""
    feature_file = project_dir / "openplan" / "features" / "epic-1-feature-1.yaml"
    feature_file.parent.mkdir(exist_ok=True)
    feature_file.write_text(
        "id: epic-1-feature-1\n"
        "title: Test Feature\n"
        "description: A test feature\n"
        "acceptance_criteria:\n"
        "  - criterion one\n"
        "  - criterion two\n"
        "  - criterion three\n"
        "dependencies: []\n"
        "complexity: medium\n"
        "spec_ready: false\n"
    )

    mock_client = MagicMock()
    mock_client.generate.return_value = yaml.dump(
        {
            "id": "epic-1-feature-1",
            "title": "Test Feature",
            "description": "A test feature",
            "acceptance_criteria": [
                "Expanded criterion one with specific steps",
                "Expanded criterion two with verification steps",
                "Expanded criterion three with test cases",
            ],
            "dependencies": [],
            "complexity": "medium",
            "spec_ready": True,
        }
    )
    mock_openplan_client.return_value.__enter__.return_value = mock_client

    result = runner.invoke(app, ["stabilize-feature", "epic-1-feature-1", str(project_dir)])

    assert result.exit_code == 0, result.stdout
    assert "stabilized" in result.stdout.lower()

    with open(feature_file) as f:
        feature_data = yaml.safe_load(f)

    assert feature_data["spec_ready"] is True
    assert len(feature_data["acceptance_criteria"]) == 3


def test_openspec_export_blocked_if_not_ready(
    project_dir, openspec_dir, mock_openplan_client
):
    """Assert ExportError raised for feature with spec_ready=False."""
    from openplan.integrations.openspec import ExportError, export_feature
    from openplan.core.schemas import Feature

    feature = Feature(
        id="epic-1-feature-1",
        title="Test",
        description="Test feature",
        acceptance_criteria=["c1", "c2", "c3"],
        spec_ready=False,
    )

    with pytest.raises(ExportError) as exc_info:
        export_feature(feature, openspec_dir)

    assert "spec_ready=False" in str(exc_info.value)


def test_status_command(project_dir):
    """Test init, write artifacts, run openplan status, assert output contains expected counts."""
    (project_dir / "openplan" / "visions" / "vision.yaml").write_text(
        "id: vision-1\n"
        "problem_statement: Reduce API response time from 500ms to under 100ms for user dashboard\n"
        "target_users: Internal engineering team\n"
        "objectives:\n"
        "  - Reduce latency\n"
        "success_metrics:\n"
        "  - name: response_time\n"
        "    target: '100'\n"
        "    unit: milliseconds\n"
    )

    (project_dir / "openplan" / "features" / "epic-1-feature-1.yaml").write_text(
        "id: epic-1-feature-1\n"
        "title: Test Feature\n"
        "description: Test\n"
        "acceptance_criteria:\n"
        "  - criterion one\n"
        "  - criterion two\n"
        "  - criterion three\n"
        "dependencies: []\n"
        "complexity: medium\n"
        "spec_ready: true\n"
    )

    (project_dir / "openplan" / "features" / "epic-1-feature-2.yaml").write_text(
        "id: epic-1-feature-2\n"
        "title: Another Feature\n"
        "description: Test\n"
        "acceptance_criteria:\n"
        "  - criterion one\n"
        "  - criterion two\n"
        "  - criterion three\n"
        "dependencies: []\n"
        "complexity: low\n"
        "spec_ready: false\n"
    )

    (project_dir / "openplan" / "campaigns" / "campaign-1.yaml").write_text(
        "id: campaign-1\n"
        "title: Test Campaign\n"
        "description: Test\n"
        "phases:\n"
        "  - name: Phase 1\n"
        "    description: Desc\n"
        "    duration_weeks: 1\n"
        "  - name: Phase 2\n"
        "    description: Desc\n"
        "    duration_weeks: 2\n"
        "rollback_strategy: Revert\n"
    )

    (project_dir / "openplan" / "adrs" / "adr-1.yaml").write_text(
        "id: adr-1\n"
        "title: Use PostgreSQL\n"
        "decision: Use PostgreSQL\n"
        "context: Need database\n"
        "alternatives:\n"
        "  - MySQL\n"
        "consequences: Manage PostgreSQL\n"
        "status: proposed\n"
    )

    result = runner.invoke(app, ["status", str(project_dir)])

    assert result.exit_code == 0
    assert "Vision loaded:" in result.stdout and "Yes" in result.stdout
    assert "2 total" in result.stdout
    assert "1 spec_ready" in result.stdout
    assert "Campaigns:" in result.stdout
    assert "ADRs:" in result.stdout


def test_status_command_with_locked_artifact(project_dir):
    """Test status command shows locked artifacts."""
    from openplan.storage import PlanRepository

    repo = PlanRepository(str(project_dir))

    (project_dir / "openplan" / "visions").mkdir(parents=True, exist_ok=True)
    vision_file = project_dir / "openplan" / "visions" / "vision-1.yaml"
    vision_file.write_text(
        "id: vision-1\n"
        "problem_statement: Reduce API response time from 500ms to under 100ms for user dashboard\n"
        "target_users: Internal engineering team\n"
        "objectives:\n"
        "  - Reduce latency\n"
        "success_metrics:\n"
        "  - name: response_time\n"
        "    target: '100'\n"
        "    unit: milliseconds\n"
    )

    repo.lock("vision", "vision-1")

    result = runner.invoke(app, ["status", str(project_dir)])

    assert result.exit_code == 0
    assert "Locked artifacts:" in result.stdout
    assert "vision/vision-1" in result.stdout
