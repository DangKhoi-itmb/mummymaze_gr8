from __future__ import annotations

from .models import GameState, GameSnapshot, Entity, Direction
from .config import EntityKind, GameMode, Difficulty, CellType
from .maze_data import load_level_txt, create_dummy_maze


def create_game_for_level(level_name: str) -> GameState:
    """
    tạo một GameState mới từ level cố định (đọc file text).

    hiện tại dùng cho việc: chơi level_01, level_02...
    sau này adventure mode sẽ gọi hàm này.
    """
    maze = load_level_txt(level_name)
    player = Entity(kind=EntityKind.PLAYER, pos=maze.start)
    enemies: list[Entity] = []

    state = GameState(
        maze=maze,
        player=player,
        enemies=enemies,
        mode=GameMode.ADVENTURE,
        difficulty=Difficulty.EASY,
    )
    _push_snapshot(state)  # lưu trạng thái ban đầu cho undo sau này
    return state


def create_dummy_gamestate() -> GameState:
    """
    tạo GameState dummy với mê cung rỗng.
    giữ lại để dùng debug nếu cần, không dùng trong game chính.
    """
    maze = create_dummy_maze()
    player = Entity(kind=EntityKind.PLAYER, pos=maze.start)
    enemies: list[Entity] = []
    state = GameState(
        maze=maze,
        player=player,
        enemies=enemies,
        mode=GameMode.ADVENTURE,
        difficulty=Difficulty.EASY,
    )
    _push_snapshot(state)
    return state


def _push_snapshot(state: GameState) -> None:
    """
    lưu một snapshot mới vào history.

    mỗi lần player chuẩn bị di chuyển (hoặc có thay đổi lớn),
    ta gọi hàm này để sau còn undo/redo được.
    """
    snap = GameSnapshot(
        maze=state.maze,
        player=Entity(kind=state.player.kind, pos=state.player.pos, alive=state.player.alive),
        enemies=[Entity(kind=e.kind, pos=e.pos, alive=e.alive) for e in state.enemies],
        move_count=state.move_count,
        status=state.status,
    )
    # nếu trước đó đã undo, cắt bỏ các snapshot "tương lai"
    state.history = state.history[: state.history_index + 1]
    state.history.append(snap)
    state.history_index += 1


def move_player(state: GameState, direction: Direction) -> None:
    """
    xử lý di chuyển người chơi 1 ô theo direction.

    - chặn ra ngoài biên
    - chặn đi xuyên tường
    - cập nhật vị trí và số bước
    - nếu đi vào ô EXIT thì set trạng thái WIN
    """
    if state.status != "RUNNING":
        # nếu đã win/lose rồi thì không cho di chuyển nữa
        return

    dx, dy = 0, 0
    if direction == "UP":
        dy = -1
    elif direction == "DOWN":
        dy = 1
    elif direction == "LEFT":
        dx = -1
    elif direction == "RIGHT":
        dx = 1
    elif direction == "STAY":
        dx = dy = 0

    if dx == dy == 0:
        # stay hiện tại chưa xử lý gì, sau này có thể coi là 1 lượt pass
        return

    x, y = state.player.pos
    nx, ny = x + dx, y + dy

    # check ra ngoài biên
    if not (0 <= nx < state.maze.width and 0 <= ny < state.maze.height):
        return

    cell = state.maze.grid[ny][nx]
    if cell == CellType.WALL:
        # gặp tường thì không đi được
        return

    # di chuyển hợp lệ: lưu snapshot trước rồi cập nhật
    _push_snapshot(state)

    state.player.pos = (nx, ny)
    state.move_count += 1

    if cell == CellType.EXIT:
        state.status = "WIN"


def undo(state: GameState) -> None:
    """
    quay lại 1 bước trước đó bằng snapshot trong history.

    hiện tại dùng tạm, sau này có thể mở rộng undo/redo nhiều bước.
    """
    if state.history_index <= 0:
        return

    state.history_index -= 1
    snap = state.history[state.history_index]

    state.maze = snap.maze
    state.player = snap.player
    state.enemies = snap.enemies
    state.move_count = snap.move_count
    state.status = snap.status
