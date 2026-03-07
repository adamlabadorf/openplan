import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import yaml
import tempfile
import shutil

from openplan.core.engine import PlanningEngine, PlanningError
from openplan.core.schemas import (
    Vision,
    Epic,
    Feature,
    SuccessMetric,
    ArchitecturalImpact,
)


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
def sample_vision():
    return Vision(
        id="vision-1",
        problem_statement="Build a todo app with REST API",
        target_users="Developers",
        objectives=["Create API", "Create UI"],
        success_metrics=[SuccessMetric(name="api_latency", target="<100ms", unit="ms")],
    )


@pytest.fixture
def sample_epic():
    return Epic(
        id="epic-1",
        title="Build API",
        outcome="REST API for todo items",
        success_metrics=[
            SuccessMetric(name="response_time", target="<100ms", unit="ms")
        ],
        architectural_impact=[
            ArchitecturalImpact(
                component="backend", change_type="new", description="New REST API"
            )
        ],
    )


class TestPlanningEngine:
    def test_engine_initialization(self, temp_dirs):
        project_dir, plan_dir = temp_dirs
        engine = PlanningEngine(
            plan_dir=str(plan_dir),
            project_dir=str(project_dir),
            model="gpt-4",
        )
        assert engine.plan_dir == plan_dir
        assert engine.project_dir == project_dir
        assert engine.model == "gpt-4"

    def test_engine_default_model(self, temp_dirs):
        project_dir, plan_dir = temp_dirs
        engine = PlanningEngine(
            plan_dir=str(plan_dir),
            project_dir=str(project_dir),
        )
        assert engine.model is None


class TestGenerateRoadmap:
    @patch("openplan.core.engine.OpenCodeClient")
    def test_generate_roadmap_happy_path(
        self, mock_client_class, temp_dirs, sample_vision
    ):
        project_dir, plan_dir = temp_dirs

        mock_client = MagicMock()
        mock_client.generate.return_value = yaml.dump(
            {
                "id": "roadmap-1",
                "title": "Test Roadmap",
                "vision_id": "vision-1",
                "epics": [],
            }
        )
        mock_client_class.return_value.__enter__.return_value = mock_client

        engine = PlanningEngine(
            plan_dir=str(plan_dir),
            project_dir=str(project_dir),
        )
        roadmap = engine.generate_roadmap(sample_vision)

        assert roadmap.id == "roadmap-1"
        assert roadmap.title == "Test Roadmap"
        assert roadmap.vision_id == "vision-1"

    @patch("openplan.core.engine.OpenCodeClient")
    def test_refinement_loop_behavior(
        self, mock_client_class, temp_dirs, sample_vision
    ):
        project_dir, plan_dir = temp_dirs

        call_count = 0

        def generate_side_effect(prompt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return yaml.dump(
                    {
                        "id": "roadmap-1",
                        "title": "Invalid",
                        "vision_id": "vision-1",
                        "epics": "not_a_list",
                    }
                )
            if call_count == 2:
                return '{"issues": ["epics should be a list"], "requires_refinement": true}'
            return yaml.dump(
                {
                    "id": "roadmap-1",
                    "title": "Test Roadmap",
                    "vision_id": "vision-1",
                    "epics": [],
                }
            )

        mock_client = MagicMock()
        mock_client.generate.side_effect = generate_side_effect
        mock_client_class.return_value.__enter__.return_value = mock_client

        engine = PlanningEngine(
            plan_dir=str(plan_dir),
            project_dir=str(project_dir),
        )
        roadmap = engine.generate_roadmap(sample_vision)

        assert call_count == 3

    @patch("openplan.core.engine.OpenCodeClient")
    def test_failure_after_max_refinements(
        self, mock_client_class, temp_dirs, sample_vision
    ):
        project_dir, plan_dir = temp_dirs

        mock_client = MagicMock()
        mock_client.generate.return_value = "invalid: yaml: content:"
        mock_client_class.return_value.__enter__.return_value = mock_client

        engine = PlanningEngine(
            plan_dir=str(plan_dir),
            project_dir=str(project_dir),
        )

        with pytest.raises(PlanningError) as exc_info:
            engine.generate_roadmap(sample_vision)

        assert "2 refinements" in str(exc_info.value.message)


class TestDecomposeEpic:
    @patch("openplan.core.engine.OpenCodeClient")
    def test_decompose_epic_happy_path(self, mock_client_class, temp_dirs, sample_epic):
        project_dir, plan_dir = temp_dirs

        mock_client = MagicMock()
        mock_client.generate.return_value = yaml.dump(
            [
                {
                    "id": "feature-1",
                    "title": "Create endpoint",
                    "description": "POST /todos endpoint",
                    "acceptance_criteria": [
                        "returns 201",
                        "validates input",
                        "creates todo",
                    ],
                    "dependencies": [],
                    "complexity": "medium",
                    "spec_ready": False,
                }
            ]
        )
        mock_client_class.return_value.__enter__.return_value = mock_client

        engine = PlanningEngine(
            plan_dir=str(plan_dir),
            project_dir=str(project_dir),
        )
        features = engine.decompose_epic(sample_epic)

        assert len(features) == 1
        assert features[0].id == "epic-1-feature-1"
        assert features[0].title == "Create endpoint"

    @patch("openplan.core.engine.OpenCodeClient")
    def test_decompose_epic_multiple_features(
        self, mock_client_class, temp_dirs, sample_epic
    ):
        project_dir, plan_dir = temp_dirs

        mock_client = MagicMock()
        mock_client.generate.return_value = yaml.dump(
            [
                {
                    "id": "feature-1",
                    "title": "Feature 1",
                    "description": "Desc",
                    "acceptance_criteria": ["a", "b", "c"],
                    "dependencies": [],
                    "complexity": "low",
                    "spec_ready": False,
                },
                {
                    "id": "feature-2",
                    "title": "Feature 2",
                    "description": "Desc",
                    "acceptance_criteria": ["a", "b", "c"],
                    "dependencies": ["feature-1"],
                    "complexity": "medium",
                    "spec_ready": False,
                },
            ]
        )
        mock_client_class.return_value.__enter__.return_value = mock_client

        engine = PlanningEngine(
            plan_dir=str(plan_dir),
            project_dir=str(project_dir),
        )
        features = engine.decompose_epic(sample_epic)

        assert len(features) == 2
