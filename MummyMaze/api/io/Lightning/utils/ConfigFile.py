import os

# Thiết lập đường dẫn gốc của project
# Đi lên 4 cấp từ folder utils: utils -> Lightning -> io -> api -> MummyMaze
PROJECT_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "../../../..")
)

# Thiết lập các thư mục con
API_PATH = os.path.join(PROJECT_PATH, "api")
DIST_PATH = os.path.join(PROJECT_PATH, "dist")
RESOURCE_PATH = os.path.join(PROJECT_PATH, "resources")

# Thiết lập đường dẫn dữ liệu level
LEVELS_PATH = os.path.join(DIST_PATH, "levels")

# Thiết lập đường dẫn tài nguyên (Ảnh, Nhạc, UI)
ENTITIES_PATH = os.path.join(RESOURCE_PATH, "entities")
OBJECTS_PATH = os.path.join(RESOURCE_PATH, "objects")
UI_PATH = os.path.join(RESOURCE_PATH, "ui")
SOUNDS_PATH = os.path.join(RESOURCE_PATH, "sounds")
MUSIC_PATH = os.path.join(RESOURCE_PATH, "music")

# Tọa độ vẽ mê cung trên màn hình (để căn giữa)
maze_coord_x = 213
maze_coord_y = 80
fps = 60