"""Build an explainable LocalWorldDraft from limited observation and memory."""
from __future__ import annotations

from .cells import CellType, WALKABLE_CELLS
from .directions import DIRECTION_ORDER, Direction
from .schemas import AgentStateDraft, LocalWorldDraft, Observation


def build_local_world_from_observation(observation: Observation, agent_state: AgentStateDraft) -> LocalWorldDraft:
    walkable: set[Direction] = set()
    blocked: set[Direction] = set()
    frontier: set[Direction] = set()
    for direction in DIRECTION_ORDER:
        pos = observation.player_position.moved(direction.delta)
        cell = observation.visible_cells.get(pos, CellType.UNKNOWN)
        if cell in WALKABLE_CELLS:
            walkable.add(direction)
            beyond = pos.moved(direction.delta)
            if beyond not in observation.explored_cells or observation.visible_cells.get(beyond) == CellType.UNKNOWN:
                frontier.add(direction)
        elif cell == CellType.WALL:
            blocked.add(direction)
        else:
            frontier.add(direction)
    candidates = [d for d in DIRECTION_ORDER if d in frontier and d in walkable and d not in agent_state.failed_directions]
    if not candidates:
        candidates = [d for d in DIRECTION_ORDER if d in walkable and d not in agent_state.failed_directions]
    if not candidates:
        candidates = [d for d in DIRECTION_ORDER if d in walkable]
    recommended = candidates[0] if candidates else None
    known = len(walkable) + len(blocked)
    confidence = known / len(DIRECTION_ORDER)
    needs_probe = confidence < 0.75 or recommended is None
    reason = f"walkable={len(walkable)} blocked={len(blocked)} frontier={len(frontier)}"
    return LocalWorldDraft(observation.player_position, walkable, blocked, frontier, recommended, confidence, needs_probe, reason)
