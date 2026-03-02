import sys
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console
from rich.table import Table

from openplan.core.engine import PlanningEngine, PlanningError
from openplan.core.schemas import Epic, Vision
from openplan.storage import LockedArtifactError, PlanRepository

app = typer.Typer(help="OpenPlan CLI")
console = Console()


@app.command()
def init(
    project_dir: str = typer.Argument(".", help="Project directory to initialize"),
) -> None:
    """Initialize a new OpenPlan project structure."""
    repo = PlanRepository(project_dir)
    repo.init()
    console.print(
        f"[green]Initialized OpenPlan in {Path(project_dir).resolve()}[/green]"
    )
    console.print(
        "[green]Created openplan/ with subdirectories: epics/, features/, campaigns/, adrs/[/green]"
    )


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


if __name__ == "__main__":
    app()
