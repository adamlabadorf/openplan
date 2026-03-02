## ADDED Requirements

### Requirement: openplan init command
The system SHALL provide an init command that creates the openplan/ directory structure.

#### Scenario: Init creates structure in current directory
- **WHEN** `openplan init` is run in a directory
- **THEN** it SHALL create openplan/ with subdirectories epics/, features/, campaigns/, adrs/

#### Scenario: Init confirms creation
- **WHEN** `openplan init` is run successfully
- **THEN** it SHALL print confirmation message

### Requirement: openplan validate command
The system SHALL provide a validate command to check artifact schemas.

#### Scenario: Validate all artifacts
- **WHEN** `openplan validate --all` is run
- **THEN** it SHALL load and validate all artifacts, printing any errors

#### Scenario: Validate specific type
- **WHEN** `openplan validate --type epic --id my-epic` is run
- **THEN** it SHALL load and validate only that specific artifact

#### Scenario: Validate reports structured errors
- **WHEN** validation fails for one or more artifacts
- **THEN** it SHALL print structured error messages with artifact ID and error details
