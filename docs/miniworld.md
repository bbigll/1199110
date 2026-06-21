# MiniWorld Lab

MiniWorld Lab is a deterministic navigation cognition lab for d2ai. It is not a Diablo clone, a gameplay feature, or real game automation. It uses only text/grid data and no copyrighted assets.

The lab tests whether `next_exploration_action.direction` is meaningful by closing this loop:

1. `MiniWorldEnv.observe()` returns limited local visibility.
2. `build_local_world_from_observation()` creates a `LocalWorldDraft`.
3. `ExplorationPolicy.choose_action()` returns a `NextExplorationAction`.
4. `MiniWorldEnv.step()` executes 8-direction grid movement.
5. `DirectionValidator.validate()` compares intended and observed deltas.
6. `AgentStateDraft.apply_feedback()` updates short-term memory and direction calibration.
7. `Evaluator.run_episode()` records deterministic metrics.

## Coordinate system

`x` increases east/right and `y` increases south/down. Canonical direction order for deterministic tie-breaking is north, northeast, east, southeast, south, southwest, west, northwest.

## Observation vs GroundTruth

`Observation` exposes a local visible grid, explored cells, player position estimate, view radius, and step index. It does not expose the full map. `GroundTruth` exposes full map layout, exact player position, neighboring walkability, frontier cells, explored/visible cells, and coverage for tests and metrics only.

## Schemas

`LocalWorldDraft` records the agent's local navigation belief: player position estimate, walkable directions, blocked directions, frontier directions, optional recommendation, confidence, probe need, and debug reason.

`AgentStateDraft` records short-term memory: recent actions, recent observed deltas, failed directions, stuck counter, visited cells, per-direction calibration, last recommended/successful directions, repeated-position count, and step index.

`DirectionCalibrationStats` tracks attempts, successes, failures, average observed delta, and success rate per direction.

## DirectionValidator

The validator compares the intended direction delta with the movement result's observed delta. A north action agrees only with `(0, -1)`, east only with `(1, 0)`, and so on. Blocked movement with `(0, 0)` is a failed validation unless a future caller models it as an explicit blocked-probe test.

## ExplorationPolicy

The baseline policy is deterministic and explainable. It prefers frontier directions, then walkable directions, avoids recently failed directions, avoids immediate backtracking when alternatives exist, marks low-confidence choices as probes, and uses canonical direction order for tie-breaking.

## Evaluator metrics

Required metrics include step count, successful moves, failed moves, direction agreement rate, stuck rate, exploration coverage, repeated position rate, unique visited positions, final position, final stuck counter, frontier action count, and probe action count. Optional metrics include frontier selection rate, average confidence, average agreement score, longest stuck streak, and loop count.

## Running tests

```bash
python -m pytest tests/test_miniworld.py
```

## Running the demo

```bash
python -m d2ai.miniworld.demo --seed 7 --steps 50
python -m d2ai.miniworld.demo --seed 7 --steps 10 --verbose
```

## Future d2ai migration value

MiniWorld Lab gives d2ai a safe, deterministic place to test direction calibration, movement feedback, LocalWorld quality, AgentStateDraft memory, exploration policy changes, and coverage/regression metrics before connecting similar concepts to AI Eye or real integration layers. It intentionally does not send inputs to, scrape, or automate the real game.
