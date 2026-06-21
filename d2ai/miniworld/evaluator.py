"""Deterministic MiniWorld episode evaluator."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .direction_validator import DirectionValidator
from .env import MiniWorldEnv
from .exploration_policy import ExplorationPolicy
from .local_world_builder import build_local_world_from_observation
from .schemas import AgentStateDraft, Position


@dataclass
class EpisodeResult:
    metrics: dict[str, Any]
    final_map: str


class Evaluator:
    def __init__(self, env: MiniWorldEnv | None = None) -> None:
        self.env = env or MiniWorldEnv()
        self.policy = ExplorationPolicy()
        self.validator = DirectionValidator()

    def run_episode(self, seed: int | None, steps: int) -> EpisodeResult:
        observation = self.env.reset(seed)
        state = AgentStateDraft()
        state.visited_cells.add(observation.player_position)
        successes = failures = frontier_actions = probe_actions = agreements = 0
        agreement_scores: list[float] = []
        confidences: list[float] = []
        longest_stuck = 0
        for _ in range(steps):
            local_world = build_local_world_from_observation(observation, state)
            action = self.policy.choose_action(local_world, state)
            frontier_actions += int(action.source == "frontier_policy")
            probe_actions += int(action.is_probe)
            confidences.append(action.confidence)
            result = self.env.step(action.direction)
            validation = self.validator.validate(action, result)
            agreements += int(validation.agreement)
            agreement_scores.append(validation.agreement_score)
            successes += int(result.moved)
            failures += int(not result.moved)
            state.apply_feedback(action, result, validation)
            longest_stuck = max(longest_stuck, state.stuck_counter)
            observation = self.env.observe()
        truth = self.env.ground_truth()
        metrics = {
            "number_of_steps": steps,
            "number_of_successful_moves": successes,
            "number_of_failed_moves": failures,
            "direction_agreement_rate": agreements / steps if steps else 0.0,
            "stuck_rate": failures / steps if steps else 0.0,
            "exploration_coverage": truth.coverage,
            "repeated_position_rate": state.repeated_position_count / steps if steps else 0.0,
            "unique_positions_visited": len(state.visited_cells),
            "final_position": {"x": truth.player_position.x, "y": truth.player_position.y},
            "final_stuck_counter": state.stuck_counter,
            "frontier_action_count": frontier_actions,
            "probe_action_count": probe_actions,
            "frontier_selection_rate": frontier_actions / steps if steps else 0.0,
            "average_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
            "average_agreement_score": sum(agreement_scores) / len(agreement_scores) if agreement_scores else 0.0,
            "longest_stuck_streak": longest_stuck,
            "loop_count": state.repeated_position_count,
        }
        return EpisodeResult(metrics, self.env.render_map_text(reveal=False))
