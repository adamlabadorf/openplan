## ADDED Requirements

### Requirement: generate-campaign CLI command exists
The system SHALL provide a CLI command `openplan generate-campaign SUBSYSTEM [--debt TEXT] [--model MODEL]`.

#### Scenario: generate-campaign command
- **WHEN** user runs `openplan generate-campaign auth --debt "outdated token handling"`
- **THEN** a campaign is generated and persisted

### Requirement: Subsystem required
The system SHALL require a SUBSYSTEM argument.

#### Scenario: Missing subsystem
- **WHEN** user runs `openplan generate-campaign` without subsystem
- **THEN** an error is displayed

### Requirement: Debt option
The system SHALL accept an optional --debt flag for technical debt description.

#### Scenario: With debt flag
- **WHEN** user runs `openplan generate-campaign auth --debt "outdated tokens"`
- **THEN** the debt description is passed to the generator

### Requirement: Model option
The system SHALL accept an optional --model flag to specify the LLM model.

#### Scenario: With model flag
- **WHEN** user runs `openplan generate-campaign auth --model gpt-4`
- **THEN** the specified model is used for generation
