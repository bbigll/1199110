"""Deterministic frontier-first MiniWorld exploration policy."""
from __future__ import annotations

from .directions import DIRECTION_ORDER, Direction
from .schemas import AgentStateDraft, LocalWorldDraft, NextExplorationAction


class ExplorationPolicy:
    def choose_action(self, local_world: LocalWorldDraft, agent_state: AgentStateDraft) -> NextExplorationAction:
        failed = set(agent_state.failed_directions)
        if agent_state.stuck_counter >= 2:
            failed.add(agent_state.last_recommended_direction) if agent_state.last_recommended_direction else None
        candidates = self._ordered(local_world.frontier_directions & local_world.walkable_directions, failed, agent_state)
        source = "frontier_policy"
        if not candidates:
            candidates = self._ordered(local_world.walkable_directions, failed, agent_state)
            source = "walkable_fallback"
        if not candidates and agent_state.last_successful_direction:
            candidates = [agent_state.last_successful_direction.opposite]
            source = "backtrack_policy"
        if not candidates:
            candidates = list(DIRECTION_ORDER)
            source = "deterministic_fallback"
        direction = local_world.recommended_direction if local_world.recommended_direction in candidates else candidates[0]
        return NextExplorationAction(direction, local_world.needs_probe, local_world.confidence, f"selected {direction.value} via {source}", source)

    def _ordered(self, directions: set[Direction], failed: set[Direction], agent_state: AgentStateDraft) -> list[Direction]:
        ordered = [d for d in DIRECTION_ORDER if d in directions and d not in failed]
        if agent_state.last_successful_direction and len(ordered) > 1:
            immediate_back = agent_state.last_successful_direction.opposite
            non_back = [d for d in ordered if d != immediate_back]
            return non_back or ordered
        return ordered
