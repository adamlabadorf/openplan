## ADDED Requirements

### Requirement: Topic profile definition
The system SHALL allow researchers to define topic profiles with specific keywords.

#### Scenario: Define topic profile with keywords
- **WHEN** researcher creates a topic profile with keywords
- **THEN** system uses those keywords to filter publications from external sources

### Requirement: Keyword-based publication filtering
The system SHALL filter publications based on keyword matches in title, authors, or abstract.

#### Scenario: Filter publications by keywords
- **WHEN** system fetches publications
- **THEN** system filters publications that match at least one keyword from the active topic profile

## MODIFIED Requirements

### Requirement: Pubwatch commands interface
The system SHALL support new `pubwatch fetch` and `pubwatch list` commands.

#### Scenario: Execute fetch command with topic profiles
- **WHEN** user runs `pubwatch fetch`
- **THEN** system fetches publications for all active topic profiles
