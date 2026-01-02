import json
import os
import hashlib

class UserProfile:
    def __init__(self, username, data=None):
        self.username = username
        self.data = data or {
            "unlocked_levels": 1,
            "high_scores": {}, # key: level_id, value: score
            "settings": {"music": 0.5, "sfx": 0.5}
        }

class StorageManager:
    def __init__(self):
        self.profiles_path = "data/profiles.json"
        self.current_user = None
        self._ensure_path()

    def _ensure_path(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.exists(self.profiles_path):
            with open(self.profiles_path, 'w') as f:
                json.dump({}, f)

    def login(self, username, password):
        # TODO: Implement hash check
        # Load profiles.json
        # If valid, self.current_user = UserProfile(username, data)
        print(f"Logging in as {username}...")
        return True

    def register(self, username, password):
        # TODO: Add new entry to json
        pass

    def save_game_progress(self, level_id, score):
        if not self.current_user: return
        # Update high score
        # Save back to json
        print(f"Saved progress: Level {level_id} - Score {score}")

# Global instance
storage_manager = StorageManager()