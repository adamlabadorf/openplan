"""Tests for resolve_epic_order (Kahn's topological sort)."""

import pytest
from openplan.core.ordering import resolve_epic_order
from openplan.core.schemas import ArchitecturalImpact, Epic, SuccessMetric


def make_epic(epic_id: str, depends_on: list[str] | None = None) -> Epic:
    """Helper to construct a minimal valid Epic (bypassing Roadmap validator)."""
    return Epic(
        id=epic_id,
        title=f"Epic {epic_id}",
        outcome="some outcome",
        success_metrics=[SuccessMetric(name="m", target="t", unit="u")],
        architectural_impact=[
            ArchitecturalImpact(component="c", change_type="add", description="d")
        ],
        depends_on=depends_on or [],
    )


def ids(epics: list[Epic]) -> list[str]:
    return [e.id for e in epics]


def test_empty_list():
    """Empty list returns empty list."""
    assert resolve_epic_order([]) == []


def test_single_epic():
    """Single epic with no deps returns list of one."""
    e = make_epic("e1")
    result = resolve_epic_order([e])
    assert ids(result) == ["e1"]


def test_linear_chain():
    """e1 -> e2 -> e3 returns [e1, e2, e3]."""
    e1 = make_epic("e1")
    e2 = make_epic("e2", depends_on=["e1"])
    e3 = make_epic("e3", depends_on=["e2"])
    result = resolve_epic_order([e1, e2, e3])
    assert ids(result) == ["e1", "e2", "e3"]


def test_reverse_order_input():
    """Epics given in reverse dependency order are sorted correctly."""
    e1 = make_epic("e1")
    e2 = make_epic("e2", depends_on=["e1"])
    e3 = make_epic("e3", depends_on=["e2"])
    # Pass in reverse
    result = resolve_epic_order([e3, e2, e1])
    result_ids = ids(result)
    # e1 must come before e2, e2 before e3
    assert result_ids.index("e1") < result_ids.index("e2")
    assert result_ids.index("e2") < result_ids.index("e3")


def test_diamond_dependency():
    """Diamond: e1 -> e2, e1 -> e3, e2 -> e4, e3 -> e4."""
    e1 = make_epic("e1")
    e2 = make_epic("e2", depends_on=["e1"])
    e3 = make_epic("e3", depends_on=["e1"])
    e4 = make_epic("e4", depends_on=["e2", "e3"])
    result = resolve_epic_order([e1, e2, e3, e4])
    result_ids = ids(result)
    assert result_ids.index("e1") < result_ids.index("e2")
    assert result_ids.index("e1") < result_ids.index("e3")
    assert result_ids.index("e2") < result_ids.index("e4")
    assert result_ids.index("e3") < result_ids.index("e4")


def test_no_dependencies_preserves_declaration_order():
    """Epics with no deps preserve their original declaration order."""
    epics = [make_epic(f"e{i}") for i in range(1, 6)]
    result = resolve_epic_order(epics)
    assert ids(result) == [f"e{i}" for i in range(1, 6)]


def test_cycle_raises_value_error():
    """Cycle in dependencies raises ValueError."""
    e1 = make_epic("e1", depends_on=["e2"])
    e2 = make_epic("e2", depends_on=["e1"])
    with pytest.raises(ValueError, match="[Cc]ycle"):
        resolve_epic_order([e1, e2])


def test_three_node_cycle_raises():
    """Three-node cycle raises ValueError."""
    e1 = make_epic("e1", depends_on=["e3"])
    e2 = make_epic("e2", depends_on=["e1"])
    e3 = make_epic("e3", depends_on=["e2"])
    with pytest.raises(ValueError, match="[Cc]ycle"):
        resolve_epic_order([e1, e2, e3])
