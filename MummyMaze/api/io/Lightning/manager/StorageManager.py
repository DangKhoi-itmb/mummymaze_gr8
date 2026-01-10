import json
import hashlib
import os
from api.io.Lightning.utils.ConfigFile import PROJECT_PATH

class UserProfile:
    def __init__(self, username, display_name="", data=None):
        self.username = username
        self.display_name = display_name
        self.password_hash = ""
        # Default user data
        self.data = data or {
            "unlocked_levels": [1], 
            "best_scores": {},      # key: level_id (str), value: score (int)
            "options": {"music_on": True, "sfx_on": True, "language": "en"},
            "saved_game": None
        }

    def to_dict(self):
        return {
            "username": self.username,
            "display_name": self.display_name,
            "password_hash": self.password_hash,
            "data": self.data
        }

    @staticmethod
    def from_dict(d):
        # Create object from dictionary
        p = UserProfile(d.get("username", "guest"), d.get("display_name", "Guest"), d.get("data"))
        p.password_hash = d.get("password_hash", "")
        return p

class StorageManager:
    def __init__(self):
        # Set absolute paths
        self.data_dir = os.path.join(PROJECT_PATH, "data")
        self.save_dir = os.path.join(self.data_dir, "saves")
        self.profiles_path = os.path.join(self.data_dir, "profiles.json")
        
        self.current_user = None
        self._ensure_paths()

    def _ensure_paths(self):
        """Create necessary directories and files if they don't exist"""
        if not os.path.exists(self.data_dir): os.makedirs(self.data_dir)
        if not os.path.exists(self.save_dir): os.makedirs(self.save_dir)
        
        if not os.path.exists(self.profiles_path):
            with open(self.profiles_path, 'w') as f: json.dump({}, f)

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def _load_all_profiles(self):
        try:
            with open(self.profiles_path, 'r') as f: return json.load(f)
        except: return {}

    def _save_all_profiles(self, profiles_data):
        try:
            with open(self.profiles_path, 'w') as f: json.dump(profiles_data, f, indent=4)
        except Exception as e: print(f"Save Error: {e}")

    def login(self, username, password):
        profiles = self._load_all_profiles()
        if username not in profiles: return "User not found"
        
        user_data = profiles[username]
        # Check password
        if user_data.get("password_hash") != self._hash_password(password):
            return "Wrong password"

        self.current_user = UserProfile.from_dict(user_data)
        return "success"

    def register(self, username, password, display_name):
        if not username or not password: return "Empty fields"
        profiles = self._load_all_profiles()
        if username in profiles: return "Username exists"
        
        # Create new user
        new_user = UserProfile(username, display_name)
        new_user.password_hash = self._hash_password(password)
        
        # Save to DB
        profiles[username] = new_user.to_dict()
        self._save_all_profiles(profiles)
        
        self.current_user = new_user
        return "success"

    def save_current_user_progress(self):
        """Save current user data (unlocks, scores, saves)"""
        if not self.current_user: return
        profiles = self._load_all_profiles()
        profiles[self.current_user.username] = self.current_user.to_dict()
        self._save_all_profiles(profiles)

    def unlock_level(self, level_num):
        if not self.current_user: return
        if level_num not in self.current_user.data["unlocked_levels"]:
            self.current_user.data["unlocked_levels"].append(level_num)
            self.current_user.data["unlocked_levels"].sort()
            self.save_current_user_progress()

    def update_high_score(self, level_id, score):
        if not self.current_user: return
        lid = str(level_id)
        current = self.current_user.data["best_scores"].get(lid, 0)
        if score > current:
            self.current_user.data["best_scores"][lid] = score
            self.save_current_user_progress()

    def save_game_state(self, game_state_dict):
        if not self.current_user: return False
        self.current_user.data["saved_game"] = game_state_dict
        self.save_current_user_progress()
        return True

    def load_game_state(self):
        if not self.current_user: return None
        return self.current_user.data.get("saved_game")

    def has_saved_game(self):
        if not self.current_user: return False
        return self.current_user.data.get("saved_game") is not None

    def get_leaderboard_data(self, level_id, limit=5):
        """Retrieve top high scores for a specific level"""
        profiles = self._load_all_profiles()
        lid = str(level_id)
        ranking = []
        
        for username, p_data in profiles.items():
            if not isinstance(p_data, dict): continue
            
            dname = p_data.get("display_name", username)
            user_data = p_data.get("data", {})
            if not user_data: continue

            scores = user_data.get("best_scores", {})
            if not scores: continue

            score = scores.get(lid, 0)
            
            if score > 0:
                ranking.append({"name": dname, "score": score})
        
        # Sort descending by score
        ranking.sort(key=lambda x: x["score"], reverse=True)
        return ranking[:limit]

# Global instance
storage_manager = StorageManager()