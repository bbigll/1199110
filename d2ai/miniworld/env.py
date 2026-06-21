"""Deterministic grid MiniWorld environment."""
from __future__ import annotations

from .cells import CELL_TO_CHAR, CellType, WALKABLE_CELLS
from .directions import Direction, DIRECTION_ORDER
from .dungeon_generator import DungeonGenerator
from .maps import parse_ascii_map, render_grid
from .schemas import GroundTruth, MovementResult, Observation, Position


class MiniWorldEnv:
    def __init__(self, width: int = 24, height: int = 16, view_radius: int = 2, ascii_map: str | None = None) -> None:
        self.width = width
        self.height = height
        self.view_radius = view_radius
        self._ascii_map = ascii_map
        self._seed: int | None = None
        self.grid: list[list[CellType]] = []
        self.player_position = Position(0, 0)
        self.step_index = 0
        self.explored_cells: set[Position] = set()
        self.visible_cells: set[Position] = set()

    @classmethod
    def from_ascii(cls, ascii_map: str, view_radius: int = 2) -> "MiniWorldEnv":
        return cls(view_radius=view_radius, ascii_map=ascii_map)

    def reset(self, seed: int | None = None) -> Observation:
        self._seed = seed
        if self._ascii_map is None:
            self.grid, self.player_position = DungeonGenerator(self.width, self.height).generate(seed)
        else:
            self.grid, self.player_position = parse_ascii_map(self._ascii_map)
            self.height = len(self.grid)
            self.width = len(self.grid[0])
        self.step_index = 0
        self.explored_cells = set()
        self._update_visibility()
        return self.observe()

    def in_bounds(self, position: Position) -> bool:
        return 0 <= position.x < self.width and 0 <= position.y < self.height

    def cell_at(self, position: Position) -> CellType:
        if not self.in_bounds(position):
            return CellType.WALL
        return self.grid[position.y][position.x]

    def is_walkable(self, position: Position) -> bool:
        return self.in_bounds(position) and self.cell_at(position) in WALKABLE_CELLS

    def step(self, direction: Direction) -> MovementResult:
        previous = self.player_position
        candidate = previous.moved(direction.delta)
        self.step_index += 1
        if not self.in_bounds(candidate):
            reason = "out_of_bounds"
            moved = False
        elif not self.is_walkable(candidate):
            reason = "blocked_by_wall"
            moved = False
        else:
            reason = "moved"
            moved = True
            self.player_position = candidate
        self._update_visibility()
        return MovementResult(direction, previous, self.player_position, previous.delta_to(self.player_position), moved, not moved, reason, self.step_index)

    def _update_visibility(self) -> None:
        self.visible_cells = set()
        for y in range(self.player_position.y - self.view_radius, self.player_position.y + self.view_radius + 1):
            for x in range(self.player_position.x - self.view_radius, self.player_position.x + self.view_radius + 1):
                pos = Position(x, y)
                if self.in_bounds(pos):
                    self.visible_cells.add(pos)
        self.explored_cells.update(self.visible_cells)

    def observe(self) -> Observation:
        self._update_visibility()
        return Observation(
            visible_cells={pos: self.cell_at(pos) for pos in sorted(self.visible_cells)},
            explored_cells=set(self.explored_cells),
            player_position=self.player_position,
            player_local_position=Position(self.view_radius, self.view_radius),
            local_view_radius=self.view_radius,
            step_index=self.step_index,
        )

    def ground_truth(self) -> GroundTruth:
        walkable = {d for d in DIRECTION_ORDER if self.is_walkable(self.player_position.moved(d.delta))}
        blocked = set(DIRECTION_ORDER) - walkable
        frontier = self.frontier_cells()
        total_walkable = sum(1 for row in self.grid for cell in row if cell in WALKABLE_CELLS)
        explored_walkable = sum(1 for pos in self.explored_cells if self.cell_at(pos) in WALKABLE_CELLS)
        coverage = explored_walkable / total_walkable if total_walkable else 0.0
        return GroundTruth(tuple(tuple(row) for row in self.grid), self.player_position, walkable, blocked, frontier, set(self.explored_cells), set(self.visible_cells), coverage)

    def frontier_cells(self) -> set[Position]:
        frontiers = set()
        for pos in self.explored_cells:
            if self.cell_at(pos) not in WALKABLE_CELLS:
                continue
            for direction in DIRECTION_ORDER:
                neighbor = pos.moved(direction.delta)
                if self.in_bounds(neighbor) and neighbor not in self.explored_cells:
                    frontiers.add(pos)
                    break
        return frontiers

    def render_observation_text(self) -> str:
        obs = self.observe()
        rows = []
        for y in range(self.player_position.y - self.view_radius, self.player_position.y + self.view_radius + 1):
            chars = []
            for x in range(self.player_position.x - self.view_radius, self.player_position.x + self.view_radius + 1):
                pos = Position(x, y)
                if pos == self.player_position:
                    chars.append("@")
                elif pos in obs.visible_cells:
                    chars.append(CELL_TO_CHAR[obs.visible_cells[pos]])
                else:
                    chars.append("?")
            rows.append("".join(chars))
        return "\n".join(rows)

    def render_map_text(self, reveal: bool = False) -> str:
        if reveal:
            return render_grid(self.grid, self.player_position)
        rows = []
        for y, row in enumerate(self.grid):
            chars = []
            for x, cell in enumerate(row):
                pos = Position(x, y)
                if pos == self.player_position:
                    chars.append("@")
                elif pos in self.explored_cells:
                    chars.append(CELL_TO_CHAR[cell])
                else:
                    chars.append("?")
            rows.append("".join(chars))
        return "\n".join(rows)
