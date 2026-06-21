"""MiniWorld cell types and text rendering symbols."""
from enum import Enum


class CellType(str, Enum):
    UNKNOWN = "unknown"
    WALL = "wall"
    FLOOR = "floor"
    DOOR = "door"
    PLAYER = "player"


CELL_TO_CHAR = {
    CellType.UNKNOWN: "?",
    CellType.WALL: "#",
    CellType.FLOOR: ".",
    CellType.DOOR: "+",
    CellType.PLAYER: "@",
}
CHAR_TO_CELL = {
    "#": CellType.WALL,
    ".": CellType.FLOOR,
    "+": CellType.DOOR,
    "@": CellType.FLOOR,
}
WALKABLE_CELLS = {CellType.FLOOR, CellType.DOOR, CellType.PLAYER}
