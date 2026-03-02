from pathlib import Path
from typing import Any, Optional, Type, TypeVar, cast

import yaml
from pydantic import BaseModel

from openplan.core.schemas import (
    ADR,
    Campaign,
    Epic,
    Feature,
    PlanState,
    Roadmap,
    Vision,
)

T = TypeVar("T", bound=BaseModel)

ARTIFACT_TYPE_MAP: dict[str, Type[BaseModel]] = {
    "vision": Vision,
    "epic": Epic,
    "feature": Feature,
    "campaign": Campaign,
    "adr": ADR,
    "roadmap": Roadmap,
}


class LockedArtifactError(Exception):
    """Raised when attempting to write to a locked artifact."""

    pass


class PlanRepository:
    """Repository for managing planning artifacts."""

    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.openplan_dir = self.project_dir / "openplan"

    def init(self) -> None:
        """Initialize the project structure."""
        subdirs = ["epics", "features", "campaigns", "adrs", "visions"]
        for subdir in subdirs:
            (self.openplan_dir / subdir).mkdir(parents=True, exist_ok=True)

    def _get_artifact_dir(self, artifact_type: str) -> Path:
        """Get the directory for an artifact type."""
        return self.openplan_dir / f"{artifact_type}s"

    def _get_artifact_path(self, artifact_type: str, artifact_id: str) -> Path:
        """Get the path for an artifact file."""
        return self._get_artifact_dir(artifact_type) / f"{artifact_id}.yaml"

    def _get_lock_path(self, artifact_type: str, artifact_id: str) -> Path:
        """Get the path for the lock file."""
        return self._get_artifact_path(artifact_type, artifact_id).with_suffix(
            ".yaml.locked"
        )

    def lock(self, artifact_type: str, artifact_id: str) -> None:
        """Lock an artifact to prevent concurrent writes."""
        lock_path = self._get_lock_path(artifact_type, artifact_id)
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.touch()

    def is_locked(self, artifact_type: str, artifact_id: str) -> bool:
        """Check if an artifact is locked."""
        lock_path = self._get_lock_path(artifact_type, artifact_id)
        return lock_path.exists()

    def write(self, artifact: BaseModel) -> None:
        """Write an artifact to YAML with snake_case keys."""
        artifact_type = artifact.__class__.__name__.lower()
        artifact_id = artifact.model_dump()["id"]

        if self.is_locked(artifact_type, artifact_id):
            raise LockedArtifactError(
                f"Artifact {artifact_type}/{artifact_id} is locked"
            )

        artifact_path = self._get_artifact_path(artifact_type, artifact_id)
        artifact_path.parent.mkdir(parents=True, exist_ok=True)

        with open(artifact_path, "w") as f:
            yaml.dump(
                artifact.model_dump(by_alias=True),
                f,
                default_flow_style=False,
                sort_keys=False,
            )

    def read(
        self, artifact_type: str, artifact_id: str, validate: bool = True
    ) -> Optional[BaseModel]:
        """Read and validate an artifact."""
        artifact_path = self._get_artifact_path(artifact_type, artifact_id)

        if not artifact_path.exists():
            return None

        with open(artifact_path) as f:
            data = yaml.safe_load(f)

        if validate:
            model_class = ARTIFACT_TYPE_MAP.get(artifact_type)
            if model_class:
                return model_class(**data)

        return data

    def list(self, artifact_type: str) -> list[str]:
        """List all artifact IDs of a given type."""
        artifact_dir = self._get_artifact_dir(artifact_type)

        if not artifact_dir.exists():
            return []

        ids = []
        for f in artifact_dir.glob("*.yaml"):
            if not f.name.endswith(".locked"):
                ids.append(f.stem)

        return sorted(ids)

    def read_state(self) -> PlanState:
        """Read the full plan state from all artifacts."""
        state = PlanState()

        vision_ids = self.list("vision")
        if vision_ids:
            state.vision = cast(Vision, self.read("vision", vision_ids[0]))

        roadmap_ids = self.list("roadmap")
        if roadmap_ids:
            state.roadmap = cast(Roadmap, self.read("roadmap", roadmap_ids[0]))

        for epic_id in self.list("epic"):
            epic = self.read("epic", epic_id)
            if epic:
                state.epics.append(cast(Epic, epic))

        for feature_id in self.list("feature"):
            feature = self.read("feature", feature_id)
            if feature:
                state.features.append(cast(Feature, feature))

        for campaign_id in self.list("campaign"):
            campaign = self.read("campaign", campaign_id)
            if campaign:
                state.campaigns.append(cast(Campaign, campaign))

        for adr_id in self.list("adr"):
            adr = self.read("adr", adr_id)
            if adr:
                state.adrs.append(cast(ADR, adr))

        return state
