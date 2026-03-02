## ADDED Requirements

### Requirement: CampaignGenerator class exists
The system SHALL provide a CampaignGenerator class in openplan/core/campaign_generator.py that accepts a PlanningEngine instance.

#### Scenario: CampaignGenerator initialization
- **WHEN** CampaignGenerator is instantiated with a PlanningEngine
- **THEN** it stores the engine reference for later use

### Requirement: Generate campaign from subsystem
The system SHALL generate a campaign YAML when given a subsystem name and technical debt description.

#### Scenario: Generate campaign
- **WHEN** generate is called with subsystem="auth" and technical_debt="outdated token handling"
- **THEN** it returns a Campaign object with proper structure

### Requirement: Campaign structure
The system SHALL generate a campaign with id, subsystem, motivation, phases (min 2), migration_strategy, and rollback_strategy.

#### Scenario: Campaign has required fields
- **WHEN** generate completes successfully
- **THEN** the campaign contains all required fields including at least 2 phases

### Requirement: Rollback strategy required
The system SHALL fail if rollback_strategy is an empty string.

#### Scenario: Empty rollback fails
- **WHEN** generate is called and the output has empty rollback_strategy
- **THEN** validation fails and refinement is triggered

### Requirement: Max 2 refinements
The system SHALL limit the critique→refine loop to maximum 2 iterations.

#### Scenario: Refinement limit
- **WHEN** generation requires more than 2 refinements
- **THEN** PlanningError is raised

### Requirement: Persists to file
The system SHALL persist the campaign to openplan/campaigns/<id>.yaml.

#### Scenario: Campaign persistence
- **WHEN** generate completes successfully
- **THEN** a YAML file is created in the campaigns directory
