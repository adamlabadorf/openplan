## MODIFIED Requirements

### Requirement: Pubwatch commands interface
The system SHALL support new `pubwatch fetch` and `pubwatch list` commands.

#### Scenario: Execute fetch command
- **WHEN** user runs `pubwatch fetch`
- **THEN** system retrieves publications matching current topic profiles

#### Scenario: Execute list command
- **WHEN** user runs `pubwatch list` with or without filter criteria
- **THEN** system displays publications from local storage that match the filtering options

#### Scenario: Execute list command with filter options
- **WHEN** user runs `pubwatch list` with filtering criteria (e.g., by date range, keyword)
- **THEN** system displays only publications matching the filter criteria
