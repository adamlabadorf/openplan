import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import yaml
import tempfile
import shutil

from openplan.core.campaign_generator import CampaignGenerator
from openplan.core.engine import PlanningEngine, PlanningError


@pytest.fixture
def temp_dirs():
    temp_dir = tempfile.mkdtemp()
    project_dir = Path(temp_dir) / "project"
    plan_dir = Path(temp_dir) / "plan"
    project_dir.mkdir(parents=True)
    plan_dir.mkdir(parents=True)
    yield project_dir, plan_dir
    shutil.rmtree(temp_dir)


class TestCampaignGenerator:
    @patch("openplan.core.engine.OpenCodeClient")
    def test_generator_initialization(self, mock_client_class, temp_dirs):
        project_dir, plan_dir = temp_dirs
        engine = PlanningEngine(
            plan_dir=str(plan_dir),
            project_dir=str(project_dir),
        )
        generator = CampaignGenerator(engine)
        assert generator.engine is engine

    @patch("openplan.core.campaign_generator.CampaignGenerator._persist_campaign")
    @patch("openplan.core.engine.OpenCodeClient")
    def test_generate_happy_path(self, mock_client_class, mock_persist, temp_dirs):
        project_dir, plan_dir = temp_dirs

        mock_client = MagicMock()
        mock_client.generate.return_value = yaml.dump(
            {
                "id": "campaign-1",
                "title": "Refactor Database",
                "description": "Address technical debt in database layer",
                "phases": [
                    {"name": "Phase 1", "description": "Analyze", "duration_weeks": 2},
                    {
                        "name": "Phase 2",
                        "description": "Implement",
                        "duration_weeks": 4,
                    },
                ],
                "rollback_strategy": "Revert to previous version from git",
            }
        )
        mock_client_class.return_value.__enter__.return_value = mock_client

        engine = PlanningEngine(
            plan_dir=str(plan_dir),
            project_dir=str(project_dir),
        )
        generator = CampaignGenerator(engine)
        campaign = generator.generate(
            subsystem="database",
            technical_debt="Slow queries",
        )

        assert campaign.id == "campaign-1"
        assert campaign.rollback_strategy is not None

    @patch("openplan.core.engine.OpenCodeClient")
    def test_validation_fails_for_empty_rollback_strategy(
        self, mock_client_class, temp_dirs
    ):
        project_dir, plan_dir = temp_dirs

        call_count = 0

        def generate_side_effect(prompt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return yaml.dump(
                    {
                        "id": "campaign-1",
                        "title": "Test Campaign",
                        "description": "Test",
                        "phases": [
                            {
                                "name": "Phase 1",
                                "description": "Desc",
                                "duration_weeks": 1,
                            },
                            {
                                "name": "Phase 2",
                                "description": "Desc",
                                "duration_weeks": 2,
                            },
                        ],
                        "rollback_strategy": "",  # empty
                    }
                )
            if call_count == 2:
                return '{"issues": ["rollback_strategy is empty"], "requires_refinement": true}'
            return yaml.dump(
                {
                    "id": "campaign-1",
                    "title": "Test Campaign",
                    "description": "Test",
                    "phases": [
                        {"name": "Phase 1", "description": "Desc", "duration_weeks": 1},
                        {"name": "Phase 2", "description": "Desc", "duration_weeks": 2},
                    ],
                    "rollback_strategy": "Revert changes",
                }
            )

        mock_client = MagicMock()
        mock_client.generate.side_effect = generate_side_effect
        mock_client_class.return_value.__enter__.return_value = mock_client

        engine = PlanningEngine(
            plan_dir=str(plan_dir),
            project_dir=str(project_dir),
        )
        generator = CampaignGenerator(engine)
        campaign = generator.generate(
            subsystem="api",
            technical_debt="legacy code",
        )

        assert campaign.rollback_strategy != ""
        assert campaign.rollback_strategy.strip() != ""
