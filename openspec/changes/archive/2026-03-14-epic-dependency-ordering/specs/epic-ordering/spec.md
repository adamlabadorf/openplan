# Spec: Epic Ordering

## ADDED
- `openplan/core/ordering.py` with `resolve_epic_order(epics: list[Epic]) -> list[Epic]`
- Kahn's algorithm (BFS/FIFO) for stable topological ordering
- Cycle detection raising `ValueError` in `resolve_epic_order`

## Requirements

### R1 — `resolve_epic_order` function
A function `resolve_epic_order(epics: list[Epic]) -> list[Epic]` MUST
exist in `openplan/core/ordering.py`.

### R2 — Topological order
Given a list of epics with valid `depends_on` declarations,
`resolve_epic_order` MUST return the epics in an order where every
epic appears after all epics it depends on.

### R3 — Stable order for independent epics
Epics with no dependency relationship between them MUST appear in their
original declaration order (stable sort — Kahn's algorithm with a FIFO
queue preserves insertion order for ties).

### R4 — Cycle raises PlanningError
Given a cycle in `depends_on` (A→B→A),
`resolve_epic_order` MUST raise `PlanningError` with both epic IDs named.

### R5 — Empty / single epic
Given an empty list or a single epic, the function MUST return the list
unchanged without error.

### R6 — No mutation
The function MUST NOT mutate the input list or the Epic objects.

## Scenarios

### Scenario A — Linear chain
Given epics [A, B, C] where B depends on A and C depends on B,
When `resolve_epic_order` is called,
Then the result is [A, B, C].

### Scenario B — Diamond dependency
Given epics [A, B, C, D] where B depends on A, C depends on A,
D depends on B and C,
When `resolve_epic_order` is called,
Then A appears first, D appears last, and B/C appear in declaration order.

### Scenario C — Declared out of order
Given epics [C, B, A] where B depends on A and C depends on B (declared
in reverse), When `resolve_epic_order` is called,
Then the result is [A, B, C].

### Scenario D — No dependencies
Given epics [A, B, C] with no `depends_on` on any,
When `resolve_epic_order` is called,
Then the result equals the input list (original order preserved).
