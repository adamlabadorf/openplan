import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import yaml
import tempfile
import shutil

from openplan.core.adr_generator import ADRGenerator
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


class TestADRGenerator:
    @patch("openplan.core.engine.OpenCodeClient")
    def test_generator_initialization(self, mock_client_class, temp_dirs):
        project_dir, plan_dir = temp_dirs
        engine = PlanningEngine(
            plan_dir=str(plan_dir),
            project_dir=str(project_dir),
        )
        generator = ADRGenerator(engine)
        assert generator.engine is engine

    @patch("openplan.core.adr_generator.ADRGenerator._persist_adr")
    @patch("openplan.core.engine.OpenCodeClient")
    def test_generate_happy_path(self, mock_client_class, mock_persist, temp_dirs):
        project_dir, plan_dir = temp_dirs

        mock_client = MagicMock()
        mock_client.generate.return_value = yaml.dump(
            {
                "id": "adr-0",  # will be overwritten by sequential ID
                "title": "Use PostgreSQL",
                "decision": "Use PostgreSQL for primary database",
                "context": "Need a relational database for user data",
                "alternatives": ["MySQL", "MongoDB"],
                "consequences": "Need to manage PostgreSQL instance",
                "status": "proposed",
            }
        )
        mock_client_class.return_value.__enter__.return_value = mock_client

        engine = PlanningEngine(
            plan_dir=str(plan_dir),
            project_dir=str(project_dir),
        )
        generator = ADRGenerator(engine)
        adr = generator.generate(
            decision_context="Need a database for user data",
            alternatives="MySQL, MongoDB",
        )

        assert adr.id == "adr-1"
        assert adr.title == "Use PostgreSQL"

    @patch("openplan.core.engine.OpenCodeClient")
    def test_sequential_id_generation(self, mock_client_class, temp_dirs):
        project_dir, plan_dir = temp_dirs

        adrs_dir = plan_dir / "adrs"
        adrs_dir.mkdir(parents=True, exist_ok=True)

        existing_adr = adrs_dir / "adr-2.yaml"
        existing_adr.write_text(
            "id: adr-2\ntitle: Test\ndecision: Test\ncontext: Test\nalternatives: []\nconsequences: Test\n"
        )

        mock_client = MagicMock()
        mock_client.generate.return_value = yaml.dump(
            {
                "id": "adr-0",
                "title": "New ADR",
                "decision": "Test",
                "context": "Test",
                "alternatives": [],
                "consequences": "Test",
                "status": "proposed",
            }
        )
        mock_client_class.return_value.__enter__.return_value = mock_client

        engine = PlanningEngine(
            plan_dir=str(plan_dir),
            project_dir=str(project_dir),
        )
        generator = ADRGenerator(engine)
        adr = generator.generate(
            decision_context="Test context",
            alternatives="",
        )

        assert adr.id == "adr-3"

    @patch("openplan.core.engine.OpenCodeClient")
    def test_first_adr_id_is_adr_1(self, mock_client_class, temp_dirs):
        project_dir, plan_dir = temp_dirs

        mock_client = MagicMock()
        mock_client.generate.return_value = yaml.dump(
            {
                "id": "adr-0",
                "title": "First ADR",
                "decision": "Test",
                "context": "Test",
                "alternatives": [],
                "consequences": "Test",
                "status": "proposed",
            }
        )
        mock_client_class.return_value.__enter__.return_value = mock_client

        engine = PlanningEngine(
            plan_dir=str(plan_dir),
            project_dir=str(project_dir),
        )
        generator = ADRGenerator(engine)
        adr = generator.generate(
            decision_context="Test context",
            alternatives="",
        )

        assert adr.id == "adr-1"
