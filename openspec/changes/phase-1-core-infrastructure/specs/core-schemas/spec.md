## ADDED Requirements

### Requirement: Pydantic v2 schemas for all planning artifacts
The system SHALL provide Pydantic v2 models for all planning artifact types: Vision, Epic, Feature, Campaign, ADR, Roadmap, and PlanState.

#### Scenario: Vision schema validates success metrics
- **WHEN** a Vision is created with zero success_metrics
- **THEN** validation SHALL fail with at least one error

#### Scenario: Vision rejects vague phrases
- **WHEN** a Vision contains "improve", "enhance", "optimize" without a metric, "refactor" without target, or "better"
- **THEN** validation SHALL fail

#### Scenario: Epic validates feature count
- **WHEN** an Epic is created with more than 10 features
- **THEN** validation SHALL fail

#### Scenario: Epic requires at least one metric and arch impact
- **WHEN** an Epic is created with zero success_metrics or zero architectural_impact
- **THEN** validation SHALL fail

#### Scenario: Feature validates acceptance criteria bounds
- **WHEN** a Feature is created with acceptance_criteria outside [3, 15] range
- **THEN** validation SHALL fail

#### Scenario: Feature requires non-empty criteria
- **WHEN** a Feature has an empty acceptance criterion in the list
- **THEN** validation SHALL fail

#### Scenario: Campaign requires rollback strategy
- **WHEN** a Campaign is created with empty rollback_strategy
- **THEN** validation SHALL fail

#### Scenario: Campaign requires minimum phases
- **WHEN** a Campaign is created with fewer than 2 phases
- **THEN** validation SHALL fail

#### Scenario: Roadmap limits epics
- **WHEN** a Roadmap is created with more than 8 epics
- **THEN** validation SHALL fail
