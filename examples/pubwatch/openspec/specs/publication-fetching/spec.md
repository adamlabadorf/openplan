## ADDED Requirements

### Requirement: Publication fetching from external sources
The system SHALL fetch publications matching user-defined topic profiles from external sources.

#### Scenario: Fetch publications successfully
- **WHEN** user runs `pubwatch fetch` command with a valid topic profile
- **THEN** system retrieves matching publications from external APIs (NCBI) and stores them locally

### Requirement: Exponential backoff for API rate limiting
The system SHALL implement exponential backoff when handling HTTP 429 (rate limit) errors.

#### Scenario: Handle rate limit error with retry
- **WHEN** an API call returns HTTP 429 error
- **THEN** system waits using exponential backoff strategy and retries up to 3 times

### Requirement: Avoid duplicate publications
The system SHALL prevent storing duplicate publications in the local database.

#### Scenario: Duplicate detection for fetched publications
- **WHEN** a publication matches an existing one based on title, authors, and abstract
- **THEN** system skips storing the duplicate entry

## MODIFIED Requirements

### Requirement: Pubwatch commands interface
The system SHALL support new `pubwatch fetch` and `pubwatch list` commands.

#### Scenario: Execute fetch command
- **WHEN** user runs `pubwatch fetch`
- **THEN** system retrieves publications matching current topic profiles

#### Scenario: Execute list command
- **WHEN** user runs `pubwatch list` with or without filter criteria
- **THEN** system displays publications from local storage that match the filtering options
