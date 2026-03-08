## ADDED Requirements

### Requirement: User can import topic profiles
The system SHALL allow researchers to import topic profiles from a JSON file.

#### Scenario: Successful profile import
- **WHEN** researcher attempts to import a valid JSON file
- **THEN** the system validates the JSON format and loads all profiles into the system

### Requirement: Import validation
The system SHALL validate the JSON format during import operations.

#### Scenario: Invalid JSON file
- **WHEN** researcher attempts to import an invalid JSON file
- **THEN** an error message is displayed indicating the file format is invalid

### Requirement: Duplicate profile handling
The system SHALL handle profiles that already exist with the same name.

#### Scenario: Import duplicate profile confirmation
- **WHEN** researcher imports a file containing a profile that already exists with the same name
- **THEN** user is prompted to confirm overwrite
- **WHEN** user confirms overwrite
- **THEN** the existing profile is replaced by the imported one

### Requirement: Selective loading of profiles
The system SHALL validate profile fields and load valid profiles while skipping invalid ones.

#### Scenario: Import with mixed valid/invalid profiles
- **WHEN** researcher imports a modified JSON file containing both valid and invalid profiles
- **THEN** the system loads valid profiles and skips invalid ones with appropriate logging