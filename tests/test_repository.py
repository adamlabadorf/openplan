"""Tests for PlanRepository."""

import os
import tempfile
from pathlib import Path

import pytest

from openplan.core.schemas import (
    ADR,
    Campaign,
    Epic,
    Feature,
    Phase,
    PlanState,
    Roadmap,
    SuccessMetric,
    Vision,
)
from openplan.storage import LockedArtifactError, PlanRepository


class TestPlanRepositoryInit:
    """Tests for PlanRepository.init()."""

    def test_init_creates_correct_structure(self, tmp_path):
        """Init should create correct directory structure."""
        repo = PlanRepository(str(tmp_path))
        repo.init()

        assert (tmp_path / "openplan").exists()
        assert (tmp_path / "openplan" / "epics").exists()
        assert (tmp_path / "openplan" / "features").exists()
        assert (tmp_path / "openplan" / "campaigns").exists()
        assert (tmp_path / "openplan" / "adrs").exists()


class TestPlanRepositoryWrite:
    """Tests for PlanRepository.write()."""

    def test_write_artifact(self, tmp_path):
        """Write should save artifact to YAML."""
        repo = PlanRepository(str(tmp_path))
        repo.init()

        vision = Vision(
            id="test-vision",
            problem_statement="Reduce latency by 50%",
            target_users="End users",
            objectives=["Improve performance"],
            success_metrics=[
                SuccessMetric(name="latency", target="100ms", unit="milliseconds")
            ],
        )
        repo.write(vision)

        assert (tmp_path / "openplan" / "visions" / "test-vision.yaml").exists()

    def test_write_locked_artifact_raises_error(self, tmp_path):
        """Write should raise LockedArtifactError for locked artifacts."""
        repo = PlanRepository(str(tmp_path))
        repo.init()

        vision = Vision(
            id="test-vision",
            problem_statement="Reduce latency by 50%",
            target_users="End users",
            objectives=["Improve performance"],
            success_metrics=[
                SuccessMetric(name="latency", target="100ms", unit="milliseconds")
            ],
        )

        repo.lock("vision", "test-vision")

        with pytest.raises(LockedArtifactError):
            repo.write(vision)


class TestPlanRepositoryRead:
    """Tests for PlanRepository.read()."""

    def test_read_returns_validated_artifact(self, tmp_path):
        """Read should return validated artifact."""
        repo = PlanRepository(str(tmp_path))
        repo.init()

        vision = Vision(
            id="test-vision",
            problem_statement="Reduce latency by 50%",
            target_users="End users",
            objectives=["Improve performance"],
            success_metrics=[
                SuccessMetric(name="latency", target="100ms", unit="milliseconds")
            ],
        )
        repo.write(vision)

        read_vision = repo.read("vision", "test-vision", validate=True)
        assert read_vision is not None
        assert read_vision.id == "test-vision"  # type: ignore

    def test_read_nonexistent_returns_none(self, tmp_path):
        """Read should return None for nonexistent artifact."""
        repo = PlanRepository(str(tmp_path))
        repo.init()

        result = repo.read("vision", "nonexistent")
        assert result is None


class TestPlanRepositoryLock:
    """Tests for PlanRepository lock methods."""

    def test_lock_creates_marker_file(self, tmp_path):
        """Lock should create .locked marker file."""
        repo = PlanRepository(str(tmp_path))
        repo.init()

        repo.lock("vision", "test-vision")

        assert (tmp_path / "openplan" / "visions" / "test-vision.yaml.locked").exists()

    def test_is_locked_returns_correct_status(self, tmp_path):
        """is_locked should return correct status."""
        repo = PlanRepository(str(tmp_path))
        repo.init()

        assert repo.is_locked("vision", "test-vision") is False

        repo.lock("vision", "test-vision")

        assert repo.is_locked("vision", "test-vision") is True


class TestPlanRepositoryList:
    """Tests for PlanRepository.list()."""

    def test_list_returns_all_ids(self, tmp_path):
        """List should return all artifact IDs."""
        repo = PlanRepository(str(tmp_path))
        repo.init()

        for i in range(3):
            vision = Vision(
                id=f"vision-{i}",
                problem_statement="Reduce latency by 50%",
                target_users="End users",
                objectives=["Improve performance"],
                success_metrics=[
                    SuccessMetric(name="latency", target="100ms", unit="milliseconds")
                ],
            )
            repo.write(vision)

        ids = repo.list("vision")
        assert len(ids) == 3
        assert "vision-0" in ids
        assert "vision-1" in ids
        assert "vision-2" in ids

    def test_list_empty_for_no_artifacts(self, tmp_path):
        """List should return empty list for no artifacts."""
        repo = PlanRepository(str(tmp_path))
        repo.init()

        ids = repo.list("vision")
        assert ids == []


class TestPlanRepositoryReadState:
    """Tests for PlanRepository.read_state()."""

    def test_read_state_returns_plan_state(self, tmp_path):
        """read_state should return PlanState with all artifacts."""
        repo = PlanRepository(str(tmp_path))
        repo.init()

        vision = Vision(
            id="test-vision",
            problem_statement="Reduce latency by 50%",
            target_users="End users",
            objectives=["Improve performance"],
            success_metrics=[
                SuccessMetric(name="latency", target="100ms", unit="milliseconds")
            ],
        )
        repo.write(vision)

        epic = Epic(
            id="test-epic",
            title="Test Epic",
            outcome="Test outcome",
            success_metrics=[
                SuccessMetric(name="metric", target="100", unit="percent")
            ],
            architectural_impact=[
                {"component": "api", "change_type": "add", "description": "Add API"}  # type: ignore
            ],
        )
        repo.write(epic)

        feature = Feature(
            id="test-feature",
            title="Test Feature",
            description="Test description",
            acceptance_criteria=["criterion 1", "criterion 2", "criterion 3"],
        )
        repo.write(feature)

        campaign = Campaign(
            id="test-campaign",
            title="Test Campaign",
            description="Test description",
            phases=[
                Phase(name="p1", description="d1", duration_weeks=1),
                Phase(name="p2", description="d2", duration_weeks=2),
            ],
            rollback_strategy="Rollback plan",
        )
        repo.write(campaign)

        adr = ADR(
            id="test-adr",
            title="Test ADR",
            decision="Use REST",
            context="Need API",
            consequences="Simpler design",
        )
        repo.write(adr)

        state = repo.read_state()

        assert state.vision is not None
        assert state.vision.id == "test-vision"
        assert len(state.epics) == 1
        assert state.epics[0].id == "test-epic"
        assert len(state.features) == 1
        assert state.features[0].id == "test-feature"
        assert len(state.campaigns) == 1
        assert state.campaigns[0].id == "test-campaign"
        assert len(state.adrs) == 1
        assert state.adrs[0].id == "test-adr"
