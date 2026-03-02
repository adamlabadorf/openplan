## Context

OpenPlan needs an automated generation layer to produce planning artifacts from vision statements. Currently, all artifacts are created manually. This design outlines how to build the generation layer using ACP (AI Code Partner) for code generation.

## Goals / Non-Goals

**Goals:**
- Create ACP client wrapper for AI code generation
- Build Jinja2 prompt template system for structured prompts
- Implement planning engine with validation and refinement loops
- Add CLI commands for roadmap generation and epic decomposition

**Non-Goals:**
- Live ACP integration in tests (mock all ACP calls)
- Supporting other AI backends beyond ACP
- Runtime user interaction during generation

## Decisions

1. **ACP Client Wrapper** → Use context manager pattern for resource safety
   - Alternative: Direct function calls - rejected due to no cleanup
   - Wraps `ACPClient` with `OpenCodeClient` providing `generate()` method

2. **Template System** → Jinja2 for prompt templating
   - Alternative: f-strings - rejected, no control flow support
   - Alternative: string.Template - rejected, limited functionality
   - Jinja2 provides loops, conditionals, filters needed for complex prompts

3. **Validation Approach** → Pydantic models for schema validation
   - Alternative: ad-hoc parsing - rejected, no validation guarantees
   - Pydantic provides type safety and validation errors

4. **Refinement Loop** → Max 2 iterations with critique/refine cycle
   - Alternative: unlimited iterations - rejected, could infinite loop
   - 2 iterations balances correctness with performance

5. **Artifact Persistence** → YAML files in openplan/ directory
   - Alternative: JSON - rejected, less readable for planning
   - YAML is standard for OpenPlan artifacts

## Risks / Trade-offs

- [AI generation may produce invalid YAML] → Critique/refine loop catches errors
- [Template rendering may fail] → TemplateLoader raises on missing templates
- [Engine may fail after 2 refinements] → PlanningError raised with details
- [Tests require mocking] → Mock OpenCodeClient in all engine tests

## Migration Plan

1. Create directory structure (integrations/, prompts/, prompts/templates/)
2. Implement ACP client wrapper
3. Implement template loader
4. Create prompt templates (roadmap, epic, critique, refine)
5. Implement planning engine
6. Add CLI commands
7. Write unit tests

## Open Questions

- Should the engine support async generation?
- Should templates support custom filters?
