import json
import hashlib
import os

from models import Profile, GameState, Entity, Maze
from config import Difficulty, EntityKind, GameMode, SAVES_DIR, PROFILES_PATH

# Sử dụng đường dẫn từ config.py
GAMES_DIR = os.path.join(SAVES_DIR, "games")

# --- HELPER FUNCTIONS ---
def _hash_password(password: str) -> str:
    """Mã hóa mật khẩu."""
    return hashlib.sha256(password.encode()).hexdigest()

def _profile_to_dict(profile: Profile) -> dict:
    """Chuyển Profile sang dict để lưu JSON."""
    return {
        "username": profile.username,
        "display_name": profile.display_name,
        "password_hash": profile.password_hash,
        "current_save": profile.current_save,
        "total_time": profile.total_time,
        "unlocked_levels": profile.unlocked_levels,
        "best_steps": profile.best_steps,
        "options": profile.options
    }

def _dict_to_profile(data: dict) -> Profile:
    """Đọc dict từ JSON thành Profile."""
    p = Profile(
        username=data["username"],
        display_name=data["display_name"]
    )
    p.password_hash = data.get("password_hash", "")
    p.current_save = data.get("current_save", "")
    p.total_time = data.get("total_time", 0.0)
    p.unlocked_levels = data.get("unlocked_levels", ["level_01"])
    p.best_steps = data.get("best_steps", {})
    p.options = data.get("options", {"music_on": True, "sfx_on": True, "language": "vi"})
    return p

# --- API QUẢN LÝ PROFILE (Authentication) ---
def load_profiles():
    if not os.path.exists(PROFILES_PATH):
        return {}
    try:
        with open(PROFILES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {u: _dict_to_profile(info) for u, info in data.items()}
    except Exception:
        return {}

def save_profiles(profiles):
    data = {u: _profile_to_dict(p) for u, p in profiles.items()}
    with open(PROFILES_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def register(username: str, password: str, display_name: str):
    """Đăng ký user mới."""
    profiles = load_profiles()
    if username in profiles:
        return None # Trùng user
    
    new_profile = Profile(username=username, display_name=display_name)
    new_profile.password_hash = _hash_password(password)
    
    profiles[username] = new_profile
    save_profiles(profiles)
    return new_profile

def login(username: str, password: str):
    """Đăng nhập."""
    profiles = load_profiles()
    if username not in profiles:
        return None
    
    profile = profiles[username]
    if profile.password_hash == _hash_password(password):
        return profile
    return None

def get_guest_profile() -> Profile:
    return Profile(username="guest", display_name="Khách")

# --- SAVE / LOAD GAME SYSTEM ---
def save_game(profile: Profile, state: GameState, slot: int = 0):
    filename = f"{profile.username}_slot{slot}.json"
    filepath = os.path.join(GAMES_DIR, filename)
    
    enemies_data = []
    for e in state.enemies:
        enemies_data.append({"type": e.kind.name, "pos": e.pos, "alive": e.alive})

    save_data = {
        "level_id": getattr(state, "level_id", "level_01"),
        "difficulty": state.difficulty.value,
        "move_count": state.move_count,
        "status": state.status,
        "player": {"pos": state.player.pos, "alive": state.player.alive},
        "enemies": enemies_data
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, indent=4)
    
    profile.current_save = filename
    # Lưu profile để cập nhật current_save
    profs = load_profiles()
    if profile.username != "guest":
        profs[profile.username] = profile
        save_profiles(profs)

def load_game(profile: Profile, slot: int = 0) -> GameState | None:
    filename = f"{profile.username}_slot{slot}.json"
    filepath = os.path.join(GAMES_DIR, filename)
    
    if not os.path.exists(filepath):
        return None
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        player = Entity(EntityKind.PLAYER, tuple(data["player"]["pos"]), data["player"]["alive"])
        enemies = []
        for e in data["enemies"]:
            kind = getattr(EntityKind, e["type"], EntityKind.MUMMY_WHITE)
            enemies.append(Entity(kind, tuple(e["pos"]), e["alive"]))
            
        diff_str = data.get("difficulty", "normal")
        difficulty = next((d for d in Difficulty if d.value == diff_str), Difficulty.NORMAL)

        # Trả về State (Maze = None)
        state = GameState(
            maze=None, 
            player=player, 
            enemies=enemies, 
            mode=GameMode.CLASSIC, 
            difficulty=difficulty,
            move_count=data.get("move_count", 0),
            status=data.get("status", "RUNNING"),
            level_id=data.get("level_id", "level_01")
        )
        return state
    except Exception as e:
        print(f"Error loading save: {e}")
        return None
