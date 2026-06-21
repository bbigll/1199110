from d2ai.miniworld.directions import Direction, DIRECTION_DELTAS, DIRECTION_ORDER
from d2ai.miniworld.env import MiniWorldEnv
from d2ai.miniworld.schemas import AgentStateDraft, NextExplorationAction, MovementResult, Position
from d2ai.miniworld.direction_validator import DirectionValidator
from d2ai.miniworld.local_world_builder import build_local_world_from_observation
from d2ai.miniworld.exploration_policy import ExplorationPolicy
from d2ai.miniworld.evaluator import Evaluator

SIMPLE = """
########
#@.....#
###.####
#......#
########
"""


def test_direction_deltas_and_opposites():
    assert DIRECTION_DELTAS == {
        Direction.NORTH: (0, -1), Direction.NORTHEAST: (1, -1), Direction.EAST: (1, 0), Direction.SOUTHEAST: (1, 1),
        Direction.SOUTH: (0, 1), Direction.SOUTHWEST: (-1, 1), Direction.WEST: (-1, 0), Direction.NORTHWEST: (-1, -1),
    }
    assert Direction.NORTH.opposite == Direction.SOUTH
    assert Direction.EAST.opposite == Direction.WEST


def test_deterministic_generation_and_episode():
    a = MiniWorldEnv(); b = MiniWorldEnv(); c = MiniWorldEnv()
    a.reset(7); b.reset(7); c.reset(8)
    assert a.render_map_text(reveal=True) == b.render_map_text(reveal=True)
    assert a.render_map_text(reveal=True) != c.render_map_text(reveal=True)
    actions = [Direction.EAST, Direction.EAST, Direction.SOUTH, Direction.WEST]
    a2 = MiniWorldEnv(); b2 = MiniWorldEnv(); a2.reset(3); b2.reset(3)
    assert [a2.step(d) for d in actions] == [b2.step(d) for d in actions]


def test_movement_open_wall_and_out_of_bounds():
    env = MiniWorldEnv.from_ascii(SIMPLE, view_radius=2); env.reset()
    result = env.step(Direction.EAST)
    assert result.moved and not result.blocked and result.observed_delta == (1, 0)
    wall = env.step(Direction.NORTH)
    assert not wall.moved and wall.blocked and wall.reason == "blocked_by_wall" and wall.observed_delta == (0, 0)
    edge = MiniWorldEnv.from_ascii("@#\n##", view_radius=1); edge.reset()
    oob = edge.step(Direction.NORTHWEST)
    assert not oob.moved and oob.reason == "out_of_bounds"


def test_observation_ground_truth_and_frontier_separation():
    env = MiniWorldEnv.from_ascii(SIMPLE, view_radius=1); obs = env.reset()
    truth = env.ground_truth()
    assert len(obs.visible_cells) < len(truth.full_map) * len(truth.full_map[0])
    assert len(truth.frontier_cells) > 0
    assert Direction.EAST in truth.walkable_neighbor_directions
    assert Direction.NORTH in truth.blocked_neighbor_directions


def test_local_world_builder_identifies_walkable_blocked_frontier():
    env = MiniWorldEnv.from_ascii(SIMPLE, view_radius=1); obs = env.reset()
    state = AgentStateDraft()
    local = build_local_world_from_observation(obs, state)
    assert Direction.EAST in local.walkable_directions
    assert Direction.NORTH in local.blocked_directions
    assert local.frontier_directions
    assert 0 <= local.confidence <= 1


def test_agent_state_and_direction_validator_updates():
    state = AgentStateDraft(); validator = DirectionValidator()
    action = NextExplorationAction(Direction.EAST, False, 1.0, "", "test")
    moved = MovementResult(Direction.EAST, Position(1, 1), Position(2, 1), (1, 0), True, False, "moved", 1)
    validation = validator.validate(action, moved)
    assert validation.agreement and validation.corrected_direction_guess == Direction.EAST
    state.apply_feedback(action, moved, validation)
    assert state.last_successful_direction == Direction.EAST
    assert state.direction_calibration[Direction.EAST].success_rate == 1.0
    blocked = MovementResult(Direction.NORTH, Position(2, 1), Position(2, 1), (0, 0), False, True, "blocked", 2)
    north = NextExplorationAction(Direction.NORTH, False, 1.0, "", "test")
    validation2 = validator.validate(north, blocked)
    state.apply_feedback(north, blocked, validation2)
    assert Direction.NORTH in state.failed_directions
    assert state.stuck_counter == 1
    assert state.recent_observed_deltas[-1] == (0, 0)


def test_validator_disagreement_corrected_guess():
    action = NextExplorationAction(Direction.NORTH, False, 1.0, "", "test")
    result = MovementResult(Direction.NORTH, Position(1, 1), Position(2, 1), (1, 0), True, False, "slipped", 1)
    validation = DirectionValidator().validate(action, result)
    assert not validation.agreement
    assert validation.corrected_direction_guess == Direction.EAST


def test_policy_prefers_frontier_avoids_failed_and_probe():
    env = MiniWorldEnv.from_ascii(SIMPLE, view_radius=1); obs = env.reset()
    state = AgentStateDraft(); local = build_local_world_from_observation(obs, state)
    action = ExplorationPolicy().choose_action(local, state)
    assert action.direction in local.frontier_directions
    assert action.is_probe == local.needs_probe
    state.failed_directions.add(action.direction)
    action2 = ExplorationPolicy().choose_action(local, state)
    if len(local.walkable_directions) > 1:
        assert action2.direction != action.direction


def test_policy_increases_coverage_and_avoids_obvious_wall():
    env = MiniWorldEnv.from_ascii(SIMPLE, view_radius=1)
    result = Evaluator(env).run_episode(seed=None, steps=8)
    assert result.metrics["exploration_coverage"] > 0.3
    assert result.metrics["number_of_successful_moves"] > result.metrics["number_of_failed_moves"]


def test_evaluator_metrics_are_complete_and_deterministic():
    r1 = Evaluator(MiniWorldEnv()).run_episode(seed=7, steps=20)
    r2 = Evaluator(MiniWorldEnv()).run_episode(seed=7, steps=20)
    assert r1.metrics == r2.metrics
    required = {"number_of_steps", "number_of_successful_moves", "number_of_failed_moves", "direction_agreement_rate", "stuck_rate", "exploration_coverage", "repeated_position_rate", "unique_positions_visited", "final_position", "final_stuck_counter", "frontier_action_count", "probe_action_count"}
    assert required <= set(r1.metrics)
