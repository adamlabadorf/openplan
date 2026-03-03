import yaml
from typing import Optional

from openplan.core.schemas import Feature
from openplan.core.engine import PlanningEngine, PlanningError


class FeatureStabilizer:
    """Stabilizer for features - expands vague criteria and ensures testability."""

    def __init__(self, engine: PlanningEngine):
        self.engine = engine

    def stabilize(self, feature: Feature) -> Feature:
        """Stabilize a feature by expanding vague acceptance criteria.

        Args:
            feature: Feature object to stabilize

        Returns:
            Stabilized Feature with spec_ready=True if valid

        Raises:
            PlanningError: If stabilization fails after max refinements
        """
        feature_yaml = yaml.dump(feature.model_dump(by_alias=True))

        context = {
            "feature_yaml": feature_yaml,
        }

        try:
            with self.engine.client_context():
                stabilized_data = self.engine._generate_with_refinement(
                    template_name="stabilize_feature.j2",
                    context=context,
                    schema_class=None,
                    artifact_type="feature",
                )

            if isinstance(stabilized_data, dict):
                stabilized_data = self._normalize_feature_dict(stabilized_data, feature)
                stabilized_data["spec_ready"] = True
                feature = Feature(**stabilized_data)
                self._persist_feature(feature)
                return feature
            else:
                raise PlanningError("Stabilized feature is not a valid dictionary")

        except PlanningError:
            feature.spec_ready = False
            raise

    def _normalize_feature_dict(self, data: dict, original: Feature) -> dict:
        """Unwrap common LLM output shape mistakes and fill in missing fields from original."""
        # Unwrap {feature: {...}} or {Feature: {...}}
        for key in ("feature", "Feature"):
            if key in data and isinstance(data[key], dict):
                data = data[key]
                break

        # Normalize Acceptance criteria / Acceptance Criteria -> acceptance_criteria
        for bad_key in ("Acceptance criteria", "Acceptance Criteria", "acceptance criteria"):
            if bad_key in data:
                data["acceptance_criteria"] = data.pop(bad_key)

        # Fill in fields that must match the original if missing
        for field in ("id", "title", "description", "dependencies", "complexity"):
            if field not in data:
                data[field] = getattr(original, field)

        # Coerce dependencies from string to list if model returned a bare string
        if isinstance(data.get("dependencies"), str):
            dep = data["dependencies"].strip()
            data["dependencies"] = [dep] if dep else []

        return data

    def _persist_feature(self, feature: Feature) -> None:
        """Persist stabilized feature to plan directory."""
        features_dir = self.engine.plan_dir / "features"
        features_dir.mkdir(parents=True, exist_ok=True)
        filepath = features_dir / f"{feature.id}.yaml"
        with open(filepath, "w") as f:
            yaml.dump(feature.model_dump(by_alias=True), f, default_flow_style=False)
