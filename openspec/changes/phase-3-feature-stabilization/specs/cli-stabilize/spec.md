## ADDED Requirements

### Requirement: stabilize-feature CLI command exists
The system SHALL provide a CLI command `openplan stabilize-feature FEATURE_ID [--model MODEL]`.

#### Scenario: stabilize-feature command
- **WHEN** user runs `openplan stabilize-feature feature-123`
- **THEN** the feature is processed through FeatureStabilizer

### Requirement: Model option
The system SHALL accept an optional --model flag to specify the LLM model.

#### Scenario: With model flag
- **WHEN** user runs `openplan stabilize-feature feature-123 --model gpt-4`
- **THEN** the specified model is used for generation

### Requirement: Typer test client support
The system SHALL support testing the CLI using Typer's test client.

#### Scenario: CLI test client
- **WHEN** using Typer's test client
- **THEN** commands are callable without subprocess
