from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Tuple, List, Dict, Any

from .config import CellType, EntityKind, GameMode, Difficulty

# kiểu toạ độ (x, y) cho ô trong mê cung
Coord = Tuple[int, int]

# hướng di chuyển của người chơi
Direction = Literal["UP", "DOWN", "LEFT", "RIGHT", "STAY"]

# trạng thái tổng thể của ván chơi
GameStatus = Literal["RUNNING", "WIN", "LOSE"]


@dataclass
class Maze:
    # thông tin mê cung: kích thước, lưới ô, vị trí start/exit
    width: int
    height: int
    grid: List[List[CellType]]
    start: Coord
    exit: Coord


@dataclass
class Entity:
    # một thực thể trong game: player, mummy, scorpion...
    kind: EntityKind
    pos: Coord
    alive: bool = True


@dataclass
class GameSnapshot:
    # ảnh chụp trạng thái game, dùng để undo/redo
    maze: Maze
    player: Entity
    enemies: List[Entity]
    move_count: int
    status: GameStatus


@dataclass
class GameState:
    # trạng thái hiện tại của ván chơi
    maze: Maze
    player: Entity
    enemies: List[Entity]

    mode: GameMode
    difficulty: Difficulty

    move_count: int = 0
    status: GameStatus = "RUNNING"

    # lịch sử các snapshot để undo/redo
    history: List[GameSnapshot] = field(default_factory=list)
    history_index: int = -1


@dataclass
class Profile:
    # thông tin tài khoản người chơi (sẽ dùng cho login sau này)
    username: str
    display_name: str
    level: int = 1
    exp: int = 0
    unlocked_levels: List[str] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=lambda: {
        "music_on": True,
        "sfx_on": True,
        "language": "vi",
    })
