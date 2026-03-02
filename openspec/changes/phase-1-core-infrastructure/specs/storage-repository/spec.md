## ADDED Requirements

### Requirement: PlanRepository initialization
The system SHALL provide a PlanRepository class that initializes a project structure.

#### Scenario: Init creates correct directory structure
- **WHEN** PlanRepository.init(project_dir) is called
- **THEN** it SHALL create openplan/ with subdirectories: epics/, features/, campaigns/, adrs/

### Requirement: Write artifacts to YAML
The system SHALL save artifacts as YAML files with snake_case keys.

#### Scenario: Write succeeds for valid artifact
- **WHEN** PlanRepository.write(artifact) is called with a valid artifact
- **THEN** it SHALL save the artifact as YAML in the appropriate subdirectory

#### Scenario: Write refuses locked artifact
- **WHEN** PlanRepository.write(artifact) is called for a locked artifact
- **THEN** it SHALL raise LockedArtifactError

### Requirement: Read and validate artifacts
The system SHALL load artifacts and validate them against schemas.

#### Scenario: Read returns validated artifact
- **WHEN** PlanRepository.read(artifact_type, id) is called
- **THEN** it SHALL return a validated Pydantic model

### Requirement: Lock mechanism
The system SHALL provide locking to prevent concurrent writes.

#### Scenario: Lock creates marker file
- **WHEN** PlanRepository.lock(artifact_type, id) is called
- **THEN** it SHALL create a .locked marker file alongside the artifact

#### Scenario: Is locked returns correct status
- **WHEN** PlanRepository.is_locked(artifact_type, id) is called
- **THEN** it SHALL return True if .locked exists, False otherwise

### Requirement: List artifacts
The system SHALL provide listing of artifact IDs by type.

#### Scenario: List returns all IDs
- **WHEN** PlanRepository.list(artifact_type) is called
- **THEN** it SHALL return a list of all artifact IDs of that type
