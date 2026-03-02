Excellent. I’ll give you something you can hand directly to a coding agent.

This will be structured like an **OpenSpec-style meta-spec** for building **OpenPlan** itself.

No fluff — just system design, modules, schemas, execution flow, constraints, and phased implementation.

---

# OpenPlan — System Specification

## 0. Purpose

OpenPlan is a structured, deterministic planning framework modeled after OpenSpec, but operating at the **project governance layer** instead of the code-change layer.

It must:

* Transform vision → roadmap → epics → features → stories → execution-ready specs
* Enforce structure (no prose-only plans)
* Validate scope and measurability
* Support iterative refinement
* Produce machine-readable artifacts
* Integrate directly with OpenSpec

Non-goals:

* It does not implement code.
* It does not replace OpenSpec.
* It does not generate unbounded brainstorming output.

---

# 1. Core Design Principles

1. Structured outputs only (YAML / JSON)
2. Deterministic pipelines
3. Explicit schemas
4. Validation at every stage
5. Bounded decomposition
6. No recursive runaway expansion
7. Version-controlled artifacts
8. LLM calls wrapped in deterministic workflows

---

# 2. High-Level Architecture

```text
openplan/
  core/
    engine.py
    state.py
    validation.py
    schemas.py
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
```

---

# 3. Planning Hierarchy Model

OpenPlan operates on strict hierarchy:

```text
Vision
  → Initiatives (optional)
      → Epics
          → Features
              → Stories
                  → OpenSpec Spec
```

Each level has:

* Required fields
* Max size constraints
* Measurable outputs
* Risk annotations

---

# 4. Core Schemas

These must be implemented as strict validation schemas (Pydantic or equivalent).

---

## 4.1 Vision Schema

```yaml
vision:
  problem_statement: string
  target_users: [string]
  business_objectives: [string]
  constraints: [string]
  success_metrics:
    - name: string
      target: string
      deadline: optional string
```

Validation:

* At least one measurable success metric required
* No vague phrases allowed (“improve”, “enhance”)

---

## 4.2 Epic Schema

```yaml
epic:
  id: string
  description: string
  outcome: string
  success_metrics:
    - metric: string
      target: string
  risks:
    - description: string
      severity: low|medium|high
  architectural_impact:
    - subsystem: string
      impact_type: new|modify|remove
  features: [feature_id]
  max_feature_count: <= 10
```

Validation:

* Must include measurable success metric
* Must declare architectural impact
* Max 10 features

---

## 4.3 Feature Schema

```yaml
feature:
  id: string
  epic_id: string
  description: string
  user_value: string
  acceptance_criteria:
    - condition: string
  dependencies: [feature_id]
  estimated_complexity: low|medium|high
  spec_ready: boolean
```

Validation:

* At least 3 acceptance criteria
* Each criterion testable
* No circular dependencies

---

## 4.4 Refactoring Campaign Schema

```yaml
campaign:
  id: string
  subsystem: string
  motivation: string
  phases:
    - phase_id: string
      goal: string
      success_metric: string
  migration_strategy: string
  rollback_strategy: string
```

Validation:

* Must define rollback strategy
* Must define phased execution

---

## 4.5 ADR Schema

```yaml
adr:
  id: string
  decision: string
  context: string
  alternatives_considered: [string]
  consequences:
    positive: [string]
    negative: [string]
```

---

# 5. Planning Engine

## 5.1 Engine Responsibilities

The engine:

* Loads state
* Executes generation steps
* Validates output
* Runs critique pass
* Refines if needed
* Persists artifacts

---

## 5.2 Deterministic Flow

Every generation step must follow:

```text
Generate → Validate → Critique → Refine → Lock
```

Maximum:

* 2 refinement loops
* Otherwise fail fast

---

# 6. Generator Modules

Each generator is isolated and bounded.

---

## 6.1 Roadmap Generator

Input:

* Vision schema
* Constraints
* Time horizon

Output:

* List of epics (max 8)
* Sequencing
* Dependency graph

Constraints:

* Epics must be outcome-based
* Not implementation tasks

---

## 6.2 Epic Decomposer

Input:

* Single epic
* Architecture summary

Output:

* 3–10 features
* Feature ordering
* Risk distribution

Constraints:

* Features must be independently deliverable
* No mega-features

---

## 6.3 Feature Stabilizer

Input:

* Feature draft

Output:

* Fully acceptance-criteria-complete feature
* Mark spec_ready = true if valid

Must:

* Expand vague criteria
* Remove non-testable language

---

## 6.4 Refactoring Campaign Generator

Input:

* Subsystem description
* Known technical debt

Output:

* Phased refactor roadmap
* Migration sequencing

Must:

* Limit each phase scope
* Contain blast radius

---

# 7. Validation System

All validators must:

* Reject vague verbs
* Enforce measurable metrics
* Enforce size bounds
* Detect dependency cycles
* Detect scope creep

Vague phrase blacklist:

* improve
* enhance
* optimize (without metric)
* refactor (without target)
* better

---

# 8. Refinement Layer

After generation:

Critique agent must evaluate:

* Ambiguity
* Over-scope
* Missing constraints
* Risk underestimation

Return structured critique:

```json
{
  "issues": [...],
  "severity": "...",
  "requires_refinement": true|false
}
```

---

# 9. Storage Model

All artifacts must be:

* Stored as YAML
* Version-controlled
* Immutable once locked
* Linked by ID references

Suggested structure:

```text
/plan
  vision.yaml
  roadmap.yaml
  epics/
  features/
  campaigns/
  adrs/
```

---

# 10. OpenSpec Integration

Add adapter:

```python
def feature_to_openspec_input(feature):
    return {
        "goal": feature.description,
        "acceptance_criteria": feature.acceptance_criteria,
        "constraints": inherited_constraints,
        "architectural_context": lookup_arch_context()
    }
```

OpenPlan must:

* Only pass features where spec_ready == true
* Block execution if feature invalid

---

# 11. CLI Interface

Commands:

```bash
openplan init
openplan generate-roadmap
openplan decompose-epic EPIC_ID
openplan stabilize-feature FEATURE_ID
openplan generate-campaign SUBSYSTEM
openplan validate
openplan export-to-openspec FEATURE_ID
```

---

# 12. Governance Rules

Enforce globally:

* Max 8 epics per roadmap
* Max 10 features per epic
* Max 15 acceptance criteria per feature
* No feature without measurable criteria
* No epic without architectural impact

---

# 13. Phase-Based Implementation Plan (For Your Coding Agent)

## Phase 1 — Core Infrastructure

* Implement schemas
* Implement validation layer
* File storage system
* CLI scaffolding

## Phase 2 — Roadmap + Epic Generators

* Roadmap generator
* Epic decomposition
* Validation integration

## Phase 3 — Feature Stabilization + Refinement

* Acceptance criteria expansion
* Critique/refinement loop

## Phase 4 — Campaign + ADR Support

* Refactoring campaign generator
* ADR generator

## Phase 5 — OpenSpec Adapter

* Feature export
* Integration tests

---

# 14. Safety Constraints

The system must:

* Refuse unbounded decomposition
* Refuse vague goals
* Refuse recursive generation loops
* Log all LLM interactions
* Support dry-run mode

---

# 15. Success Criteria for OpenPlan Itself

OpenPlan is considered complete when:

1. Given a Vision → it generates valid roadmap.yaml
2. Given an Epic → it generates bounded features
3. Given a Feature → it generates spec-ready artifact
4. All outputs pass validation without manual edits
5. OpenSpec can consume a feature automatically

---

# Final Instruction Block You Can Hand to an Agent

You can give your coding agent:

> Implement OpenPlan as a deterministic planning layer modeled after OpenSpec.
> Use strict schemas, bounded generation, validation gates, refinement loops, and version-controlled YAML artifacts.
> No freeform markdown outputs.
> All planning artifacts must be machine-executable and enforce measurable success criteria.

---

If you'd like, I can next:

* Convert this into an OpenSpec-formatted spec for building OpenPlan
* Or design the exact prompt templates your coding agent should use for each generator module
* Or design the LangGraph orchestration for autonomous planning mode

Which layer do you want to formalize next?

