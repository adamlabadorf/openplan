## ADDED Requirements

### Requirement: openplan status shows vision loaded status
The `openplan status` command SHALL display whether a vision has been loaded.

#### Scenario: Vision not loaded
- **WHEN** user runs `openplan status` without a vision.yaml file
- **THEN** output shows "vision loaded? n"

#### Scenario: Vision loaded
- **WHEN** user runs `openplan status` with a valid vision.yaml file
- **THEN** output shows "vision loaded? y"

### Requirement: openplan status shows roadmap count
The `openplan status` command SHALL display the number of epics in the roadmap.

#### Scenario: Epics present
- **WHEN** user runs `openplan status` with epics in the plan
- **THEN** output shows "roadmap: N epics"

### Requirement: openplan status shows feature counts
The `openplan status` command SHALL display total features and spec_ready features count.

#### Scenario: Features present
- **WHEN** user runs `openplan status` with features in the plan
- **THEN** output shows "features: N total, N spec_ready"

### Requirement: openplan status shows campaigns count
The `openplan status` command SHALL display the number of campaigns.

#### Scenario: Campaigns present
- **WHEN** user runs `openplan status` with campaigns in the plan
- **THEN** output shows "campaigns: N"

### Requirement: openplan status shows adrs count
The `openplan status` command SHALL display the number of ADRs.

#### Scenario: ADRs present
- **WHEN** user runs `openplan status` with ADRs in the plan
- **THEN** output shows "adrs: N"

### Requirement: openplan status lists locked artifacts
The `openplan status` command SHALL list any locked artifacts.

#### Scenario: No locked artifacts
- **WHEN** user runs `openplan status` with no locked artifacts
- **THEN** output does not list any locked artifacts

#### Scenario: Locked artifacts present
- **WHEN** user runs `openplan status` with locked artifacts
- **THEN** output lists each locked artifact
