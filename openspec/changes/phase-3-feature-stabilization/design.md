## Context

OpenPlan needs a feature stabilization pipeline to expand vague acceptance criteria, enforce testability, and wire the full critique→refine loop end-to-end for all artifact types. Currently, features may have incomplete or untestable requirements that lead to poor quality and rework.

## Goals / Non-Goals

**Goals:**
- Build FeatureStabilizer that expands vague acceptance criteria and ensures testability (min 3 criteria)
- Create prompt templates for stabilization, campaigns, and ADRs
- Implement CampaignGenerator for technical debt remediation
- Implement ADRGenerator for architecture decisions
- Add CLI commands for all generators
- Write unit tests for all components

**Non-Goals:**
- Live ACP integration in tests (mock all ACP calls)
- Supporting other AI backends beyond ACP
- Runtime user interaction during generation

## Decisions

1. **FeatureStabilizer** → Reuses existing PlanningEngine._generation_loop()
   - Alternative: New LLM wiring - rejected, violates constraint
   - Stabilization prompt expands vague criteria, validates testability

2. **Prompt Templates** → Jinja2 for templating
   - stabilize_feature.j2: Expands acceptance_criteria, sets spec_ready
   - campaign.j2: Generates campaign YAML with phases, migration, rollback
   - adr.j2: Generates ADR YAML with context, alternatives, consequences

3. **CampaignGenerator** → Max 2 refinement iterations
   - Validates rollback_strategy is non-empty (fail if empty string)
   - Persists to openplan/campaigns/<id>.yaml

4. **ADRGenerator** → Sequential ID generation
   - Auto-generates id as adr-<N> based on existing ADRs
   - Persists to openplan/adrs/<id>.yaml

5. **CLI Commands** → Typer with test client support
   - stabilize-feature FEATURE_ID [--model MODEL]
   - generate-campaign SUBSYSTEM [--debt TEXT] [--model MODEL]
   - generate-adr [--context TEXT] [--model MODEL]

## Risks / Trade-offs

- [AI generation may produce invalid YAML] → Critique/refine loop catches errors
- [Vague criteria may still pass if not caught] → Enforce min 3 testable criteria
- [Sequential ID may conflict in parallel] → File-based locking or single-writer
- [Empty rollback_strategy may be passed] → Explicit validation fails if empty string
- [Tests require mocking] → Mock PlanningEngine in all generator tests

## Migration Plan

1. Create prompt templates in openplan/prompts/templates/
2. Implement FeatureStabilizer in openplan/core/stabilizer.py
3. Implement CampaignGenerator in openplan/core/campaign_generator.py
4. Implement ADRGenerator in openplan/core/adr_generator.py
5. Add CLI commands to openplan/cli/main.py
6. Write unit tests for all components

## Open Questions

- Should stabilization be automatic after spec creation?
- Should campaign IDs be random instead of sequential?
