## ADDED Requirements

### Requirement: generate-adr CLI command exists
The system SHALL provide a CLI command `openplan generate-adr [--context TEXT] [--model MODEL]`.

#### Scenario: generate-adr command
- **WHEN** user runs `openplan generate-adr`
- **THEN** an ADR is generated and persisted

### Requirement: Context option
The system SHALL accept an optional --context flag for decision context.

#### Scenario: With context flag
- **WHEN** user runs `openplan generate-adr --context "We need to choose auth method"`
- **THEN** the context is passed to the generator

### Requirement: Model option
The system SHALL accept an optional --model flag to specify the LLM model.

#### Scenario: With model flag
- **WHEN** user runs `openplan generate-adr --model gpt-4`
- **THEN** the specified model is used for generation

### Requirement: Alternatives from input
The system SHALL accept alternatives either via prompt or flags.

#### Scenario: With alternatives
- **WHEN** user provides alternatives via flags or prompt
- **THEN** they are included in the ADR generation
