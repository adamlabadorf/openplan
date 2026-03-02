## Why

OpenPlan needs a deterministic planning harness that drives OpenSpec/OpenCode via prompt templates. Currently there's no foundational scaffolding to manage plans, schemas, and artifacts in a structured way. Building Phase 1 establishes the core infrastructure needed to support future planning features.

## What Changes

- **New**: `pyproject.toml` with uv, pydantic>=2.0, jinja2, typer, pyyaml
- **New**: Standard Python package layout under `openplan/`
- **New**: Pydantic v2 schemas for all planning artifacts (Vision, Epic, Feature, Campaign, ADR, Roadmap, PlanState)
- **New**: Storage layer with PlanRepository for YAML persistence and locking
- **New**: CLI with `init` and `validate` commands using Typer
- **New**: Unit tests for schemas, storage, and CLI

## Capabilities

### New Capabilities

- `core-schemas`: Pydantic v2 models for all planning artifacts with validators
- `storage-repository`: PlanRepository class for YAML CRUD operations with locking
- `cli-commands`: Typer-based CLI with init and validate commands
- `test-suite`: Unit tests for validators, storage, and CLI

### Modified Capabilities

- (none - this is foundational infrastructure)

## Impact

- New `openplan/` Python package with core/, storage/, cli/ modules
- New `tests/` directory with unit tests
- YAML file format uses snake_case keys throughout
