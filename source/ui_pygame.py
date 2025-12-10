import pygame
from pathlib import Path

from . import config
from .config import CellType, EntityKind
from .logic import create_game_for_level, move_player, undo
from .storage import get_guest_profile

# ==== biến global chứa asset đã load ====

TILE_IMAGES: dict[CellType, pygame.Surface] = {}
CHAR_IMAGES: dict[EntityKind, pygame.Surface] = {}

MOVE_SFX: pygame.mixer.Sound | None = None
NEAR_SFX: pygame.mixer.Sound | None = None
TRAP_SFX: pygame.mixer.Sound | None = None
GATE_SFX: pygame.mixer.Sound | None = None
WIN_SFX: pygame.mixer.Sound | None = None
LOSE_SFX: pygame.mixer.Sound | None = None


def load_image(path: Path, fallback_color: tuple[int, int, int]) -> pygame.Surface:
    """
    load một ảnh từ đường dẫn.

    nếu load thành công:
      - convert_alpha để hỗ trợ alpha
      - scale về đúng kích thước TILE_SIZE x TILE_SIZE
    nếu lỗi (file không tồn tại hoặc lỗi định dạng):
      - trả về 1 surface màu fallback để tránh game bị crash
    """
    surf = pygame.Surface((config.TILE_SIZE, config.TILE_SIZE), pygame.SRCALPHA)
    surf.fill(fallback_color)
    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, (config.TILE_SIZE, config.TILE_SIZE))
        return img
    except Exception:
        # nếu cần debug thì mở print ra
        # print(f"[warn] cannot load image: {path}")
        return surf


def load_sound(path: Path) -> pygame.mixer.Sound | None:
    """
    load một file âm thanh.

    nếu load ok thì trả về đối tượng Sound,
    nếu lỗi thì trả về None để chỗ khác kiểm tra trước khi play.
    """
    try:
        return pygame.mixer.Sound(path)
    except Exception:
        # print(f"[warn] cannot load sound: {path}")
        return None


def load_assets() -> None:
    """
    hàm này load tất cả image và sound cần dùng vào các dict global ở trên.

    đặt tên file trong assets sao cho khớp với phần này là xong,
    sau này đổi skin chỉ cần thay file chứ không phải sửa code.
    """
    global TILE_IMAGES, CHAR_IMAGES
    global MOVE_SFX, NEAR_SFX, TRAP_SFX, GATE_SFX, WIN_SFX, LOSE_SFX

    # --- tiles ---
    tiles_dir = config.GFX_DIR / "tiles"
    TILE_IMAGES = {
        CellType.EMPTY: load_image(tiles_dir / "floor.png", (30, 30, 60)),
        CellType.WALL: load_image(tiles_dir / "wall.png", (80, 80, 90)),
        CellType.TRAP: load_image(tiles_dir / "trap.png", (180, 40, 40)),
        CellType.EXIT: load_image(tiles_dir / "exit.png", (200, 200, 40)),
        CellType.KEY: load_image(tiles_dir / "key.png", (230, 200, 80)),
        CellType.GATE_CLOSED: load_image(tiles_dir / "gate_closed.png", (40, 120, 200)),
        CellType.GATE_OPEN: load_image(tiles_dir / "gate_open.png", (120, 200, 240)),
    }

    # --- characters ---
    chars_dir = config.GFX_DIR / "chars"
    CHAR_IMAGES = {
        EntityKind.PLAYER: load_image(chars_dir / "player.png", (40, 200, 40)),
        EntityKind.MUMMY_WHITE: load_image(chars_dir / "mummy_white.png", (220, 220, 220)),
        EntityKind.MUMMY_RED: load_image(chars_dir / "mummy_red.png", (220, 80, 80)),
        EntityKind.SCORPION_WHITE: load_image(chars_dir / "scorpion_white.png", (220, 220, 160)),
        EntityKind.SCORPION_RED: load_image(chars_dir / "scorpion_red.png", (220, 120, 80)),
    }

    # --- sounds ---
    MOVE_SFX = load_sound(config.SFX_DIR / "move.wav")
    NEAR_SFX = load_sound(config.SFX_DIR / "near_mummy.wav")
    TRAP_SFX = load_sound(config.SFX_DIR / "trap.wav")
    GATE_SFX = load_sound(config.SFX_DIR / "gate_toggle.wav")
    WIN_SFX = load_sound(config.SFX_DIR / "win.wav")
    LOSE_SFX = load_sound(config.SFX_DIR / "lose.wav")

    # --- music (nhạc nền) ---
    try:
        pygame.mixer.music.load(config.MUSIC_DIR / "bgm_main.ogg")
    except Exception:
        # nếu không load được nhạc thì thôi, game vẫn chạy bình thường
        # print("[warn] cannot load bgm_main.ogg")
        pass


def play_move_sfx() -> None:
    """
    play sound bước chân nếu MOVE_SFX đã được load.

    sau này mỗi lần player di chuyển xong có thể gọi hàm này.
    """
    if MOVE_SFX:
        MOVE_SFX.play()


def run_game_loop() -> None:
    """
    vòng lặp chính của game (phần pygame).

    - khởi động pygame, mixer
    - load assets
    - tạo GameState từ level_01
    - xử lý input người dùng
    - vẽ mê cung + player mỗi frame
    """
    # đảm bảo thư mục lưu trữ tồn tại
    config.ensure_dirs()

    pygame.init()
    pygame.mixer.init()

    load_assets()

    # tạm thời dùng profile guest, chưa có đăng nhập
    profile = get_guest_profile()  # noqa: F841  # chưa dùng đến nhưng giữ lại

    # tạo game state từ level_01
    state = create_game_for_level("level_01")

    width = state.maze.width * config.TILE_SIZE
    height = state.maze.height * config.TILE_SIZE

    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Mummy Maze - WIP")

    # bật nhạc nền nếu đã load được
    try:
        pygame.mixer.music.play(-1)  # loop forever
    except Exception:
        pass

    clock = pygame.time.Clock()
    running = True

    while running:
        # --- xử lý event ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # esc để thoát game
                    running = False
                elif event.key in (pygame.K_UP, pygame.K_w):
                    move_player(state, "UP")
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    move_player(state, "DOWN")
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    move_player(state, "LEFT")
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    move_player(state, "RIGHT")
                elif event.key == pygame.K_SPACE:
                    # stay: sau này dùng làm pass turn
                    move_player(state, "STAY")
                elif event.key == pygame.K_u:
                    # undo 1 bước
                    undo(state)

        # --- cập nhật logic quái, trạng thái... (chưa làm) ---

        # --- vẽ ---
        screen.fill((10, 10, 30))
        draw_grid(screen, state)
        pygame.display.flip()
        clock.tick(config.FPS)

    pygame.quit()


def draw_grid(screen: pygame.Surface, state) -> None:
    """
    vẽ toàn bộ mê cung và player lên màn hình.

    - mỗi ô trong maze.grid được vẽ bằng tile tương ứng
    - player vẽ chồng lên trên bằng sprite trong CHAR_IMAGES
    """
    tile = config.TILE_SIZE
    maze = state.maze

    # vẽ ô nền theo loại cell
    for y in range(maze.height):
        for x in range(maze.width):
            cell_type = maze.grid[y][x]
            img = TILE_IMAGES.get(cell_type, TILE_IMAGES[CellType.EMPTY])
            screen.blit(img, (x * tile, y * tile))

    # vẽ player
    px, py = state.player.pos
    player_img = CHAR_IMAGES.get(EntityKind.PLAYER)
    if player_img:
        screen.blit(player_img, (px * tile, py * tile))
