# Spec: Epic Dependency Schema

## Requirements

### R1 — `depends_on` field
`Epic` MUST have a field `depends_on: list[str]` that defaults to `[]`.

### R2 — Backwards compatibility
Existing `Epic` YAML/dict objects without a `depends_on` key MUST
deserialise successfully, treating the field as `[]`.

### R3 — Roadmap cycle detection
`Roadmap` MUST validate that `depends_on` references form a DAG (no
cycles). Validation MUST occur at model construction time (Pydantic
validator).

### R4 — Roadmap reference validation
`Roadmap` MUST validate that every ID listed in any `Epic.depends_on`
refers to another epic ID present in `roadmap.epics`. An unknown ID
MUST raise `PlanningError` at load time.

### R5 — Error messages
`PlanningError` raised for a cycle MUST name both epic IDs involved.
`PlanningError` raised for an unknown reference MUST name the
referencing epic and the missing ID.

## Scenarios

### Scenario A — No dependencies (existing behaviour)
Given an Epic with no `depends_on` key,
When the Roadmap is constructed,
Then the epic has `depends_on == []` and no error is raised.

### Scenario B — Valid dependency
Given epic-002 with `depends_on: [epic-001]` and epic-001 present,
When the Roadmap is constructed,
Then no error is raised.

### Scenario C — Cycle detection
Given epic-001 with `depends_on: [epic-002]` and
      epic-002 with `depends_on: [epic-001]`,
When the Roadmap is constructed,
Then a `PlanningError` is raised naming both epic-001 and epic-002.

### Scenario D — Unknown reference
Given epic-002 with `depends_on: [epic-999]` and no epic-999 in the roadmap,
When the Roadmap is constructed,
Then a `PlanningError` is raised naming epic-002 and epic-999.
