## ADDED Requirements

### Requirement: feature_to_openspec_input returns dict
The adapter SHALL provide a function `feature_to_openspec_input(feature: Feature, arch_context: str = "") -> dict` that returns a dictionary with keys: goal, acceptance_criteria, constraints, and architectural_context.

#### Scenario: Basic feature conversion
- **WHEN** `feature_to_openspec_input` is called with a valid Feature object
- **THEN** it returns a dict with goal, acceptance_criteria, constraints, and architectural_context keys

#### Scenario: Feature with architectural context
- **WHEN** `feature_to_openspec_input` is called with arch_context parameter
- **THEN** the returned dict includes the architectural context in the architectural_context field

### Requirement: export_feature validates spec_ready
The function `export_feature(feature: Feature, openspec_dir: Path, arch_context: str = "") -> Path` SHALL raise `ExportError` if feature.spec_ready is False.

#### Scenario: Export blocked for non-spec-ready feature
- **WHEN** `export_feature` is called with a feature where spec_ready is False
- **THEN** it raises ExportError with message indicating feature is not spec_ready

#### Scenario: Export allowed for spec-ready feature
- **WHEN** `export_feature` is called with a feature where spec_ready is True
- **THEN** it proceeds to create the OpenSpec change

### Requirement: export_feature validates openspec CLI
The `export_feature` function SHALL raise `ExportError` if the openspec CLI is not found on the system.

#### Scenario: openspec CLI not found
- **WHEN** `export_feature` is called and openspec CLI is not installed
- **THEN** it raises ExportError with message indicating openspec CLI not found

### Requirement: export_feature creates change via subprocess
The `export_feature` function SHALL call `openspec new change <feature.id>` via subprocess to create the change directory.

#### Scenario: Successful change creation
- **WHEN** `export_feature` is called with valid inputs and openspec CLI is available
- **THEN** it creates the change in openspec_dir and returns the Path to the created change

### Requirement: export_feature writes change proposal file
After creating the change, `export_feature` SHALL write the OpenSpec input to the change proposal file.

#### Scenario: Proposal file written
- **WHEN** export_feature successfully creates the change
- **THEN** it writes the feature data to the proposal file in the change directory

### Requirement: ExportError is distinct exception class
The system SHALL define `ExportError` as a distinct exception class in `openplan/integrations/openspec.py`.

#### Scenario: ExportError is catchable
- **WHEN** code catches ExportError
- **THEN** it catches only export-related errors, not other exceptions

### Requirement: export-to-openspec CLI command exists
The CLI SHALL provide `openplan export-to-openspec FEATURE_ID [--openspec-dir PATH] [--arch-context TEXT]` command.

#### Scenario: CLI command exports feature
- **WHEN** user runs `openplan export-to-openspec my-feature`
- **THEN** it loads the feature, validates spec_ready, calls export_feature, and prints the created change path

#### Scenario: CLI command missing feature_id
- **WHEN** user runs `openplan export-to-openspec` without FEATURE_ID
- **THEN** it shows an error about missing required argument
