## ADDED Requirements

### Requirement: ADRGenerator class exists
The system SHALL provide an ADRGenerator class in openplan/core/adr_generator.py that accepts a PlanningEngine instance.

#### Scenario: ADRGenerator initialization
- **WHEN** ADRGenerator is instantiated with a PlanningEngine
- **THEN** it stores the engine reference for later use

### Requirement: Generate ADR from context
The system SHALL generate an ADR when given decision context and alternatives considered.

#### Scenario: Generate ADR
- **WHEN** generate is called with decision_context and alternatives
- **THEN** it returns an ADR object with proper structure

### Requirement: ADR structure
The system SHALL generate an ADR with id, decision, context, alternatives_considered, consequences_positive, and consequences_negative.

#### Scenario: ADR has required fields
- **WHEN** generate completes successfully
- **THEN** the ADR contains all required fields

### Requirement: Sequential ID generation
The system SHALL auto-generate id as adr-<N> where N is sequential based on existing ADRs.

#### Scenario: Sequential ID assignment
- **WHEN** generate is called
- **THEN** the ADR id is assigned sequentially (adr-1, adr-2, etc.)

### Requirement: Max 2 refinements
The system SHALL limit the critique→refine loop to maximum 2 iterations.

#### Scenario: Refinement limit
- **WHEN** generation requires more than 2 refinements
- **THEN** PlanningError is raised

### Requirement: Persists to file
The system SHALL persist the ADR to openplan/adrs/<id>.yaml.

#### Scenario: ADR persistence
- **WHEN** generate completes successfully
- **THEN** a YAML file is created in the adrs directory
