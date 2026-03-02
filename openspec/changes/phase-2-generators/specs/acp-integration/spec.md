## ADDED Requirements

### Requirement: ACP Client Wrapper
The system SHALL provide a thin wrapper around ACPClient that enables AI code generation through OpenCode.

#### Scenario: Context manager usage
- **WHEN** code uses `OpenCodeClient` as a context manager
- **THEN** it SHALL provide access to the `generate()` method
- **AND** SHALL automatically clean up resources on exit

#### Scenario: Generate method returns text
- **WHEN** `generate(prompt: str)` is called with a prompt string
- **THEN** it SHALL return the reply text as a string
- **AND** SHALL use `permission="allow"` for all requests

#### Scenario: Generation failure raises error
- **WHEN** ACP client fails to generate a response
- **THEN** it SHALL raise a `GenerationError` exception
- **AND** the error SHALL include failure details

### Requirement: OpenCodeClient Constructor
The system SHALL accept project directory and optional model/agent parameters.

#### Scenario: Default agent configuration
- **WHEN** `OpenCodeClient` is created without agent parameter
- **THEN** it SHALL default to `agent="build"`

#### Scenario: Custom model override
- **WHEN** `OpenCodeClient` is created with model parameter
- **THEN** it SHALL use the specified model for generation
