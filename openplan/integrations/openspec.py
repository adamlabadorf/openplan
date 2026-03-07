"""OpenSpec integration for exporting features."""

import shutil
import subprocess
from pathlib import Path
from typing import Optional

from openplan.core.schemas import Feature


class ExportError(Exception):
    """Raised when export to OpenSpec is blocked or fails."""

    pass


def feature_to_openspec_input(feature: Feature, arch_context: str = "") -> dict:
    """
    Convert a Feature to OpenSpec input format.

    Args:
        feature: The feature to convert
        arch_context: Optional architectural context to include

    Returns:
        Dictionary with goal, acceptance_criteria, constraints, architectural_context
    """
    constraints = []
    if feature.dependencies:
        constraints.append(f"Depends on: {', '.join(feature.dependencies)}")
    if feature.complexity:
        constraints.append(f"Complexity: {feature.complexity}")

    return {
        "goal": f"{feature.title}: {feature.description}",
        "acceptance_criteria": feature.acceptance_criteria,
        "constraints": constraints,
        "architectural_context": arch_context,
    }


def _check_openspec_available() -> bool:
    """Check if openspec CLI is available."""
    return shutil.which("openspec") is not None


def export_feature(
    feature: Feature,
    openspec_dir: Path,
    arch_context: str = "",
) -> Path:
    """
    Export a feature to OpenSpec as a new change.

    Args:
        feature: The feature to export (must have spec_ready=True)
        openspec_dir: Directory to run openspec CLI in
        arch_context: Optional architectural context

    Returns:
        Path to the created change

    Raises:
        ExportError: If spec_ready=False or openspec CLI not available
    """
    if not feature.spec_ready:
        raise ExportError(
            f"Cannot export feature '{feature.id}': spec_ready=False. "
            "Feature must be stabilized before export."
        )

    if not _check_openspec_available():
        raise ExportError(
            "OpenSpec CLI not found. Please install openspec CLI: npm install -g @openspec/cli"
        )

    openspec_input = feature_to_openspec_input(feature, arch_context)

    # If the change already exists, remove it so we can recreate with fresh content
    change_path = openspec_dir / "openspec" / "changes" / feature.id
    if change_path.exists():
        shutil.rmtree(change_path)

    result = subprocess.run(
        ["openspec", "new", "change", feature.id],
        cwd=str(openspec_dir),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise ExportError(
            f"Failed to export feature '{feature.id}' to OpenSpec: {result.stderr}"
        )
    proposal_file = change_path / "proposal.md"

    proposal_content = f"""# {feature.title}

## Goal
{openspec_input["goal"]}

## Acceptance Criteria
"""
    for criterion in openspec_input["acceptance_criteria"]:
        proposal_content += f"- {criterion}\n"

    if openspec_input["constraints"]:
        proposal_content += "\n## Constraints\n"
        for constraint in openspec_input["constraints"]:
            proposal_content += f"- {constraint}\n"

    if openspec_input["architectural_context"]:
        proposal_content += (
            f"\n## Architectural Context\n{openspec_input['architectural_context']}\n"
        )

    proposal_file.write_text(proposal_content)

    return change_path
