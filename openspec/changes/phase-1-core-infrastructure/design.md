## Context

OpenPlan Phase 1 establishes foundational infrastructure: a deterministic planning harness with Pydantic v2 schemas, storage layer, and CLI. The project targets developers using OpenPlan to manage structured planning artifacts. Key constraints: no LLM calls in Phase 1, pure Python + schemas + file I/O, snake_case YAML keys.

## Goals / Non-Goals

**Goals:**
- Create runnable Python package with uv dependency management
- Define Pydantic v2 schemas with validators for all artifact types
- Implement PlanRepository for YAML CRUD with locking
- Build CLI with init and validate commands
- Establish test suite covering schemas, storage, and CLI

**Non-Goals:**
- Database integration (filesystem-only for Phase 1)
- LLM/AI integration
- Web UI or API server
- Advanced search or querying
- Multi-file atomic transactions (single-file locking only)

## Decisions

1. **YAML over JSON**: YAML is more human-readable for planning artifacts and supports comments. Snake_case keys maintain consistency.

2. **File-based locking over DB**: Simpler for Phase 1. `.locked` marker files provide basic concurrency safety.

3. **Pydantic v2 over v1**: Required by user. Better validation, performance, and future-proofing.

4. **Typer over Click**: More Pythonic, better type inference, integrates cleanly with Pydantic models.

5. **Single module per artifact type**: Features/epics/campaigns/adrs as separate directories keeps organization clean.

## Risks / Trade-offs

- **Risk**: Circular feature dependencies undetected → **Mitigation**: Collection-level validation checks for cycles
- **Risk**: Lock file left behind after crash → **Mitigation**: Document manual cleanup process; consider atime-based cleanup in future
- **Risk**: Vague phrase validation is overly aggressive → **Mitigation**: Clear blacklist documented; can be extended
- **Trade-off**: Limited concurrency (one writer at a time) → **Mitigation**: Acceptable for planning tool use case

## Migration Plan

1. Install package: `uv pip install -e .`
2. Initialize: `openplan init` creates `openplan/` directory structure
3. Create artifacts via CLI or direct YAML files
4. Validate: `openplan validate --all`

**Rollback**: Remove `openplan/` directory and uninstall package.

## Open Questions

- Should feature IDs be auto-generated (UUID) or user-provided? → User-provided for readability
- How to handle schema migration for existing plans? → Defer to Phase 2
