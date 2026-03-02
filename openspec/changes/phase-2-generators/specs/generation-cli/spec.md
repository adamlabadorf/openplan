## ADDED Requirements

### Requirement: Generate roadmap CLI command
The system SHALL provide a `generate-roadmap` CLI command.

#### Scenario: Default vision file location
- **WHEN** `openplan generate-roadmap` is run without arguments
- **THEN** it SHALL load vision.yaml from openplan/ directory
- **AND** SHALL run the planning engine
- **AND** SHALL save roadmap.yaml to openplan/ directory

#### Scenario: Custom vision file
- **WHEN** `openplan generate-roadmap --vision-file PATH` is run
- **THEN** it SHALL load vision from the specified PATH
- **AND** SHALL use that vision for roadmap generation

#### Scenario: Custom model
- **WHEN** `openplan generate-roadmap --model MODEL` is run
- **THEN** it SHALL use the specified model for generation

#### Scenario: Custom time horizon
- **WHEN** `openplan generate-roadmap --time-horizon TEXT` is run
- **THEN** it SHALL pass the time horizon to the roadmap template

### Requirement: Decompose epic CLI command
The system SHALL provide a `decompose-epic` CLI command.

#### Scenario: Decompose by epic ID
- **WHEN** `openplan decompose-epic EPIC_ID` is run
- **THEN** it SHALL load the epic from openplan/epics/ directory
- **AND** SHALL run the planning engine to decompose
- **AND** SHALL save each feature YAML to openplan/features/ directory
- **AND** SHALL return the list of created features

#### Scenario: Custom model for decomposition
- **WHEN** `openplan decompose-epic EPIC_ID --model MODEL` is run
- **THEN** it SHALL use the specified model for generation

### Requirement: CLI integration with existing main
The system SHALL integrate new commands into the existing CLI main module.

#### Scenario: Commands available
- **WHEN** `openplan --help` is run
- **THEN** it SHALL show generate-roadmap and decompose-epic commands
- **AND** each SHALL show appropriate help text
