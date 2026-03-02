## Why

The OpenPlan system lacks a feature stabilization pipeline to expand vague acceptance criteria, enforce testability, and wire the full critique→refine loop end-to-end for all artifact types. Without this, features may ship with incomplete or untestable requirements, leading to poor quality and rework.

## What Changes

- Add `FeatureStabilizer` class in `openplan/core/stabilizer.py` that sends features through stabilization prompts, expands vague criteria, ensures min 3 testable criteria, and sets `spec_ready=True` when valid
- Create new prompt templates: `stabilize_feature.j2`, `campaign.j2`, `adr.j2` in `openplan/prompts/templates/`
- Add `CampaignGenerator` in `openplan/core/campaign_generator.py` to generate campaign YAMLs for technical debt remediation
- Add `ADRGenerator` in `openplan/core/adr_generator.py` to generate ADR YAMLs for architecture decisions
- Add CLI commands: `stabilize-feature`, `generate-campaign`, `generate-adr`
- Add unit tests for all new components

## Capabilities

### New Capabilities

- **feature-stabilization**: Feature stabilization pipeline that expands vague acceptance criteria, enforces testability (min 3 criteria), and sets spec_ready flag
- **campaign-generator**: Campaign generator for technical debt remediation with phases, migration, and rollback strategies
- **adr-generator**: ADR (Architecture Decision Record) generator for documenting decisions with context, alternatives, and consequences
- **cli-stabilize**: CLI command to stabilize a feature by ID
- **cli-campaign**: CLI command to generate a campaign for a subsystem
- **cli-adr**: CLI command to generate an ADR

### Modified Capabilities

- None - this is a net-new capability set

## Impact

- New files: `openplan/core/stabilizer.py`, `openplan/core/campaign_generator.py`, `openplan/core/adr_generator.py`, `openplan/prompts/templates/stabilize_feature.j2`, `openplan/prompts/templates/campaign.j2`, `openplan/prompts/templates/adr.j2`
- Modified files: `openplan/cli/main.py` (new commands), test files
- Dependencies: Uses existing `PlanningEngine._generation_loop()` - no new LLM wiring
