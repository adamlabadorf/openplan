## ADDED Requirements

### Requirement: FeatureStabilizer class exists
The system SHALL provide a FeatureStabilizer class in openplan/core/stabilizer.py that accepts a PlanningEngine instance.

#### Scenario: FeatureStabilizer initialization
- **WHEN** FeatureStabilizer is instantiated with a PlanningEngine
- **THEN** it stores the engine reference for later use

### Requirement: Stabilize expands acceptance criteria
The system SHALL send a feature through a stabilization prompt that expands vague acceptance criteria into specific, testable requirements.

#### Scenario: Stabilize with vague criteria
- **WHEN** stabilize is called with a feature containing vague criteria like "user friendly"
- **THEN** the output contains expanded criteria like "user can complete X in under Y clicks"

### Requirement: Minimum 3 testable criteria
The system SHALL ensure each stabilized feature has at least 3 independently testable acceptance criteria.

#### Scenario: Feature with insufficient criteria
- **WHEN** stabilize is called with a feature having fewer than 3 testable criteria
- **THEN** the output expands to include at least 3 testable criteria

### Requirement: spec_ready flag
The system SHALL set spec_ready=True on the feature only after successful Pydantic validation.

#### Scenario: Valid feature stabilization
- **WHEN** stabilize is called with a valid feature
- **THEN** the returned feature has spec_ready=True

#### Scenario: Invalid feature stabilization
- **WHEN** stabilize is called with an invalid feature that fails validation
- **THEN** the returned feature has spec_ready=False

### Requirement: Uses generation loop
The system SHALL reuse PlanningEngine._generation_loop() for all generation, avoiding new LLM wiring.

#### Scenario: Stabilizer uses engine loop
- **WHEN** stabilize is called
- **THEN** it invokes engine._generation_loop() internally
