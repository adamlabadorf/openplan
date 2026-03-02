import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import yaml
import tempfile
import shutil

from openplan.core.stabilizer import FeatureStabilizer
from openplan.core.schemas import Feature


@pytest.fixture
def temp_dirs():
    temp_dir = tempfile.mkdtemp()
    project_dir = Path(temp_dir) / "project"
    plan_dir = Path(temp_dir) / "plan"
    project_dir.mkdir(parents=True)
    plan_dir.mkdir(parents=True)
    yield project_dir, plan_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_feature():
    return Feature(
        id="feature-1",
        title="Test Feature",
        description="A test feature",
        acceptance_criteria=["user friendly", "fast", "reliable"],  # vague criteria
        dependencies=[],
        complexity="medium",
        spec_ready=False,
    )


class TestFeatureStabilizer:
    @patch("openplan.core.engine.OpenCodeClient")
    def test_stabilizer_initialization(self, mock_client_class, temp_dirs):
        from openplan.core.engine import PlanningEngine

        project_dir, plan_dir = temp_dirs
        engine = PlanningEngine(
            plan_dir=str(plan_dir),
            project_dir=str(project_dir),
        )
        stabilizer = FeatureStabilizer(engine)
        assert stabilizer.engine is engine

    @patch("openplan.core.stabilizer.FeatureStabilizer._persist_feature")
    @patch("openplan.core.engine.OpenCodeClient")
    def test_stabilize_happy_path(
        self, mock_client_class, mock_persist, temp_dirs, sample_feature
    ):
        from openplan.core.engine import PlanningEngine

        project_dir, plan_dir = temp_dirs

        mock_client = MagicMock()
        mock_client.generate.return_value = yaml.dump(
            {
                "id": "feature-1",
                "title": "Test Feature",
                "description": "A test feature",
                "acceptance_criteria": [
                    "user can complete task in under 3 clicks",
                    "response time under 100ms",
                    "error rate below 1%",
                ],
                "dependencies": [],
                "complexity": "medium",
                "spec_ready": True,
            }
        )
        mock_client_class.return_value.__enter__.return_value = mock_client

        engine = PlanningEngine(
            plan_dir=str(plan_dir),
            project_dir=str(project_dir),
        )
        stabilizer = FeatureStabilizer(engine)
        stabilized = stabilizer.stabilize(sample_feature)

        assert stabilized.spec_ready is True
        assert len(stabilized.acceptance_criteria) >= 3

    @patch("openplan.core.engine.OpenCodeClient")
    def test_stabilize_sets_spec_ready_true(
        self, mock_client_class, temp_dirs, sample_feature
    ):
        from openplan.core.engine import PlanningEngine

        project_dir, plan_dir = temp_dirs

        mock_client = MagicMock()
        mock_client.generate.return_value = yaml.dump(
            {
                "id": "feature-1",
                "title": "Test Feature",
                "description": "A test feature",
                "acceptance_criteria": [
                    "criterion 1",
                    "criterion 2",
                    "criterion 3",
                ],
                "dependencies": [],
                "complexity": "medium",
                "spec_ready": True,
            }
        )
        mock_client_class.return_value.__enter__.return_value = mock_client

        engine = PlanningEngine(
            plan_dir=str(plan_dir),
            project_dir=str(project_dir),
        )
        stabilizer = FeatureStabilizer(engine)
        stabilized = stabilizer.stabilize(sample_feature)

        assert stabilized.spec_ready is True
