"""ASCII map support for MiniWorld tests and demos."""
from __future__ import annotations

from .cells import CellType, CHAR_TO_CELL, CELL_TO_CHAR
from .schemas import Position


def parse_ascii_map(text: str) -> tuple[list[list[CellType]], Position]:
    lines = [line.rstrip("\n") for line in text.strip("\n").splitlines() if line.strip()]
    if not lines:
        raise ValueError("map must contain at least one row")
    width = len(lines[0])
    if any(len(line) != width for line in lines):
        raise ValueError("map rows must have equal width")
    spawn: Position | None = None
    grid: list[list[CellType]] = []
    for y, line in enumerate(lines):
        row = []
        for x, char in enumerate(line):
            if char == "@":
                if spawn is not None:
                    raise ValueError("map may contain only one player spawn")
                spawn = Position(x, y)
            if char == "?":
                raise ValueError("? is reserved for observation unknown cells")
            if char not in CHAR_TO_CELL:
                raise ValueError(f"unsupported map character: {char!r}")
            row.append(CHAR_TO_CELL[char])
        grid.append(row)
    if spawn is None:
        raise ValueError("map must include @ player spawn")
    return grid, spawn


def render_grid(grid: list[list[CellType]] | tuple[tuple[CellType, ...], ...], player: Position | None = None) -> str:
    rows = []
    for y, row in enumerate(grid):
        chars = []
        for x, cell in enumerate(row):
            chars.append("@" if player == Position(x, y) else CELL_TO_CHAR[cell])
        rows.append("".join(chars))
    return "\n".join(rows)
