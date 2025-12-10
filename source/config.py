from pathlib import Path
from enum import Enum, auto

# === cấu hình đường dẫn cơ bản ===

# thư mục gốc của project (folder MummyMaze)
BASE_DIR = Path(__file__).resolve().parent.parent

# thư mục assets: hình ảnh, âm thanh, level
ASSETS_DIR = BASE_DIR / "assets"
GFX_DIR = ASSETS_DIR / "gfx"
SFX_DIR = ASSETS_DIR / "sfx"
MUSIC_DIR = ASSETS_DIR / "music"
LEVELS_DIR = ASSETS_DIR / "levels"

# thư mục lưu dữ liệu người chơi
SAVES_DIR = BASE_DIR / "saves"
PROFILES_PATH = SAVES_DIR / "profiles.json"
GAMES_DIR = SAVES_DIR / "games"


def ensure_dirs() -> None:
    """
    hàm này đảm bảo các thư mục saves và games tồn tại.
    nếu chưa có thì tự tạo, tránh lỗi khi ghi file sau này.
    """
    SAVES_DIR.mkdir(exist_ok=True)
    GAMES_DIR.mkdir(exist_ok=True)


# === cài đặt game cơ bản ===

# kích thước mỗi ô (tile) khi vẽ trên màn hình
TILE_SIZE = 64

# số khung hình mỗi giây khi render pygame
FPS = 60

# các kích thước mê cung được hỗ trợ
GRID_SIZES = (6, 8, 10)
DEFAULT_GRID_SIZE = 6


# === enum cho loại ô, loại entity, mode, độ khó ===

class CellType(Enum):
    EMPTY = 0
    WALL = 1
    TRAP = 2
    EXIT = 3
    KEY = 4
    GATE_CLOSED = 5
    GATE_OPEN = 6


class EntityKind(Enum):
    PLAYER = auto()

    MUMMY_WHITE = auto()
    MUMMY_RED = auto()

    SCORPION_WHITE = auto()
    SCORPION_RED = auto()


class GameMode(Enum):
    CLASSIC = "classic"
    ADVENTURE = "adventure"
    RANDOM = "random"


class Difficulty(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
