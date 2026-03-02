## ADDED Requirements

### Requirement: Schema validator tests
The system SHALL include unit tests for all schema validators.

#### Scenario: Vision validator rejects vague phrases
- **WHEN** Vision with vague phrases is validated
- **THEN** it SHALL fail with appropriate error

#### Scenario: Vision validator requires metrics
- **WHEN** Vision with empty success_metrics is validated
- **THEN** it SHALL fail

#### Scenario: Epic validator enforces size bounds
- **WHEN** Epic with more than 10 features is validated
- **THEN** it SHALL fail

#### Scenario: Feature validator checks criteria bounds
- **WHEN** Feature with acceptance_criteria outside [3, 15] is validated
- **THEN** it SHALL fail

#### Scenario: Campaign validator requires rollback
- **WHEN** Campaign with empty rollback_strategy is validated
- **THEN** it SHALL fail

#### Scenario: Roadmap validator limits epics
- **WHEN** Roadmap with more than 8 epics is validated
- **THEN** it SHALL fail

### Requirement: PlanRepository tests
The system SHALL include unit tests for PlanRepository operations.

#### Scenario: Init creates correct structure
- **WHEN** PlanRepository.init() is tested
- **THEN** it SHALL create all required subdirectories

#### Scenario: Write and read round-trip
- **WHEN** artifact is written and then read
- **THEN** the result SHALL match the original

#### Scenario: Lock prevents write
- **WHEN** locked artifact write is attempted
- **THEN** it SHALL raise LockedArtifactError

#### Scenario: List returns correct IDs
- **WHEN** artifacts exist and list() is called
- **THEN** it SHALL return all artifact IDs

### Requirement: CLI command tests
The system SHALL include unit tests for CLI commands using Typer test client.

#### Scenario: Init command succeeds
- **WHEN** init command is invoked via test client
- **THEN** it SHALL complete without error

#### Scenario: Validate command reports errors
- **WHEN** validate command runs on invalid artifacts
- **THEN** it SHALL report structured errors
