from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


VAGUE_PHRASES = [
    "improve",
    "enhance",
    "optimize",
    "refactor",
    "better",
    "faster",
    "easier",
    "simpler",
    "cleaner",
    "modernize",
]


class SuccessMetric(BaseModel):
    name: str
    target: str
    unit: str


class Risk(BaseModel):
    description: str
    severity: str
    mitigation: str


class ArchitecturalImpact(BaseModel):
    component: str
    change_type: str
    description: str


class Vision(BaseModel):
    id: str
    problem_statement: str
    target_users: str
    objectives: list[str]
    success_metrics: list[SuccessMetric]
    risks: list[Risk] = Field(default_factory=list)

    @field_validator("success_metrics")
    @classmethod
    def validate_metrics(cls, v):
        if len(v) < 1:
            raise ValueError("Vision must have at least one success metric")
        return v

    @field_validator("problem_statement", "target_users")
    @classmethod
    def validate_no_vague_phrases(cls, v):
        v_lower = v.lower()
        for phrase in VAGUE_PHRASES:
            if phrase in v_lower:
                raise ValueError(
                    f"Vague phrase '{phrase}' not allowed without specific metric"
                )
        return v


class FeatureRef(BaseModel):
    feature_id: str
    reason: Optional[str] = None


class Epic(BaseModel):
    id: str
    title: str
    outcome: str
    success_metrics: list[SuccessMetric]
    architectural_impact: list[ArchitecturalImpact]
    features: list[FeatureRef] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)

    @field_validator("success_metrics")
    @classmethod
    def validate_metrics(cls, v):
        if len(v) < 1:
            raise ValueError("Epic must have at least one success metric")
        return v

    @field_validator("architectural_impact")
    @classmethod
    def validate_arch_impact(cls, v):
        if len(v) < 1:
            raise ValueError("Epic must have at least one architectural impact")
        return v

    @field_validator("features")
    @classmethod
    def validate_features_count(cls, v):
        if len(v) > 10:
            raise ValueError("Epic cannot have more than 10 features")
        return v


class Feature(BaseModel):
    id: str
    title: str
    description: str
    acceptance_criteria: list[str]
    dependencies: list[str] = Field(default_factory=list)
    complexity: str = "medium"
    spec_ready: bool = False

    @field_validator("acceptance_criteria")
    @classmethod
    def validate_criteria_count(cls, v):
        if len(v) < 3:
            raise ValueError("Feature must have at least 3 acceptance criteria")
        if len(v) > 15:
            raise ValueError("Feature cannot have more than 15 acceptance criteria")
        return v

    @field_validator("acceptance_criteria")
    @classmethod
    def validate_criteria_not_empty(cls, v):
        for criterion in v:
            if not criterion.strip():
                raise ValueError("Acceptance criteria cannot be empty")
        return v

    @field_validator("dependencies")
    @classmethod
    def validate_no_circular_deps(cls, v):
        if len(v) > 0:
            deps_set = set(v)
            for dep in v:
                if dep in deps_set and dep != "":
                    pass
        return v


class Phase(BaseModel):
    name: str
    description: str
    duration_weeks: int


class Campaign(BaseModel):
    id: str
    title: str
    description: str
    phases: list[Phase]
    rollback_strategy: str

    @field_validator("phases")
    @classmethod
    def validate_phases_count(cls, v):
        if len(v) < 2:
            raise ValueError("Campaign must have at least 2 phases")
        return v

    @field_validator("rollback_strategy")
    @classmethod
    def validate_rollback(cls, v):
        if not v or not v.strip():
            raise ValueError("Campaign must have a rollback strategy")
        return v


class ADR(BaseModel):
    id: str
    title: str
    decision: str
    context: str
    alternatives: list[str] = Field(default_factory=list)
    consequences: str
    status: str = "proposed"


class Roadmap(BaseModel):
    id: str
    title: str
    vision_id: str
    epics: list[Epic]

    @field_validator("epics")
    @classmethod
    def validate_epics_count(cls, v):
        if len(v) > 8:
            raise ValueError("Roadmap cannot have more than 8 epics")
        return v

    @model_validator(mode='after')
    def validate_epic_dependencies(self) -> 'Roadmap':
        """Validate depends_on references and detect cycles."""
        epic_ids = {e.id for e in self.epics}

        # Check all depends_on IDs reference known epics
        for epic in self.epics:
            for dep_id in epic.depends_on:
                if dep_id not in epic_ids:
                    raise ValueError(
                        f"Epic '{epic.id}' depends_on unknown epic '{dep_id}'"
                    )

        # Detect cycles using DFS colour map (white=0, grey=1, black=2)
        colour = {e.id: 0 for e in self.epics}
        adj = {e.id: list(e.depends_on) for e in self.epics}

        def dfs(node: str, path: list) -> None:
            colour[node] = 1  # grey — in progress
            for neighbour in adj[node]:
                if colour[neighbour] == 1:
                    raise ValueError(
                        f"Cycle detected in epic dependencies: '{node}' -> '{neighbour}'"
                    )
                if colour[neighbour] == 0:
                    dfs(neighbour, path + [neighbour])
            colour[node] = 2  # black — done

        for epic in self.epics:
            if colour[epic.id] == 0:
                dfs(epic.id, [epic.id])

        return self


class PlanState(BaseModel):
    vision: Optional[Vision] = None
    roadmap: Optional[Roadmap] = None
    epics: list[Epic] = Field(default_factory=list)
    features: list[Feature] = Field(default_factory=list)
    campaigns: list[Campaign] = Field(default_factory=list)
    adrs: list[ADR] = Field(default_factory=list)
