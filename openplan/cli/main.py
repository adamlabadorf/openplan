import sys
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from openplan.core.engine import PlanningEngine, PlanningError
from openplan.core.schemas import Epic, Feature, Vision
from openplan.core.stabilizer import FeatureStabilizer
from openplan.core.campaign_generator import CampaignGenerator
from openplan.core.adr_generator import ADRGenerator
from openplan.integrations.openspec import ExportError, export_feature
from openplan.storage import LockedArtifactError, PlanRepository

app = typer.Typer(help="OpenPlan CLI")
console = Console()


DEFAULT_MODEL = "ollama/qwen3-coder:30b"


@app.command()
def init(
    project_dir: str = typer.Argument(".", help="Project directory to initialize"),
    model: str = typer.Option(
        DEFAULT_MODEL,
        "--model",
        help="Default OpenCode model for generation (provider/model)",
    ),
) -> None:
    """Initialize a new OpenPlan project structure."""
    import json

    repo = PlanRepository(project_dir)
    repo.init()

    # Write opencode.json so generation calls use the specified model
    opencode_config = {
        "$schema": "https://opencode.ai/config.json",
        "model": model,
        "default_agent": "build",
        "permission": "allow",
    }
    opencode_path = Path(project_dir) / "opencode.json"
    with open(opencode_path, "w") as f:
        json.dump(opencode_config, f, indent=2)

    console.print(
        f"[green]Initialized OpenPlan in {Path(project_dir).resolve()}[/green]"
    )
    console.print(
        "[green]Created openplan/ with subdirectories: epics/, features/, campaigns/, adrs/[/green]"
    )
    console.print(f"[green]Model: {model}[/green]")


@app.command()
def validate(
    all: bool = typer.Option(False, "--all", help="Validate all artifacts"),
    type: Optional[str] = typer.Option(
        None, "--type", help="Artifact type to validate"
    ),
    id: Optional[str] = typer.Option(None, "--id", help="Artifact ID to validate"),
    project_dir: str = typer.Argument(".", help="Project directory"),
) -> None:
    """Validate OpenPlan artifacts."""
    repo = PlanRepository(project_dir)

    if not all and not type:
        console.print("[red]Error: Specify --all or use --type with --id[/red]")
        raise typer.Exit(code=1)

    errors: list[dict] = []

    if all:
        artifact_types = ["vision", "epic", "feature", "campaign", "adr", "roadmap"]
        for artifact_type in artifact_types:
            artifact_ids = repo.list(artifact_type)
            for artifact_id in artifact_ids:
                _validate_artifact(repo, artifact_type, artifact_id, errors)
    elif type and id:
        _validate_artifact(repo, type, id, errors)
    else:
        console.print("[red]Error: When using --type, you must also specify --id[/red]")
        raise typer.Exit(code=1)

    if errors:
        _print_validation_errors(errors)
        raise typer.Exit(code=1)
    else:
        console.print("[green]All artifacts validated successfully![/green]")


def _validate_artifact(
    repo: PlanRepository, artifact_type: str, artifact_id: str, errors: list[dict]
) -> None:
    """Validate a single artifact."""
    try:
        artifact = repo.read(artifact_type, artifact_id, validate=True)
        if artifact is None:
            errors.append(
                {
                    "id": f"{artifact_type}/{artifact_id}",
                    "error": "Artifact not found",
                }
            )
    except Exception as e:
        errors.append(
            {
                "id": f"{artifact_type}/{artifact_id}",
                "error": str(e),
            }
        )


def _print_validation_errors(errors: list[dict]) -> None:
    """Print structured validation errors."""
    table = Table(title="Validation Errors")
    table.add_column("Artifact", style="red")
    table.add_column("Error", style="red")

    for error in errors:
        table.add_row(error["id"], error["error"])

    console.print(table)
    console.print(f"\n[red]Found {len(errors)} error(s)[/red]")


@app.command()
def generate_roadmap(
    vision_file: Optional[str] = typer.Option(
        None, "--vision-file", help="Path to vision YAML file"
    ),
    model: Optional[str] = typer.Option(
        None, "--model", help="Model to use for generation"
    ),
    time_horizon: str = typer.Option(
        "12 months", "--time-horizon", help="Time horizon for roadmap"
    ),
    project_dir: str = typer.Argument(".", help="Project directory"),
) -> None:
    """Generate a roadmap from a vision statement."""
    project_path = Path(project_dir)
    openplan_dir = project_path / "openplan"

    if vision_file is None:
        vision_path = openplan_dir / "visions" / "vision.yaml"
    else:
        vision_path = Path(vision_file)

    if not vision_path.exists():
        console.print(f"[red]Error: Vision file not found: {vision_path}[/red]")
        raise typer.Exit(code=1)

    with open(vision_path) as f:
        vision_data = yaml.safe_load(f)

    vision = Vision(**vision_data)

    try:
        engine = PlanningEngine(
            plan_dir=str(openplan_dir),
            project_dir=str(project_path),
            model=model,
        )
        roadmap = engine.generate_roadmap(
            vision=vision,
            time_horizon=time_horizon,
        )
        console.print(f"[green]Roadmap generated: {roadmap.id}[/green]")
        console.print(
            f"[green]Saved to: {openplan_dir / 'roadmaps' / f'{roadmap.id}.yaml'}[/green]"
        )
    except PlanningError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.validation_errors:
            for err in e.validation_errors:
                console.print(f"  [red]- {err}[/red]")
        raise typer.Exit(code=1)


@app.command()
def decompose_epic(
    epic_id: str = typer.Argument(..., help="Epic ID to decompose"),
    model: Optional[str] = typer.Option(
        None, "--model", help="Model to use for generation"
    ),
    project_dir: str = typer.Argument(".", help="Project directory"),
) -> None:
    """Decompose an epic into features."""
    project_path = Path(project_dir)
    openplan_dir = project_path / "openplan"

    epic_path = openplan_dir / "epics" / f"{epic_id}.yaml"

    if not epic_path.exists():
        console.print(f"[red]Error: Epic not found: {epic_path}[/red]")
        raise typer.Exit(code=1)

    with open(epic_path) as f:
        epic_data = yaml.safe_load(f)

    epic = Epic(**epic_data)

    try:
        engine = PlanningEngine(
            plan_dir=str(openplan_dir),
            project_dir=str(project_path),
            model=model,
        )
        features = engine.decompose_epic(epic=epic)
        console.print(f"[green]Created {len(features)} features:[/green]")
        for feature in features:
            console.print(f"  - {feature.id}: {feature.title}")
    except PlanningError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.validation_errors:
            for err in e.validation_errors:
                console.print(f"  [red]- {err}[/red]")
        raise typer.Exit(code=1)


@app.command()
def stabilize_feature(
    feature_id: str = typer.Argument(..., help="Feature ID to stabilize"),
    model: Optional[str] = typer.Option(
        None, "--model", help="Model to use for generation"
    ),
    project_dir: str = typer.Argument(".", help="Project directory"),
) -> None:
    """Stabilize a feature by expanding vague acceptance criteria."""
    project_path = Path(project_dir)
    openplan_dir = project_path / "openplan"

    feature_path = openplan_dir / "features" / f"{feature_id}.yaml"

    if not feature_path.exists():
        console.print(f"[red]Error: Feature not found: {feature_path}[/red]")
        raise typer.Exit(code=1)

    with open(feature_path) as f:
        feature_data = yaml.safe_load(f)

    feature = Feature(**feature_data)

    try:
        engine = PlanningEngine(
            plan_dir=str(openplan_dir),
            project_dir=str(project_path),
            model=model,
        )
        stabilizer = FeatureStabilizer(engine)
        stabilized = stabilizer.stabilize(feature)
        console.print(f"[green]Feature stabilized: {stabilized.id}[/green]")
        console.print(f"[green]spec_ready: {stabilized.spec_ready}[/green]")
        console.print(
            f"[green]Saved to: {openplan_dir / 'features' / f'{stabilized.id}.yaml'}[/green]"
        )
    except PlanningError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.validation_errors:
            for err in e.validation_errors:
                console.print(f"  [red]- {err}[/red]")
        raise typer.Exit(code=1)


@app.command()
def generate_campaign(
    subsystem: str = typer.Argument(..., help="Subsystem to generate campaign for"),
    debt: Optional[str] = typer.Option(
        None, "--debt", help="Technical debt description"
    ),
    model: Optional[str] = typer.Option(
        None, "--model", help="Model to use for generation"
    ),
    project_dir: str = typer.Argument(".", help="Project directory"),
) -> None:
    """Generate a campaign for technical debt remediation."""
    project_path = Path(project_dir)
    openplan_dir = project_path / "openplan"

    try:
        engine = PlanningEngine(
            plan_dir=str(openplan_dir),
            project_dir=str(project_path),
            model=model,
        )
        generator = CampaignGenerator(engine)
        campaign = generator.generate(
            subsystem=subsystem,
            technical_debt=debt or "",
        )
        console.print(f"[green]Campaign generated: {campaign.id}[/green]")
        console.print(
            f"[green]Saved to: {openplan_dir / 'campaigns' / f'{campaign.id}.yaml'}[/green]"
        )
    except PlanningError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.validation_errors:
            for err in e.validation_errors:
                console.print(f"  [red]- {err}[/red]")
        raise typer.Exit(code=1)


@app.command()
def generate_adr(
    context: Optional[str] = typer.Option(None, "--context", help="Decision context"),
    alternatives: Optional[str] = typer.Option(
        None, "--alternatives", help="Alternatives considered"
    ),
    model: Optional[str] = typer.Option(
        None, "--model", help="Model to use for generation"
    ),
    project_dir: str = typer.Argument(".", help="Project directory"),
) -> None:
    """Generate an Architecture Decision Record (ADR)."""
    project_path = Path(project_dir)
    openplan_dir = project_path / "openplan"

    try:
        engine = PlanningEngine(
            plan_dir=str(openplan_dir),
            project_dir=str(project_path),
            model=model,
        )
        generator = ADRGenerator(engine)
        adr = generator.generate(
            decision_context=context or "",
            alternatives=alternatives or "",
        )
        console.print(f"[green]ADR generated: {adr.id}[/green]")
        console.print(
            f"[green]Saved to: {openplan_dir / 'adrs' / f'{adr.id}.yaml'}[/green]"
        )
    except PlanningError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        if e.validation_errors:
            for err in e.validation_errors:
                console.print(f"  [red]- {err}[/red]")
        raise typer.Exit(code=1)


@app.command()
def export_to_openspec(
    feature_id: str = typer.Argument(..., help="Feature ID to export"),
    openspec_dir: Optional[str] = typer.Option(
        None, "--openspec-dir", help="OpenSpec directory path"
    ),
    arch_context: Optional[str] = typer.Option(
        "", "--arch-context", help="Architectural context for the feature"
    ),
    project_dir: str = typer.Argument(".", help="Project directory"),
) -> None:
    """Export a spec-ready feature to OpenSpec."""
    project_path = Path(project_dir)
    openplan_dir = project_path / "openplan"

    feature_path = openplan_dir / "features" / f"{feature_id}.yaml"

    if not feature_path.exists():
        console.print(f"[red]Error: Feature not found: {feature_path}[/red]")
        raise typer.Exit(code=1)

    with open(feature_path) as f:
        feature_data = yaml.safe_load(f)

    feature = Feature(**feature_data)

    if openspec_dir is None:
        openspec_path = project_path / "openspec"
    else:
        openspec_path = Path(openspec_dir)

    if not openspec_path.exists():
        console.print(
            f"[red]Error: OpenSpec directory not found: {openspec_path}[/red]"
        )
        raise typer.Exit(code=1)

    try:
        export_feature(feature, openspec_path, arch_context or "")
        console.print(f"[green]Feature '{feature_id}' exported to OpenSpec[/green]")
        console.print(
            f"[green]Change created in: {openspec_path / 'changes' / feature_id}[/green]"
        )
    except ExportError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)


@app.command()
def status(
    project_dir: str = typer.Argument(".", help="Project directory"),
) -> None:
    """Show the current status of the OpenPlan project."""
    project_path = Path(project_dir)
    openplan_dir = project_path / "openplan"

    if not openplan_dir.exists():
        console.print(
            "[red]Error: Not an OpenPlan project. Run 'openplan init' first.[/red]"
        )
        raise typer.Exit(code=1)

    repo = PlanRepository(project_dir)

    vision_loaded = False
    vision_ids = repo.list("vision")
    if vision_ids:
        vision = repo.read("vision", vision_ids[0])
        if vision:
            vision_loaded = True

    roadmap_ids = repo.list("roadmap")
    roadmap_count = len(roadmap_ids)

    epic_count = len(repo.list("epic"))

    feature_ids = repo.list("feature")
    from openplan.core.schemas import Feature as FeatureModel

    feature_count = len(feature_ids)
    spec_ready_count = 0
    for fid in feature_ids:
        f = repo.read("feature", fid)
        if f:
            feature = FeatureModel(**f.model_dump())
            if feature.spec_ready:
                spec_ready_count += 1

    campaign_count = len(repo.list("campaign"))
    adr_count = len(repo.list("adr"))

    locked_artifacts = []
    for artifact_type in ["vision", "epic", "feature", "campaign", "adr", "roadmap"]:
        for artifact_id in repo.list(artifact_type):
            if repo.is_locked(artifact_type, artifact_id):
                locked_artifacts.append(f"{artifact_type}/{artifact_id}")

    console.print("\n[bold]OpenPlan Status[/bold]")
    console.print(f"Vision loaded:      {'Yes' if vision_loaded else 'No'}")
    console.print(f"Roadmaps:           {roadmap_count}")
    console.print(f"Epics:              {epic_count}")
    console.print(
        f"Features:           {feature_count} total, {spec_ready_count} spec_ready"
    )
    console.print(f"Campaigns:          {campaign_count}")
    console.print(f"ADRs:               {adr_count}")

    if locked_artifacts:
        console.print(f"\n[yellow]Locked artifacts:[/yellow]")
        for artifact in locked_artifacts:
            console.print(f"  - {artifact}")
    else:
        console.print("\n[green]No locked artifacts[/green]")


if __name__ == "__main__":
    app()
