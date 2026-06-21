"""Canonical MiniWorld direction model.

Coordinate system: x increases east/right and y increases south/down.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional


class Direction(str, Enum):
    NORTH = "north"
    NORTHEAST = "northeast"
    EAST = "east"
    SOUTHEAST = "southeast"
    SOUTH = "south"
    SOUTHWEST = "southwest"
    WEST = "west"
    NORTHWEST = "northwest"

    @property
    def delta(self) -> tuple[int, int]:
        return DIRECTION_DELTAS[self]

    @property
    def opposite(self) -> "Direction":
        return OPPOSITE_DIRECTIONS[self]


DIRECTION_ORDER: tuple[Direction, ...] = (
    Direction.NORTH,
    Direction.NORTHEAST,
    Direction.EAST,
    Direction.SOUTHEAST,
    Direction.SOUTH,
    Direction.SOUTHWEST,
    Direction.WEST,
    Direction.NORTHWEST,
)

DIRECTION_DELTAS: dict[Direction, tuple[int, int]] = {
    Direction.NORTH: (0, -1),
    Direction.NORTHEAST: (1, -1),
    Direction.EAST: (1, 0),
    Direction.SOUTHEAST: (1, 1),
    Direction.SOUTH: (0, 1),
    Direction.SOUTHWEST: (-1, 1),
    Direction.WEST: (-1, 0),
    Direction.NORTHWEST: (-1, -1),
}

OPPOSITE_DIRECTIONS: dict[Direction, Direction] = {
    Direction.NORTH: Direction.SOUTH,
    Direction.NORTHEAST: Direction.SOUTHWEST,
    Direction.EAST: Direction.WEST,
    Direction.SOUTHEAST: Direction.NORTHWEST,
    Direction.SOUTH: Direction.NORTH,
    Direction.SOUTHWEST: Direction.NORTHEAST,
    Direction.WEST: Direction.EAST,
    Direction.NORTHWEST: Direction.SOUTHEAST,
}


def direction_from_delta(delta: tuple[int, int]) -> Optional[Direction]:
    for direction, candidate in DIRECTION_DELTAS.items():
        if candidate == delta:
            return direction
    return None
