"""CLI demo for the deterministic MiniWorld observe-plan-act-validate-update loop."""
from __future__ import annotations

import argparse
import json

from .direction_validator import DirectionValidator
from .env import MiniWorldEnv
from .evaluator import Evaluator
from .exploration_policy import ExplorationPolicy
from .local_world_builder import build_local_world_from_observation
from .schemas import AgentStateDraft


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a deterministic d2ai MiniWorld Lab episode.")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--steps", type=int, default=50)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if not args.verbose:
        result = Evaluator().run_episode(seed=args.seed, steps=args.steps)
        print(json.dumps({"seed": args.seed, "steps": args.steps, "metrics": result.metrics}, indent=2, sort_keys=True))
        return

    env = MiniWorldEnv()
    observation = env.reset(args.seed)
    state = AgentStateDraft()
    state.visited_cells.add(observation.player_position)
    policy = ExplorationPolicy()
    validator = DirectionValidator()
    print(f"MiniWorld seed={args.seed} size={env.width}x{env.height} steps={args.steps}")
    for _ in range(args.steps):
        local_world = build_local_world_from_observation(observation, state)
        action = policy.choose_action(local_world, state)
        result = env.step(action.direction)
        validation = validator.validate(action, result)
        state.apply_feedback(action, result, validation)
        print(f"step={result.step_index} action={action.direction.value} moved={result.moved} delta={result.observed_delta} agreement={validation.agreement} stuck={state.stuck_counter}")
        print(env.render_observation_text())
        observation = env.observe()
    print(json.dumps(Evaluator(env).run_episode(args.seed, 0).metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
