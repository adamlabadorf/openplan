import json
import re

import yaml
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Type, TypeVar

from openplan.core.schemas import (
    Epic,
    Feature,
    Roadmap,
    Vision,
)
from openplan.core.ordering import resolve_epic_order
from openplan.integrations.acp_client import GenerationError, OpenCodeClient
from openplan.prompts.loader import TemplateLoader


class PlanningError(Exception):
    """Raised when planning generation fails after max refinements."""

    def __init__(self, message: str, validation_errors: Optional[list] = None):
        super().__init__(message)
        self.message = message
        self.validation_errors = validation_errors or []


T = TypeVar("T", bound=Roadmap)


class PlanningEngine:
    """Engine for generating planning artifacts using AI."""

    MAX_REFINEMENTS = 2

    def __init__(
        self,
        plan_dir: str,
        project_dir: str,
        model: Optional[str] = None,
    ):
        self.plan_dir = Path(plan_dir)
        self.project_dir = Path(project_dir)
        self.model = model
        self.template_loader = TemplateLoader()
        # Active OpenCodeClient — set only during a top-level planning call.
        # One subprocess is shared across all _generate() calls in that run.
        self._client: Optional[OpenCodeClient] = None

    @contextmanager
    def client_context(self):
        """Open one ACP subprocess for a planning run.

        Used by FeatureStabilizer, CampaignGenerator, and ADRGenerator so they
        share the same single-subprocess pattern as generate_roadmap /
        decompose_epic.  Every engine._generate() call within the block reuses
        the same subprocess; each call still gets its own fresh session::

            with engine.client_context():
                data = engine._generate_with_refinement(...)
        """
        with OpenCodeClient(
            project_dir=str(self.project_dir), model=self.model
        ) as client:
            self._client = client
            try:
                yield client
            finally:
                self._client = None

    def generate_roadmap(
        self,
        vision: Vision,
        constraints: str = "",
        time_horizon: str = "12 months",
    ) -> Roadmap:
        """Generate a roadmap from a Vision.

        Args:
            vision: Vision object to generate roadmap from
            constraints: Optional constraints string
            time_horizon: Time horizon for the roadmap

        Returns:
            Validated Roadmap object

        Raises:
            PlanningError: If validation fails after max refinements
        """
        with OpenCodeClient(
            project_dir=str(self.project_dir), model=self.model
        ) as client:
            self._client = client
            try:
                context = {
                    # Flattened fields for cleaner templates
                    "vision_id": vision.id,
                    "problem_statement": vision.problem_statement,
                    "objectives": vision.objectives,
                    "constraints": constraints,
                    "time_horizon": time_horizon,
                    # Full YAML dump for templates that want the whole thing
                    "vision_yaml": yaml.dump(vision.model_dump(by_alias=True)),
                }
                roadmap_yaml = self._generate_with_refinement(
                    template_name="roadmap.j2",
                    context=context,
                    schema_class=Roadmap,
                    artifact_type="roadmap",
                )
                if isinstance(roadmap_yaml, dict):
                    roadmap_yaml["vision_id"] = vision.id
                    roadmap = Roadmap(**roadmap_yaml)
                else:
                    raise PlanningError("Generated roadmap is not a valid dictionary")
                self._persist_roadmap(roadmap)
                return roadmap
            finally:
                self._client = None

    def decompose_epic(
        self,
        epic: Epic,
        arch_summary: str = "",
    ) -> list[Feature]:
        """Decompose an epic into features.

        Args:
            epic: Epic object to decompose
            arch_summary: Optional architecture summary

        Returns:
            List of validated Feature objects

        Raises:
            PlanningError: If validation fails after max refinements
        """
        # Note: resolve_epic_order is intended for callers who have the full epic
        # list (e.g. run_pipeline.py). decompose_epic receives a single Epic, so
        # ordering cannot be applied here. Callers should call resolve_epic_order
        # on roadmap.epics before iterating and calling decompose_epic.
        with OpenCodeClient(
            project_dir=str(self.project_dir), model=self.model
        ) as client:
            self._client = client
            try:
                epic_yaml = yaml.dump(epic.model_dump(by_alias=True))
                context = {
                    "epic_yaml": epic_yaml,
                    "arch_summary": arch_summary,
                }
                features_yaml = self._generate_with_refinement(
                    template_name="epic.j2",
                    context=context,
                    schema_class=None,
                    artifact_type="feature",
                )
                features_list = self._normalize_features(features_yaml, epic.id)
                features = []
                for i, feature_data in enumerate(features_list, 1):
                    # Prefix IDs with epic to ensure uniqueness across epics,
                    # but only if not already prefixed (idempotent).
                    raw_id = feature_data.get("id", f"feature-{i:03d}")
                    if not raw_id.startswith(f"{epic.id}-"):
                        raw_id = f"{epic.id}-{raw_id}"
                    feature_data["id"] = raw_id
                    # Coerce dependencies string -> list
                    deps = feature_data.get("dependencies", [])
                    if isinstance(deps, str):
                        feature_data["dependencies"] = [deps] if deps.strip() else []
                    feature = Feature(**feature_data)
                    features.append(feature)
                    self._persist_feature(feature)
                return features
            finally:
                self._client = None

    def _normalize_features(self, raw: object, epic_id: str) -> list[dict]:
        """Normalize LLM output into a list of feature dicts.

        Handles multiple output shapes:
        - list of dicts (correct)
        - single dict (one feature)
        - dict of {key: feature_dict} (keyed map — common LLM mistake)
        """
        if isinstance(raw, list):
            return [f for f in raw if isinstance(f, dict)]

        if isinstance(raw, dict):
            # Check if it looks like a keyed map: {"feature-1": {...}, ...}
            first_val = next(iter(raw.values()), None)
            if isinstance(first_val, dict):
                return list(raw.values())
            # Single feature dict
            return [raw]

        return []

    def _generate_with_refinement(
        self,
        template_name: str,
        context: dict,
        schema_class: Optional[Type[T]],
        artifact_type: str,
    ) -> dict | list:
        """Generate content with critique/refine loop.

        Args:
            template_name: Name of the template to use
            context: Template context
            schema_class: Pydantic model class for validation
            artifact_type: Type of artifact being generated

        Returns:
            Parsed and validated YAML data

        Raises:
            PlanningError: If validation fails after max refinements
        """
        validation_errors: Optional[list] = None
        current_yaml: dict = {}
        critique_result: dict = {}

        for iteration in range(self.MAX_REFINEMENTS + 1):
            if iteration == 0:
                prompt = self.template_loader.render(template_name, context)
            else:
                refine_context = {
                    "artifact_type": artifact_type,
                    "artifact_yaml": yaml.dump(current_yaml),
                    "critique_json": json.dumps(critique_result),
                }
                prompt = self.template_loader.render("refine.j2", refine_context)

            generated_yaml = self._generate(prompt)

            try:
                parsed = yaml.safe_load(generated_yaml)
                if parsed is None:
                    parsed = {}
                current_yaml = parsed
            except yaml.YAMLError as e:
                validation_errors = [str(e)]
                if iteration < self.MAX_REFINEMENTS:
                    critique_result = self._critique(
                        artifact_type, generated_yaml, [str(e)]
                    )
                    continue
                else:
                    raise PlanningError(
                        f"Failed to parse generated {artifact_type} after {self.MAX_REFINEMENTS} refinements",
                        validation_errors=validation_errors,
                    )

            if schema_class:
                try:
                    schema_class(**current_yaml)
                except Exception as e:
                    validation_errors = [str(e)]
                    if iteration < self.MAX_REFINEMENTS:
                        critique_result = self._critique(
                            artifact_type, generated_yaml, [str(e)]
                        )
                        continue
                    else:
                        raise PlanningError(
                            f"Validation failed for {artifact_type} after {self.MAX_REFINEMENTS} refinements",
                            validation_errors=validation_errors,
                        )

            return current_yaml

        raise PlanningError(
            f"Failed to generate valid {artifact_type} after {self.MAX_REFINEMENTS} refinements"
        )

    def _critique(
        self,
        artifact_type: str,
        artifact_yaml: str,
        schema_errors: Optional[list] = None,
    ) -> dict:
        """Generate a critique of the artifact.

        Args:
            artifact_type: Type of artifact
            artifact_yaml: The YAML string to critique
            schema_errors: Optional schema validation errors

        Returns:
            Critique result as dict
        """
        context = {
            "artifact_type": artifact_type,
            "artifact_yaml": artifact_yaml,
            "schema_errors": "\n".join(schema_errors) if schema_errors else "",
        }

        prompt = self.template_loader.render("critique.j2", context)
        generated = self._generate(prompt)

        try:
            return json.loads(generated)
        except json.JSONDecodeError:
            return {"issues": [], "requires_refinement": False}

    def _generate(self, prompt: str) -> str:
        """Generate content using the active OpenCodeClient.

        Must only be called from within a top-level planning method
        (generate_roadmap, decompose_epic) that owns the client context.

        Args:
            prompt: The prompt to send

        Returns:
            Generated text response

        Raises:
            GenerationError: If generation fails
            PlanningError: If called outside an active client context
        """
        if self._client is None:
            raise PlanningError(
                "No active OpenCodeClient — _generate() must be called "
                "from within generate_roadmap() or decompose_epic()"
            )
        return self._client.generate(prompt)

    def _persist_roadmap(self, roadmap: Roadmap) -> None:
        """Persist roadmap to plan directory."""
        roadmap_dir = self.plan_dir / "roadmaps"
        roadmap_dir.mkdir(parents=True, exist_ok=True)
        filepath = roadmap_dir / f"{roadmap.id}.yaml"
        with open(filepath, "w") as f:
            yaml.dump(roadmap.model_dump(by_alias=True), f, default_flow_style=False)

    def _persist_feature(self, feature: Feature) -> None:
        """Persist feature to plan directory."""
        features_dir = self.plan_dir / "features"
        features_dir.mkdir(parents=True, exist_ok=True)
        filepath = features_dir / f"{feature.id}.yaml"
        with open(filepath, "w") as f:
            yaml.dump(feature.model_dump(by_alias=True), f, default_flow_style=False)


# ---------------------------------------------------------------------------
# Module-level helpers (no engine instance required)
# ---------------------------------------------------------------------------

def get_history(project_dir: Path) -> list[dict]:
    """Parse openplan/HISTORY.md and return a list of archive entry dicts.

    Each dict has keys: ``roadmap_id``, ``title``, ``date``, ``note``.
    """
    history_path = Path(project_dir) / "openplan" / "HISTORY.md"
    if not history_path.exists():
        return []

    content = history_path.read_text()
    entries: list[dict] = []

    # Match headings of the form:
    # ## road-map-001 — Some Title (archived 2025-01-01)
    heading_re = re.compile(
        r"^## ([^\s—]+) — (.+?) \(archived (\d{4}-\d{2}-\d{2})\)",
        re.MULTILINE,
    )
    note_re = re.compile(r"\*\*Note:\*\* (.+)", re.MULTILINE)

    # Split on heading boundaries to capture notes per-entry
    sections = re.split(r"(?=^## )", content, flags=re.MULTILINE)
    for section in sections:
        m = heading_re.match(section.strip())
        if not m:
            continue
        roadmap_id = m.group(1)
        title = m.group(2).strip()
        archived_date = m.group(3)
        note_m = note_re.search(section)
        note = note_m.group(1).strip() if note_m else ""
        entries.append(
            {
                "roadmap_id": roadmap_id,
                "title": title,
                "date": archived_date,
                "note": note,
            }
        )

    return entries


def list_archived_roadmaps(project_dir: Path) -> list[str]:
    """Return sorted list of archived roadmap IDs."""
    from openplan.core.archive import ArchiveManager

    manager = ArchiveManager(Path(project_dir))
    return manager.list_archived()
