"""Typed schemas for MiniWorld observation, planning, feedback, and memory."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Optional

from .cells import CellType
from .directions import Direction, DIRECTION_ORDER


@dataclass(frozen=True, order=True)
class Position:
    x: int
    y: int

    def moved(self, delta: tuple[int, int]) -> "Position":
        return Position(self.x + delta[0], self.y + delta[1])

    def delta_to(self, other: "Position") -> tuple[int, int]:
        return (other.x - self.x, other.y - self.y)


@dataclass
class Observation:
    visible_cells: dict[Position, CellType]
    explored_cells: set[Position]
    player_position: Position
    player_local_position: Position
    local_view_radius: int
    step_index: int

    def local_cell(self, direction: Direction) -> CellType:
        return self.visible_cells.get(self.player_position.moved(direction.delta), CellType.UNKNOWN)


@dataclass
class GroundTruth:
    full_map: tuple[tuple[CellType, ...], ...]
    player_position: Position
    walkable_neighbor_directions: set[Direction]
    blocked_neighbor_directions: set[Direction]
    frontier_cells: set[Position]
    explored_cells: set[Position]
    visible_cells: set[Position]
    coverage: float


@dataclass
class MovementResult:
    intended_direction: Direction
    previous_position: Position
    new_position: Position
    observed_delta: tuple[int, int]
    moved: bool
    blocked: bool
    reason: str
    step_index: int


@dataclass
class LocalWorldDraft:
    player_position_estimate: Optional[Position]
    walkable_directions: set[Direction]
    blocked_directions: set[Direction]
    frontier_directions: set[Direction]
    recommended_direction: Optional[Direction]
    confidence: float
    needs_probe: bool
    reason: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if self.recommended_direction is not None and self.recommended_direction not in DIRECTION_ORDER:
            raise ValueError("recommended_direction must be canonical or None")


@dataclass
class NextExplorationAction:
    direction: Direction
    is_probe: bool
    confidence: float
    reason: str
    source: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass
class DirectionValidationResult:
    intended_direction: Direction
    expected_delta: tuple[int, int]
    observed_delta: tuple[int, int]
    moved: bool
    agreement: bool
    agreement_score: float
    corrected_direction_guess: Optional[Direction]
    confidence_delta: float
    reason: str


@dataclass
class DirectionCalibrationStats:
    attempts: int = 0
    successes: int = 0
    failures: int = 0
    average_observed_delta: tuple[float, float] = (0.0, 0.0)

    @property
    def success_rate(self) -> float:
        return self.successes / self.attempts if self.attempts else 0.0

    def update(self, observed_delta: tuple[int, int], success: bool) -> None:
        self.attempts += 1
        if success:
            self.successes += 1
        else:
            self.failures += 1
        n = self.attempts
        self.average_observed_delta = (
            self.average_observed_delta[0] + (observed_delta[0] - self.average_observed_delta[0]) / n,
            self.average_observed_delta[1] + (observed_delta[1] - self.average_observed_delta[1]) / n,
        )


@dataclass
class AgentStateDraft:
    recent_actions: Deque[Direction] = field(default_factory=lambda: deque(maxlen=12))
    recent_observed_deltas: Deque[tuple[int, int]] = field(default_factory=lambda: deque(maxlen=12))
    failed_directions: set[Direction] = field(default_factory=set)
    stuck_counter: int = 0
    visited_cells: set[Position] = field(default_factory=set)
    direction_calibration: dict[Direction, DirectionCalibrationStats] = field(
        default_factory=lambda: {direction: DirectionCalibrationStats() for direction in DIRECTION_ORDER}
    )
    last_recommended_direction: Optional[Direction] = None
    last_successful_direction: Optional[Direction] = None
    repeated_position_count: int = 0
    step_index: int = 0

    def apply_feedback(self, action: NextExplorationAction, result: MovementResult, validation: DirectionValidationResult) -> None:
        self.recent_actions.append(action.direction)
        self.recent_observed_deltas.append(result.observed_delta)
        self.last_recommended_direction = action.direction
        self.step_index = result.step_index
        self.direction_calibration[action.direction].update(result.observed_delta, validation.agreement and result.moved)
        if result.new_position in self.visited_cells and result.moved:
            self.repeated_position_count += 1
        self.visited_cells.add(result.new_position)
        if validation.agreement and result.moved:
            self.stuck_counter = max(0, self.stuck_counter - 1)
            self.failed_directions.discard(action.direction)
            self.last_successful_direction = action.direction
        else:
            self.stuck_counter += 1
            self.failed_directions.add(action.direction)
