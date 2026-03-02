"""Tests for schema validators."""

import pytest
from pydantic import ValidationError

from openplan.core.schemas import (
    Campaign,
    Epic,
    Feature,
    Phase,
    Roadmap,
    SuccessMetric,
    Vision,
)


class TestVisionValidators:
    """Tests for Vision schema validators."""

    def test_vision_requires_at_least_one_metric(self):
        """Vision must have at least one success metric."""
        with pytest.raises(ValidationError) as exc_info:
            Vision(
                id="test-vision",
                problem_statement="Test problem",
                target_users="Test users",
                objectives=["Test objective"],
                success_metrics=[],
            )
        assert "at least one success metric" in str(exc_info.value)

    def test_vision_rejects_vague_phrases(self):
        """Vision should reject vague phrases like 'improve', 'enhance', etc."""
        with pytest.raises(ValidationError) as exc_info:
            Vision(
                id="test-vision",
                problem_statement="We need to improve the system",
                target_users="Test users",
                objectives=["Test objective"],
                success_metrics=[
                    SuccessMetric(name="metric", target="100", unit="percent")
                ],
            )
        assert "improve" in str(exc_info.value).lower()

    def test_vision_accepts_valid_input(self):
        """Vision should accept valid input."""
        vision = Vision(
            id="test-vision",
            problem_statement="Reduce latency by 50%",
            target_users="End users",
            objectives=["Improve performance"],
            success_metrics=[
                SuccessMetric(name="latency", target="100ms", unit="milliseconds")
            ],
        )
        assert vision.id == "test-vision"


class TestEpicValidators:
    """Tests for Epic schema validators."""

    def test_epic_requires_at_least_one_metric(self):
        """Epic must have at least one success metric."""
        with pytest.raises(ValidationError) as exc_info:
            Epic(
                id="test-epic",
                title="Test Epic",
                outcome="Test outcome",
                success_metrics=[],
                architectural_impact=[],
            )
        assert "at least one success metric" in str(exc_info.value)

    def test_epic_requires_at_least_one_arch_impact(self):
        """Epic must have at least one architectural impact."""
        with pytest.raises(ValidationError) as exc_info:
            Epic(
                id="test-epic",
                title="Test Epic",
                outcome="Test outcome",
                success_metrics=[
                    SuccessMetric(name="metric", target="100", unit="percent")
                ],
                architectural_impact=[],
            )
        assert "at least one architectural impact" in str(exc_info.value)

    def test_epic_max_10_features(self):
        """Epic cannot have more than 10 features."""
        from openplan.core.schemas import FeatureRef

        with pytest.raises(ValidationError) as exc_info:
            Epic(
                id="test-epic",
                title="Test Epic",
                outcome="Test outcome",
                success_metrics=[
                    SuccessMetric(name="metric", target="100", unit="percent")
                ],
                architectural_impact=[
                    {"component": "api", "change_type": "add", "description": "Add API"}  # type: ignore
                ],
                features=[FeatureRef(feature_id=f"f{i}") for i in range(11)],
            )
        assert "more than 10 features" in str(exc_info.value)

    def test_epic_accepts_valid_input(self):
        """Epic should accept valid input."""
        from openplan.core.schemas import ArchitecturalImpact

        epic = Epic(
            id="test-epic",
            title="Test Epic",
            outcome="Test outcome",
            success_metrics=[
                SuccessMetric(name="metric", target="100", unit="percent")
            ],
            architectural_impact=[
                ArchitecturalImpact(
                    component="api", change_type="add", description="Add API"
                )
            ],
        )
        assert epic.id == "test-epic"


class TestFeatureValidators:
    """Tests for Feature schema validators."""

    def test_feature_min_3_acceptance_criteria(self):
        """Feature must have at least 3 acceptance criteria."""
        with pytest.raises(ValidationError) as exc_info:
            Feature(
                id="test-feature",
                title="Test Feature",
                description="Test description",
                acceptance_criteria=["criterion 1", "criterion 2"],
            )
        assert "at least 3" in str(exc_info.value)

    def test_feature_max_15_acceptance_criteria(self):
        """Feature cannot have more than 15 acceptance criteria."""
        with pytest.raises(ValidationError) as exc_info:
            Feature(
                id="test-feature",
                title="Test Feature",
                description="Test description",
                acceptance_criteria=[f"criterion {i}" for i in range(16)],
            )
        assert "more than 15" in str(exc_info.value)

    def test_feature_rejects_empty_criteria(self):
        """Feature cannot have empty acceptance criteria."""
        with pytest.raises(ValidationError) as exc_info:
            Feature(
                id="test-feature",
                title="Test Feature",
                description="Test description",
                acceptance_criteria=["valid criterion", "", "another valid"],
            )
        assert "empty" in str(exc_info.value)

    def test_feature_accepts_valid_input(self):
        """Feature should accept valid input."""
        feature = Feature(
            id="test-feature",
            title="Test Feature",
            description="Test description",
            acceptance_criteria=["criterion 1", "criterion 2", "criterion 3"],
        )
        assert feature.id == "test-feature"


class TestCampaignValidators:
    """Tests for Campaign schema validators."""

    def test_campaign_requires_rollback_strategy(self):
        """Campaign must have a rollback strategy."""
        with pytest.raises(ValidationError) as exc_info:
            Campaign(
                id="test-campaign",
                title="Test Campaign",
                description="Test description",
                phases=[Phase(name="p1", description="d", duration_weeks=1)],
                rollback_strategy="",
            )
        assert "rollback strategy" in str(exc_info.value)

    def test_campaign_min_2_phases(self):
        """Campaign must have at least 2 phases."""
        with pytest.raises(ValidationError) as exc_info:
            Campaign(
                id="test-campaign",
                title="Test Campaign",
                description="Test description",
                phases=[Phase(name="p1", description="d", duration_weeks=1)],
                rollback_strategy="Rollback plan",
            )
        assert "at least 2 phases" in str(exc_info.value)

    def test_campaign_accepts_valid_input(self):
        """Campaign should accept valid input."""
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
        assert campaign.id == "test-campaign"


class TestRoadmapValidators:
    """Tests for Roadmap schema validators."""

    def test_roadmap_max_8_epics(self):
        """Roadmap cannot have more than 8 epics."""
        from openplan.core.schemas import ArchitecturalImpact, FeatureRef

        with pytest.raises(ValidationError) as exc_info:
            Roadmap(
                id="test-roadmap",
                title="Test Roadmap",
                vision_id="test-vision",
                epics=[
                    Epic(
                        id=f"epic-{i}",
                        title=f"Epic {i}",
                        outcome="outcome",
                        success_metrics=[SuccessMetric(name="m", target="t", unit="u")],
                        architectural_impact=[
                            ArchitecturalImpact(
                                component="c", change_type="t", description="d"
                            )
                        ],
                    )
                    for i in range(9)
                ],
            )
        assert "more than 8 epics" in str(exc_info.value)

    def test_roadmap_accepts_valid_input(self):
        """Roadmap should accept valid input."""
        from openplan.core.schemas import ArchitecturalImpact

        roadmap = Roadmap(
            id="test-roadmap",
            title="Test Roadmap",
            vision_id="test-vision",
            epics=[
                Epic(
                    id="epic-1",
                    title="Epic 1",
                    outcome="outcome",
                    success_metrics=[SuccessMetric(name="m", target="t", unit="u")],
                    architectural_impact=[
                        ArchitecturalImpact(
                            component="c", change_type="t", description="d"
                        )
                    ],
                )
            ],
        )
        assert roadmap.id == "test-roadmap"
