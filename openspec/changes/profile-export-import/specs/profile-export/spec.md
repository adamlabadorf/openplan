## ADDED Requirements

### Requirement: User can export topic profiles
The system SHALL allow researchers to export all topic profiles to a JSON file.

#### Scenario: Successful profile export
- **WHEN** researcher requests to export profiles
- **THEN** a JSON file containing all profile configurations is generated and saved to the specified location

#### Scenario: Export with specified location
- **WHEN** researcher selects an export location
- **THEN** the system saves the JSON file at that location

### Requirement: Export format structure
The system SHALL generate a JSON file with appropriate structure for topic profiles.

#### Scenario: Valid export structure
- **WHEN** export is performed
- **THEN** the JSON contains valid profile data organized by profile name

## MODIFIED Requirements

### Requirement: Profile data serialization
The system SHALL support serializing profile configurations to JSON format.

#### Scenario: Serialization of profile data
- **WHEN** system prepares profile data for export
- **THEN** all profile fields are correctly serialized into the JSON structure