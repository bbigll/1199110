"""Small deterministic room-and-corridor dungeon generator."""
from __future__ import annotations

import random

from .cells import CellType
from .schemas import Position


class DungeonGenerator:
    def __init__(self, width: int = 24, height: int = 16, room_count: int = 5) -> None:
        if width < 12 or height < 10:
            raise ValueError("MiniWorld dungeon must be at least 12x10")
        self.width = width
        self.height = height
        self.room_count = room_count

    def generate(self, seed: int | None = None) -> tuple[list[list[CellType]], Position]:
        rng = random.Random(seed)
        grid = [[CellType.WALL for _ in range(self.width)] for _ in range(self.height)]
        centers: list[Position] = []
        for _ in range(self.room_count):
            rw = rng.randint(3, 6)
            rh = rng.randint(3, 5)
            x1 = rng.randint(1, self.width - rw - 2)
            y1 = rng.randint(1, self.height - rh - 2)
            for y in range(y1, y1 + rh):
                for x in range(x1, x1 + rw):
                    grid[y][x] = CellType.FLOOR
            centers.append(Position(x1 + rw // 2, y1 + rh // 2))
        if not centers:
            centers = [Position(1, 1)]
            grid[1][1] = CellType.FLOOR
        for left, right in zip(centers, centers[1:]):
            x_step = 1 if right.x >= left.x else -1
            for x in range(left.x, right.x + x_step, x_step):
                grid[left.y][x] = CellType.FLOOR
            y_step = 1 if right.y >= left.y else -1
            door_y = left.y
            for y in range(left.y, right.y + y_step, y_step):
                grid[y][right.x] = CellType.FLOOR
            grid[door_y][right.x] = CellType.DOOR
        return grid, centers[0]
