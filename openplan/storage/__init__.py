"""Storage module for OpenPlan."""

from openplan.storage.repository import LockedArtifactError, PlanRepository

__all__ = ["PlanRepository", "LockedArtifactError"]
