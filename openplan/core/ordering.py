"""Epic dependency ordering using Kahn's topological sort algorithm."""

from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openplan.core.schemas import Epic


def resolve_epic_order(epics: list) -> list:
    """Return epics in topological order (Kahn's algorithm, FIFO for stable sort).

    Preserves declaration order for independent epics.
    Raises ValueError on cycle (should not happen if Roadmap validator passed,
    but useful when called standalone).

    Args:
        epics: List of Epic objects (must have .id and .depends_on attributes)

    Returns:
        List of epics in topological order (dependencies before dependents)

    Raises:
        ValueError: If a cycle is detected
    """
    if not epics:
        return []

    # Build index and in-degree count
    id_to_epic = {e.id: e for e in epics}
    in_degree: dict[str, int] = {e.id: 0 for e in epics}
    # adjacency: dep -> list of epics that depend on dep
    dependents: dict[str, list[str]] = {e.id: [] for e in epics}

    for epic in epics:
        for dep_id in epic.depends_on:
            in_degree[epic.id] += 1
            dependents[dep_id].append(epic.id)

    # Kahn's algorithm: start with all epics that have no dependencies,
    # preserving declaration order (stable) by using FIFO deque
    declaration_order = {e.id: i for i, e in enumerate(epics)}
    queue: deque[str] = deque()
    for epic in epics:  # iterate in declaration order for stability
        if in_degree[epic.id] == 0:
            queue.append(epic.id)

    result = []
    while queue:
        node_id = queue.popleft()
        result.append(id_to_epic[node_id])

        # Reduce in-degree for dependents, add newly-free nodes in declaration order
        newly_free = []
        for dep_id in dependents[node_id]:
            in_degree[dep_id] -= 1
            if in_degree[dep_id] == 0:
                newly_free.append(dep_id)
        # Sort newly_free by declaration order for stability
        newly_free.sort(key=lambda eid: declaration_order[eid])
        for eid in newly_free:
            queue.append(eid)

    if len(result) != len(epics):
        # Find epics still in a cycle
        remaining = [e.id for e in epics if in_degree[e.id] > 0]
        ids = ", ".join(remaining[:2])
        raise ValueError(f"Cycle detected involving epics: {ids}")

    return result
