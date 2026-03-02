## ADDED Requirements

### Requirement: PlanningEngine initialization
The system SHALL provide a PlanningEngine class with plan_dir and project_dir parameters.

#### Scenario: Engine initialization
- **WHEN** PlanningEngine is instantiated with plan_dir and project_dir
- **THEN** it SHALL store these paths for later use
- **AND** SHALL accept optional model parameter

### Requirement: Generate roadmap method
The system SHALL provide a `generate_roadmap()` method that creates a roadmap from a Vision.

#### Scenario: Roadmap generation happy path
- **WHEN** `generate_roadmap(vision: Vision)` is called with valid Vision
- **THEN** it SHALL render the roadmap template
- **AND** SHALL generate via OpenCodeClient
- **AND** SHALL parse the returned YAML
- **AND** SHALL validate using Pydantic models
- **AND** SHALL persist roadmap.yaml to openplan/ directory
- **AND** SHALL return the validated Roadmap object

#### Scenario: Roadmap validation failure triggers refinement
- **WHEN** generate_roadmap() receives invalid YAML from generation
- **THEN** it SHALL invoke critique template
- **AND** SHALL invoke refine template with critique
- **AND** SHALL re-validate the refined output
- **AND** SHALL repeat up to 2 times

#### Scenario: Max refinements exceeded raises error
- **WHEN** generate_roadmap() fails validation after 2 refinement attempts
- **THEN** it SHALL raise a PlanningError with details
- **AND** the error SHALL include validation failure information

### Requirement: Decompose epic method
The system SHALL provide a `decompose_epic()` method that breaks epics into features.

#### Scenario: Epic decomposition happy path
- **WHEN** `decompose_epic(epic: Epic, arch_summary: str = "")` is called
- **THEN** it SHALL render the epic template
- **AND** SHALL generate via OpenCodeClient
- **AND** SHALL parse the returned YAML as Feature list
- **AND** SHALL validate each feature using Pydantic models
- **AND** SHALL persist each feature YAML to openplan/features/ directory
- **AND** SHALL return the list of validated Feature objects

#### Scenario: Epic validation failure triggers refinement
- **WHEN** decompose_epic() receives invalid YAML from generation
- **THEN** it SHALL invoke critique and refine templates
- **AND** SHALL repeat up to 2 times

#### Scenario: Max refinements exceeded raises error
- **WHEN** decompose_epic() fails validation after 2 refinement attempts
- **THEN** it SHALL raise a PlanningError with details

### Requirement: Engine delegates to OpenCodeClient
The system SHALL ensure the engine NEVER calls OpenCode directly.

#### Scenario: Engine uses wrapper
- **WHEN** PlanningEngine needs to generate content
- **THEN** it SHALL use OpenCodeClient.generate() method only
- **AND** SHALL NOT instantiate or call ACPClient directly
