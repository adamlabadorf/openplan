import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

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


if __name__ == "__main__":
    app()
