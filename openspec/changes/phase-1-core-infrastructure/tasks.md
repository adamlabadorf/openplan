## 1. Project Setup

- [x] 1.1 Create pyproject.toml with uv, pydantic>=2.0, jinja2, typer, pyyaml
- [x] 1.2 Set up standard Python package layout under openplan/
- [x] 1.3 Configure pytest in pyproject.toml
- [x] 1.4 Verify package installs correctly with uv

## 2. Pydantic v2 Schemas

- [x] 2.1 Create openplan/core/schemas.py with base models (SuccessMetric, Risk, ArchitecturalImpact)
- [x] 2.2 Implement Vision model with validators (at least 1 metric, reject vague phrases)
- [x] 2.3 Implement Epic model with validators (at least 1 metric, at least 1 arch impact, max 10 features)
- [x] 2.4 Implement Feature model with validators (acceptance_criteria 3-15, no empty criteria, no circular deps)
- [x] 2.5 Implement Campaign model with validators (rollback_strategy required, at least 2 phases)
- [x] 2.6 Implement ADR model
- [x] 2.7 Implement Roadmap model with validator (max 8 epics)
- [x] 2.8 Implement PlanState as top-level envelope

## 3. Storage Layer

- [x] 3.1 Create openplan/storage/repository.py
- [x] 3.2 Implement PlanRepository.init() method
- [x] 3.3 Implement PlanRepository.write() with locking
- [x] 3.4 Implement PlanRepository.read() with validation
- [x] 3.5 Implement PlanRepository.lock() and is_locked()
- [x] 3.6 Implement PlanRepository.list()
- [x] 3.7 Define LockedArtifactError exception

## 4. CLI Commands

- [x] 4.1 Create openplan/cli/main.py with Typer
- [x] 4.2 Implement openplan init command
- [x] 4.3 Implement openplan validate command with --all, --type, --id options
- [x] 4.4 Add structured error output for validation failures

## 5. Tests

- [x] 5.1 Create tests/ directory structure
- [x] 5.2 Write unit tests for Vision validators (vague phrase rejection, metrics requirement)
- [x] 5.3 Write unit tests for Epic validators (size bounds, required fields)
- [x] 5.4 Write unit tests for Feature validators (criteria bounds, non-empty)
- [x] 5.5 Write unit tests for Campaign validators (rollback, phases)
- [x] 5.6 Write unit tests for Roadmap validators (max epics)
- [x] 5.7 Write unit tests for PlanRepository (init, write, read, lock, list)
- [x] 5.8 Write unit tests for CLI commands using Typer test client

## 6. Integration

- [x] 6.1 Verify all tests pass
- [x] 6.2 Test init command in clean directory
- [x] 6.3 Test validate command with sample artifacts
- [x] 6.4 Verify YAML output uses snake_case keys
