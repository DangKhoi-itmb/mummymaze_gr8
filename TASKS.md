# TASKS – Mummy Maze gr8

file này dùng để:
- chia 4 phần việc A/B/C/D cho 4 người
- mô tả rõ mỗi người phải làm gì
- chốt các hàm / modules cần giữ ổn định để code song song

> lưu ý: mọi người có thể tạo **stub** (hàm rỗng) trước cho người khác import, sau đó mới dần dần hoàn thiện.

---

## 0. kiến trúc + api chung (cả nhóm phải đọc)

### 0.1. data model (đã có sẵn trong `models.py`)

- `Maze`
- `Entity`
- `GameState`
- `Profile`
- `Coord = tuple[int, int]`
- `Direction = Literal["UP", "DOWN", "LEFT", "RIGHT", "STAY"]`
- `GameStatus = Literal["RUNNING", "WIN", "LOSE"]`

mọi module đều dùng chung các struct này, **không tự định nghĩa lại**.

### 0.2. các hàm “giao tiếp” giữa modules (api tối thiểu)

mỗi phần phụ trách implement, nhưng **tên hàm + kiểu trả về nên giữ như sau**:

- `maze_data.py`
  - `load_level_txt(name: str) -> Maze`
  - `generate_random_maze(width: int, height: int, difficulty: Difficulty) -> Maze`
  - `validate_maze(maze: Maze) -> tuple[bool, str]`  (true/false, kèm lí do nếu sai)

- `logic.py`
  - `create_game_for_level(level_name: str, difficulty: Difficulty) -> GameState`
  - `create_random_game(width: int, height: int, difficulty: Difficulty) -> GameState`
  - `apply_turn(state: GameState, direction: Direction) -> None`
    - 1 lượt: player đi + quái đi + cập nhật trạng thái
  - `undo(state: GameState) -> None`
  - `redo(state: GameState) -> None`

- `ai.py`
  - `shortest_path(maze: Maze, start: Coord, target: Coord) -> list[Coord] | None`
  - `update_enemies(state: GameState) -> None`  
    (gọi pathfinding, chọn nước đi cho từng enemy)

- `storage.py`
  - `load_profiles() -> dict[str, Profile]`
  - `save_profiles(profiles: dict[str, Profile]) -> None`
  - `register(username: str, password: str, display_name: str) -> Profile | None`
  - `login(username: str, password: str) -> Profile | None`
  - `save_game(profile: Profile, state: GameState, slot: int = 0) -> None`
  - `load_game(profile: Profile, slot: int = 0) -> GameState | None`

- `ui_pygame.py`
  - `run_game_loop() -> None` (entry cho main)
  - ui **chỉ gọi**:
    - `logic.create_game_for_level(...)` / `logic.create_random_game(...)`
    - `logic.apply_turn(state, direction)`
    - `logic.undo/redo(...)`
    - `storage.register/login/save_game/load_game`
  - ui **không tự gọi trực tiếp hàm ai**, việc gọi `update_enemies` nằm trong `logic.apply_turn`.

như vậy:
- A làm `maze_data` có thể chạy độc lập bằng test/print riêng.
- B làm `logic` chỉ cần dựa vào `Maze` và stub của `update_enemies`.
- C làm `ui_pygame` chỉ dựa vào api ở trên, không cần chờ ai hoàn tất.
- D làm `storage` + git/docs cũng có api riêng.

---

## phần A – maze & level & pathfinding cơ bản (0.25)

**vai trò:** thiết kế “world” cho game: level cố định, sinh maze random, kiểm tra hợp lệ, pathfinding cơ bản cho AI.

**file chính:** `maze_data.py`, một phần `ai.py`, một số file level trong `assets/levels/`.

### A.1. nhiệm vụ chính

1. **thiết kế format level file**

   - chọn ký hiệu cho tất cả thành phần:
     - `#` tường
     - `.` ô trống
     - `S` start (player)
     - `E` exit
     - `T` trap
     - `K` key
     - `G` gate đóng
     - `g` gate mở
     - ký hiệu spawn quái (ví dụ `M`, `R`, `C`, `c`…)
   - viết doc ngắn (ở cuối `maze_data.py` hoặc `docs/level_format.md`) mô tả ý nghĩa từng ký tự.

2. **hoàn thiện `load_level_txt(name: str) -> Maze`**

   - đang có bản đơn giản, cần mở rộng:
     - parse các ký hiệu mới (trap, key, gate, quái…)
     - kiểm tra:
       - tất cả dòng cùng chiều dài
       - có đúng 1 `S` và ít nhất 1 `E`
   - trả về `Maze`:
     - `grid[y][x]` chứa `CellType` đúng
     - `maze.start`, `maze.exit` đúng vị trí
   - thêm 1 cấu trúc tạm (nếu cần) để báo lại vị trí spawn enemies cho phần B/C/D (có thể lưu vào `Maze` hoặc trả riêng 1 dict).

3. **tạo 3 level cố định**

   - tạo `assets/levels/level_01.txt`, `level_02.txt`, `level_03.txt`.
   - thiết kế map:
     - khó dần
     - sử dụng trap / key / gate / quái
   - đảm bảo mỗi level:
     - có ít nhất 1 đường thắng
     - có đường để quái “bắt” player (phục vụ AI sau này).

4. **random maze generator**

   - cài hàm:

     ```python
     def generate_random_maze(width: int, height: int, difficulty: Difficulty) -> Maze:
         ...
     ```

   - yêu cầu:
     - dùng 1 thuật toán chuẩn (DFS/Prim/Kruskal) để tạo maze connected.
     - chọn start/exit hợp lý (không sát nhau).
     - rải trap/key/gate/enemy theo `difficulty`.
   - dùng BFS để kiểm tra chắc chắn có đường đi từ start đến exit.

5. **validator**

   - hàm:

     ```python
     def validate_maze(maze: Maze) -> tuple[bool, str]:
         ...
     ```

   - check:
     - chỉ dùng những `CellType` hợp lệ
     - có start/exit
     - có path start → exit
   - trả về `(False, "lí do")` nếu có gì sai, dùng cho debug.

6. **pathfinding cơ bản trong `ai.py`**

   - cài:

     ```python
     def shortest_path(maze: Maze, start: Coord, target: Coord) -> list[Coord] | None:
         ...
     ```

   - dùng BFS trên lưới ô (không cho đi xuyên tường / gate đóng).
   - viết 1 vài test nhỏ hoặc script debug để in ra đường đi.

### A.2. đầu ra tối thiểu

- 3 file level cố định chạy được với mini game.
- random generator ít nhất cho ra maze hợp lệ ở 1–2 cấu hình.
- hàm `shortest_path` dùng được để AI gọi.

---

## phần B – core logic & turn system & undo/redo (0.25)

**vai trò:** định nghĩa toàn bộ luật chơi: 1 lượt là gì, trap/key/gate hoạt động thế nào, thắng/thua, undo/redo.

**file chính:** `logic.py` (dùng `maze_data`, `ai`).

### B.1. nhiệm vụ chính

1. **turn system**

   - định nghĩa hàm:

     ```python
     def apply_turn(state: GameState, direction: Direction) -> None:
         """
         1 lượt chơi:
         - player di chuyển theo direction
         - gọi ai.update_enemies(state) cho enemy di chuyển
         - cập nhật trạng thái WIN/LOSE/RUNNING
         - lưu snapshot cho undo
         """
     ```

   - ui chỉ cần gọi `apply_turn`, không cần gọi `move_player` hoặc `update_enemies` trực tiếp.

2. **di chuyển player chi tiết**

   - mở rộng `move_player` bên trong:
     - check ô kế tiếp:
       - tường → không di chuyển
       - trap → di chuyển vào, set LOSE
       - key → nhặt key, đánh dấu trong `state` (ví dụ `state.has_key = True`)
       - gate đóng → nếu không có key thì không đi qua
       - gate mở → cho đi
       - exit → vào được nếu thỏa điều kiện (ví dụ đã xử lý key/gate)
   - nhớ cập nhật `move_count`.

3. **xử lý trap/key/gate**

   - thiết kế thêm field trong `GameState` nếu cần (ví dụ `has_key`, danh sách gate đã mở).
   - đảm bảo logic gate không làm “khóa” đường duy nhất của player (theo yêu cầu đề).
   - gọi SFX tương ứng (thông qua hàm helper ui sau này).

4. **win/lose**

   - hàm:

     ```python
     def check_win_lose(state: GameState) -> None:
         ...
     ```

   - check:
     - player đứng trên exit → WIN
     - player cùng ô với enemy hoặc bị enemy “đi qua” → LOSE
   - update `state.status`.

5. **undo/redo**

   - dùng `GameSnapshot` đã có:
     - mỗi `apply_turn` lưu 1 snapshot.
   - hàm:
     - `undo(state)` → lùi 1 snapshot
     - `redo(state)` → tiến 1 snapshot nếu còn
   - giới hạn số lượt undo (ví dụ 10), hoặc không giới hạn tùy nhóm.

6. **nhiều quái**

   - cấu trúc `state.enemies: list[Entity]`.
   - mỗi entity có `kind` để AI phân loại (mummy/scorpion).
   - logic check va chạm với tất cả quái.

### B.2. đầu ra tối thiểu

- `apply_turn` hoạt động được cho:
  - level cố định,
  - 1–2 enemy đơn giản (chưa cần AI khó).
- undo/redo hoạt động tối thiểu.
- `check_win_lose` đúng cho các trường hợp cơ bản.

---

## phần C – ui pygame + assets + audio (0.25)

**vai trò:** làm cho game chơi “sướng”: input, render, menu, HUD, âm thanh.

**file chính:** `ui_pygame.py`, quản lý `assets/`.

### C.1. nhiệm vụ chính

1. **refactor vòng lặp game**

   - trong `run_game_loop` tách thành 3 hàm:

     ```python
     def handle_events(state: GameState) -> bool: ...
     def update(state: GameState) -> None: ...
     def render(screen, state: GameState) -> None: ...
     ```

   - `handle_events`:
     - phím mũi tên / WASD → gọi `logic.apply_turn(state, direction)`
     - U → `logic.undo(state)`
     - R → `logic.redo(state)`
     - ESC → vào/thoát menu/pause
   - `update` sau này sẽ xử lý animation, timer…
   - `render` dùng `draw_grid` + vẽ HUD.

2. **menu & screen flow**

   - thiết kế đơn giản 2–3 “screen”:
     - main menu
     - in-game
     - pause menu
   - mỗi screen có vòng lặp riêng hoặc state machine nhỏ.

3. **HUD**

   - trên màn chơi hiển thị:
     - level name (vd `"level_01"`),
     - difficulty,
     - số bước,
     - trạng thái (RUNNING/WIN/LOSE).
   - dùng 1 font (có thể font mặc định hoặc thêm font vào `assets/fonts`).

4. **animation di chuyển cơ bản**

   - khi player di chuyển từ ô (x1, y1) tới (x2, y2):
     - thay vì nhảy ngay, chia thành vài frame (lerp).
   - có thể đơn giản: draw ở vị trí trung gian trong vòng lặp `update`.

5. **assets + audio**

   - đảm bảo `load_assets` load đúng tất cả file:
     - `assets/gfx/tiles/*.png`
     - `assets/gfx/chars/*.png`
     - `assets/sfx/*.wav`
     - `assets/music/bgm_main.ogg`
   - thêm các helper:
     - `play_move_sfx`, `play_trap_sfx`, `play_win_sfx`, …
   - áp dụng trong `logic` thông qua hàm gọi từ ui (có thể tách ra module `audio_helper` nếu muốn).

6. **tùy chọn bật/tắt nhạc/âm**

   - đọc `profile.options["music_on"]`, `["sfx_on"]`.
   - menu Options cho phép toggle 2 cái này.

### C.2. đầu ra tối thiểu

- main menu đơn giản (Play → vào level_01).
- in-game hiển thị HUD + di chuyển được + âm thanh cơ bản.
- menu pause / ESC hoạt động.

---

## phần D – login / profile / save + git & docs (0.25)

**vai trò:** quản lý người dùng, save/load game, giữ repo sạch, viết docs, hỗ trợ skeleton báo cáo.

**file chính:** `storage.py`, `README.md`, `TASKS.md`, cấu hình git.

### D.1. nhiệm vụ chính

1. **format profiles.json**

   - thiết kế cấu trúc:

     ```json
     {
       "username1": {
         "username": "username1",
         "display_name": "Tên hiển thị",
         "password_hash": "...",
         "unlocked_levels": ["level_01", "level_02"],
         "best_steps": {"level_01": 20, "level_02": 35},
         "options": {"music_on": true, "sfx_on": true, "language": "vi"}
       },
       ...
     }
     ```

   - triển khai hàm:
     - `load_profiles()`
     - `save_profiles(profiles)`

2. **register / login**

   - trong `storage.py`:

     ```python
     def register(username, password, display_name) -> Profile | None: ...
     def login(username, password) -> Profile | None: ...
     ```

   - hash password với `hashlib.sha256` (đơn giản là được).
   - xử lý case username đã tồn tại.

3. **save game / load game**

   - format file save: ví dụ `saves/games/<username>_slot0.json`.
   - thông tin tối thiểu cần lưu:
     - tên level / random seed
     - vị trí player
     - danh sách enemy + vị trí
     - grid maze / hoặc seed để tái tạo lại
     - move_count, status, difficulty
   - hàm:
     - `save_game(profile, state, slot=0)`
     - `load_game(profile, slot=0) -> GameState | None`
   - ui sẽ gọi 2 hàm này qua menu (Continue / Load game).

4. **tích hợp với UI**

   - phối hợp với C:
     - thêm màn hình login/register đơn giản.
     - sau khi login, profile được truyền vào `run_game_loop` hoặc global.

5. **git & docs**

   - giữ repo sạch:
     - `.gitignore` đầy đủ
     - hướng dẫn cách tạo nhánh, đặt tên commit (ghi trong README hoặc 1 mục nhỏ).
   - cập nhật `README.md` khi có thay đổi lớn:
     - thêm hướng dẫn login/save
   - chuẩn bị skeleton báo cáo LaTeX trên Overleaf:
     - mục: giới thiệu, kiến trúc, maze generator (A), logic & AI (B+C), hệ thống (D).
   - ghi rõ mỗi phần do ai phụ trách.

### D.2. đầu ra tối thiểu

- login guest + 1 user thật chạy được.
- load/save game ít nhất cho level cố định.
- README giải thích cách dùng tính năng này.

---

## 5. nguyên tắc làm việc song song

1. **giữ api ổn định**
   - nếu cần đổi tên hàm / đổi tham số, người phụ trách module đó **phải ping group** và update `TASKS.md`.
2. **mỗi người có thể tạo stub trước**
   - ví dụ B cần `ai.update_enemies` nhưng A chưa làm xong:
     - A tạo hàm rỗng `def update_enemies(state): pass` để B import được.
3. **branch theo tính năng**
   - mỗi phần A/B/C/D có thể tạo branch riêng:
     - `feature/maze`, `feature/logic`, `feature/ui`, `feature/storage`.
4. **review nhẹ trước khi merge**
   - ít nhất 1 bạn khác đọc qua PR, focus vào api và crash rõ ràng.

