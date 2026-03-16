# Spec: gap-synthesis

## ADDED

### R1 — `GATHER.md` gap analysis document
`GATHER.md` written by `GatherAnalyser` MUST include sections:
- **What Exists** — inferred modules/components from `src/`
- **What Was Planned** — summary from prior roadmap(s) via HISTORY.md
- **What Was Deferred** — items from HISTORY.md notes + unimplemented features
- **Post-Plan Changes** — OpenSpec changes added after initial implementation
- **Gaps Identified** — synthesised list of items the new roadmap should address
- **Human Review Required** — flagged items needing manual verification

### R2 — No prior history graceful handling
If `HISTORY.md` does not exist and no archived roadmaps exist,
`GATHER.md` MUST still be written with whatever can be inferred from source,
noting that no prior plan history was found.

### R3 — New roadmap does not duplicate implemented features
The generated `Roadmap` MUST NOT include epics that are semantically identical
to fully-passing epics in archived roadmaps. The LLM prompt MUST include prior
roadmap context to prevent duplication.

### R4 — Deferred items become epics
Items listed as deferred in `HISTORY.md` notes MUST be included in the
generated roadmap as epic candidates in the LLM prompt context.

#### Scenario: no prior history
Given no `HISTORY.md` and no `openplan/archived/` directory,
When gap synthesis runs,
Then `GATHER.md` is written with a note that no prior history was found and
sections contain what can be inferred from source.

#### Scenario: deferred items in history
Given `HISTORY.md` contains `Note: Auth deferred to v2`,
When gap synthesis runs,
Then `GATHER.md` "What Was Deferred" section mentions Auth, and the generated
roadmap contains an Auth-related epic.
