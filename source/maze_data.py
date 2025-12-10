from pathlib import Path

from .models import Maze
from .config import CellType, DEFAULT_GRID_SIZE, LEVELS_DIR


def load_level_txt(name: str) -> Maze:
    """
    đọc level từ file text trong assets/levels.

    name: ví dụ "level_01" -> đọc file level_01.txt

    quy ước ký hiệu trong file:
      # = tường
      . = sàn
      S = start
      E = exit
    """
    path = LEVELS_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"level file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        # bỏ dòng trống, giữ nguyên chiều ngang
        lines = [line.rstrip("\n") for line in f if line.strip()]

    if not lines:
        raise ValueError(f"empty level file: {path}")

    height = len(lines)
    width = len(lines[0])

    # khởi tạo lưới cell mặc định là EMPTY
    grid: list[list[CellType]] = [
        [CellType.EMPTY for _ in range(width)] for _ in range(height)
    ]

    start = (0, 0)
    exit_ = (width - 1, height - 1)

    for y, line in enumerate(lines):
        if len(line) != width:
            # nếu có dòng nào độ dài khác thì coi như file lỗi
            raise ValueError("all lines in level must have same length")
        for x, ch in enumerate(line):
            if ch == "#":
                grid[y][x] = CellType.WALL
            elif ch == ".":
                grid[y][x] = CellType.EMPTY
            elif ch == "S":
                start = (x, y)
                grid[y][x] = CellType.EMPTY
            elif ch == "E":
                exit_ = (x, y)
                grid[y][x] = CellType.EXIT
            else:
                # ký tự lạ thì cứ coi là ô trống
                grid[y][x] = CellType.EMPTY

    return Maze(width=width, height=height, grid=grid, start=start, exit=exit_)


def create_dummy_maze() -> Maze:
    """
    mê cung dummy 6x6 toàn ô trống.
    chỉ dùng để debug nhanh khi chưa có file level.
    """
    w = h = DEFAULT_GRID_SIZE
    grid = [[CellType.EMPTY for _ in range(w)] for _ in range(h)]
    start = (0, 0)
    exit_ = (w - 1, h - 1)
    return Maze(width=w, height=h, grid=grid, start=start, exit=exit_)
