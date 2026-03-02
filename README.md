# OpenPlan

> Structured, deterministic project planning — from vision to execution-ready specs.

OpenPlan is a planning framework that operates at the **project governance layer**, transforming high-level vision into machine-readable, validated artifacts that feed directly into [OpenSpec](../openspec/) for implementation.

---

## What It Does

OpenPlan enforces a strict planning hierarchy:

```
Vision → Initiatives → Epics → Features → Stories → OpenSpec Spec
```

At each level, artifacts are:
- **Structured** (YAML, not prose)
- **Validated** (measurable criteria, bounded scope)
- **Version-controlled** (immutable once locked)
- **Machine-executable** (consumable by OpenSpec)

---

## What It Does NOT Do

- It does not write code
- It does not replace OpenSpec
- It does not generate unbounded brainstorming output

---

## Core Design Principles

1. Structured outputs only (YAML / JSON)
2. Deterministic pipelines — no open-ended generation
3. Explicit schemas with strict validation
4. Validation gate at every stage
5. Bounded decomposition (max 8 epics, max 10 features per epic)
6. No recursive runaway expansion
7. Version-controlled, immutable artifacts
8. LLM calls wrapped in deterministic workflows

---

## CLI

```bash
openplan init                          # Initialize a new plan workspace
openplan generate-roadmap              # Generate roadmap from vision.yaml
openplan decompose-epic EPIC_ID        # Decompose an epic into features
openplan stabilize-feature FEATURE_ID  # Expand and validate a feature
openplan generate-campaign SUBSYSTEM   # Generate a refactoring campaign
openplan generate-adr                  # Generate an Architecture Decision Record
openplan validate                      # Validate all artifacts
openplan export-to-openspec FEATURE_ID # Export a spec-ready feature to OpenSpec
openplan status                        # Show project status and counts
```

---

## Artifact Structure

```
/plan
  vision.yaml
  roadmap.yaml
  epics/
  features/
  campaigns/
  adrs/
```

---

## Planning Schemas

| Artifact | Key Fields |
|---|---|
| **Vision** | problem_statement, target_users, objectives, success_metrics |
| **Epic** | outcome, success_metrics, architectural_impact, features (≤10) |
| **Feature** | acceptance_criteria (≥3, testable), dependencies, complexity, spec_ready |
| **Campaign** | phases, migration_strategy, rollback_strategy |
| **ADR** | decision, context, alternatives, consequences |

---

## Generation Pipeline

Every artifact follows:

```
Generate → Validate → Critique → Refine → Lock
```

- Max **2 refinement loops** before fail-fast
- Critique agent returns structured JSON with issue severity
- Vague language is rejected (blacklisted: *improve*, *enhance*, *optimize* without metric, etc.)

---

## Governance Rules

| Rule | Limit |
|---|---|
| Max epics per roadmap | 8 |
| Max features per epic | 10 |
| Max acceptance criteria per feature | 15 |
| Min acceptance criteria per feature | 3 |
| Refinement loops before fail | 2 |

---

## OpenSpec Integration

Features where `spec_ready: true` can be exported directly:

```python
def feature_to_openspec_input(feature):
    return {
        "goal": feature.description,
        "acceptance_criteria": feature.acceptance_criteria,
        "constraints": inherited_constraints,
        "architectural_context": lookup_arch_context()
    }
```

OpenPlan blocks export if a feature fails validation.

---

## Sample vision.yaml

```yaml
id: api-performance-vision
problem_statement: Reduce API response time from 500ms to under 100ms for user dashboard
target_users: Internal engineering team
objectives:
  - Reduce latency
  - Improve user experience
success_metrics:
  - name: response_time
    target: '100'
    unit: milliseconds
  - name: p99_latency
    target: '150'
    unit: milliseconds
```

### Validation

Vision YAML is validated against the Vision Pydantic schema on load. Validation includes:
- At least one success metric required
- Vague phrases are rejected (improve, enhance, optimize, etc. without specific metric)

```bash
openplan validate --all  # Validate all artifacts including vision.yaml
```

---

## Quickstart

```bash
# Initialize a new project
mkdir my-plan && cd my-plan
openplan init

# Create vision.yaml (see sample above)
cat > openplan/visions/vision.yaml << 'EOF'
id: api-performance-vision
problem_statement: Reduce API response time from 500ms to under 100ms for user dashboard
target_users: Internal engineering team
objectives:
  - Reduce latency
  - Improve user experience
success_metrics:
  - name: response_time
    target: '100'
    unit: milliseconds
  - name: p99_latency
    target: '150'
    unit: milliseconds
EOF

# Generate a roadmap from vision
openplan generate-roadmap

# Decompose an epic into features
openplan decompose-epic epic-1

# Stabilize a feature (expand acceptance criteria)
openplan stabilize-feature feature-1

# Export to OpenSpec (requires spec_ready: true)
openplan export-to-openspec feature-1 --openspec-dir ../openspec

# Check project status
openplan status
```

---

## Implementation Phases

| Phase | Scope |
|---|---|
| 1 | Core schemas, validation layer, file storage, CLI scaffolding |
| 2 | Roadmap generator, epic decomposer, validation integration |
| 3 | Feature stabilizer, critique/refinement loop |
| 4 | Campaign generator, ADR generator |
| 5 | OpenSpec adapter, integration tests |

---

## Success Criteria

OpenPlan is complete when:

1. Given a Vision → generates valid `roadmap.yaml`
2. Given an Epic → generates bounded, validated features
3. Given a Feature → generates a `spec_ready: true` artifact
4. All outputs pass validation without manual edits
5. OpenSpec can automatically consume an exported feature

---

## Project Layout

```
openplan/
  core/
    engine.py         # Orchestration and state management
    state.py          # Planning state model
    validation.py     # Validation engine
    schemas.py        # Pydantic schemas for all artifact types
  generators/
    roadmap.py
    epic.py
    feature.py
    campaign.py
    adr.py
  validators/
    roadmap_validator.py
    epic_validator.py
    feature_validator.py
  refinement/
    critique.py
    refine.py
  integrations/
    openspec_adapter.py
  storage/
    repository.py
  cli/
    main.py
  SYSTEM_SPECIFICATION.md
  README.md
```
