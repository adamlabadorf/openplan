## ADDED Requirements

### Requirement: TemplateLoader initialization
The system SHALL provide a TemplateLoader class that loads Jinja2 templates from the templates directory.

#### Scenario: Default templates directory
- **WHEN** TemplateLoader is instantiated without a directory parameter
- **THEN** it SHALL default to loading from `openplan/prompts/templates/`

#### Scenario: Custom templates directory
- **WHEN** TemplateLoader is instantiated with a custom directory
- **THEN** it SHALL load templates from the specified directory

### Requirement: Template rendering
The system SHALL provide a `render()` method that renders templates with context.

#### Scenario: Successful template render
- **WHEN** `render(template_name: str, context: dict)` is called with valid template and context
- **THEN** it SHALL return the rendered string
- **AND** SHALL interpolate all context variables

#### Scenario: Missing template raises error
- **WHEN** `render()` is called with a non-existent template name
- **THEN** it SHALL raise an appropriate error

### Requirement: Roadmap template
The system SHALL provide a `roadmap.j2` template that generates prompts for roadmap creation.

#### Scenario: Roadmap template structure
- **WHEN** roadmap.j2 is rendered with Vision YAML, constraints, and time_horizon
- **THEN** it SHALL output a prompt instructing OpenCode to produce YAML
- **AND** the output SHALL include instruction: "Respond with ONLY valid YAML. No explanation, no markdown fences, no extra text."

### Requirement: Epic template
The system SHALL provide an `epic.j2` template that generates prompts for epic decomposition.

#### Scenario: Epic template structure
- **WHEN** epic.j2 is rendered with Epic stub and architecture summary
- **THEN** it SHALL output a prompt for generating 3-10 features per epic
- **AND** each feature SHALL include id, epic_id, description, user_value, acceptance_criteria, dependencies, estimated_complexity, spec_ready=false

### Requirement: Critique template
The system SHALL provide a `critique.j2` template for critiquing artifacts.

#### Scenario: Critique template structure
- **WHEN** critique.j2 is rendered with artifact_type, artifact_yaml, and optional schema_errors
- **THEN** it SHALL output a prompt for generating structured JSON critique
- **AND** the output SHALL include issues list with severity and requires_refinement boolean

### Requirement: Refine template
The system SHALL provide a `refine.j2` template for refining artifacts based on critique.

#### Scenario: Refine template structure
- **WHEN** refine.j2 is rendered with original artifact_yaml, critique JSON, and artifact_type
- **THEN** it SHALL output a prompt for generating corrected YAML artifact
