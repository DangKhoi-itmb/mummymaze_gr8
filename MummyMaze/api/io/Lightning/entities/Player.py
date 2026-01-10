import pygame
import os
import random
from enum import Enum
from api.io.Lightning.entities.EntityLoader import Entity
from api.io.Lightning.manager.SoundReader import sfx_manager
from api.io.Lightning.utils.ConfigFile import ENTITIES_PATH, maze_coord_x, maze_coord_y

class PlayerState(Enum):
    IDLE = "idle"
    WALK = "walk"
    AFK_READMAP = "readmap"
    AFK_LIGHT = "light"
    AFK_SEARCH = "search"
    AFK_SHRUG = "shrug"
    DIE_WHITE_MUMMY = 'whitefight'
    DIE_RED_MUMMY = 'redfight'
    DIE_STUNG = "stung"
    DIE_TRAP = "freakout"

class Player(Entity):
    def __init__(self, x, y, maze_size, tile_size):
        super().__init__(x, y)
        self.maze_size = maze_size
        self.tile_size = tile_size
        self.target_x = x; self.target_y = y
        self.pixel_x = x * tile_size; self.pixel_y = y * tile_size
        self.move_speed = 2
        self.is_moving = False
        self.next_move_time = 0
        self.move_cooldown = 50
        self.state = PlayerState.IDLE
        self.direction = 'down'
        self.frame_index = 0
        self.animation_speed = 0.20
        self.animation_counter = 0
        self.last_input_time = pygame.time.get_ticks()
        self.afk_delay = 7000
        self.current_walk_variant = None
        self.animations = {}
        self._load_assets()

    def _load_assets(self):
        def load_img(name):
            for ext in [".png", ".gif"]:
                path = os.path.join(ENTITIES_PATH, f"{name}{self.maze_size}{ext}")
                if os.path.exists(path):
                    try: return pygame.image.load(path).convert_alpha()
                    except: pass
            return None

        def load_strip_square(sheet):
            if not sheet: return []
            w, h = sheet.get_size()
            fw = h
            count = w // fw
            return [sheet.subsurface((i * fw, 0, fw, h)) for i in range(count)]

        def load_grid_explorer(sheet):
            if not sheet: return {}
            w, h = sheet.get_size()
            cols, rows = 5, 4
            fw, fh = w // cols, h // rows
            anims = {'up': [], 'right': [], 'down': [], 'left': []}
            dirs = ['up', 'right', 'down', 'left']
            for row, d in enumerate(dirs):
                for col in range(cols):
                    anims[d].append(sheet.subsurface((col * fw, row * fh, fw, fh)))
            return anims

        sheet = load_img("explorer")
        if sheet:
            walks = load_grid_explorer(sheet)
            for d in ['up', 'right', 'down', 'left']:
                self.animations[f'walk_{d}'] = walks.get(d, [])

        # Load AFK & Death strips
        for state, name in [
            (PlayerState.AFK_READMAP, "readmap"), (PlayerState.AFK_LIGHT, "light"),
            (PlayerState.AFK_SEARCH, "search"), (PlayerState.AFK_SHRUG, "shrug"),
            (PlayerState.DIE_TRAP, "freakout"), (PlayerState.DIE_STUNG, "stung"),
            (PlayerState.DIE_RED_MUMMY, "redfight"), (PlayerState.DIE_WHITE_MUMMY, "whitefight")
        ]:
            self.animations[state] = load_strip_square(load_img(name))

    def is_ready(self):
        return (not self.is_moving and "DIE" not in self.state.name and 
                pygame.time.get_ticks() >= self.next_move_time)

    def is_anim_finished(self):
        anim = self.animations.get(self.state, [])
        return self.frame_index >= len(anim) - 1

    def handle_input(self):
        if not self.is_ready() and "AFK" not in self.state.name: return None
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = 1
        elif keys[pygame.K_UP] or keys[pygame.K_w]: dy = -1
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]: dy = 1
        elif keys[pygame.K_SPACE]: 
            self._reset_afk(); return (0, 0) # Wait
        
        if dx != 0 or dy != 0:
            self._reset_afk()
            return (dx, dy)
        return None

    def _reset_afk(self):
        self.last_input_time = pygame.time.get_ticks()
        if "AFK" in self.state.name:
            self.state = PlayerState.IDLE
            self.frame_index = 0

    def move_player(self, dx, dy):
        self.next_move_time = pygame.time.get_ticks() + self.move_cooldown
        if dx == 0 and dy == 0:
            self.state = PlayerState.IDLE
            self._reset_afk()
            return

        self.x += dx
        self.y += dy
        self.target_x = self.x * self.tile_size
        self.target_y = self.y * self.tile_size
        self.is_moving = True
        self.state = PlayerState.WALK
        self._reset_afk()
        self.current_walk_variant = sfx_manager.play_walk_start('player')
        
        if dx > 0: self.direction = 'right'
        if dx < 0: self.direction = 'left'
        if dy > 0: self.direction = 'down'
        if dy < 0: self.direction = 'up'

    def update(self):
        current_time = pygame.time.get_ticks()
        
        # Logic di chuyển
        if self.is_moving:
            if self.pixel_x < self.target_x: self.pixel_x = min(self.pixel_x + self.move_speed, self.target_x)
            elif self.pixel_x > self.target_x: self.pixel_x = max(self.pixel_x - self.move_speed, self.target_x)
            if self.pixel_y < self.target_y: self.pixel_y = min(self.pixel_y + self.move_speed, self.target_y)
            elif self.pixel_y > self.target_y: self.pixel_y = max(self.pixel_y - self.move_speed, self.target_y)

            if self.pixel_x == self.target_x and self.pixel_y == self.target_y:
                self.is_moving = False
                if self.current_walk_variant:
                    sfx_manager.play_walk_end('player', self.current_walk_variant)
                    self.current_walk_variant = None
                self.state = PlayerState.IDLE
                self.frame_index = 0
                self.last_input_time = current_time
        
        # Logic AFK
        elif self.state == PlayerState.IDLE:
            if current_time >= self.next_move_time:
                if current_time - self.last_input_time > self.afk_delay:
                    self._trigger_random_afk()

        # Update Animation
        key = f'walk_{self.direction}' if self.state in [PlayerState.WALK, PlayerState.IDLE] else self.state
        anim = self.animations.get(key, [])
        if not anim: return

        self.animation_counter += self.animation_speed
        if self.animation_counter >= 1.0:
            self.animation_counter = 0
            if self.state == PlayerState.WALK:
                self.frame_index = (self.frame_index + 1) % len(anim)
            elif "AFK" in self.state.name:
                if self.frame_index < len(anim) - 1: self.frame_index += 1
                else: 
                    self.state = PlayerState.IDLE
                    self.direction = 'down'
                    self.last_input_time = current_time
                    self.frame_index = 0
            elif "DIE" in self.state.name:
                if self.frame_index < len(anim) - 1: self.frame_index += 1

    def _trigger_random_afk(self):
        self.state = random.choice([PlayerState.AFK_READMAP, PlayerState.AFK_LIGHT, PlayerState.AFK_SEARCH, PlayerState.AFK_SHRUG])
        self.frame_index = 0

    def draw(self, surface):
        key = f'walk_{self.direction}' if self.state in [PlayerState.WALK, PlayerState.IDLE] else self.state
        anim = self.animations.get(key, [])
        if anim:
            idx = int(self.frame_index) if self.frame_index < len(anim) else 0
            img = anim[idx]
            dx = maze_coord_x + self.pixel_x + (self.tile_size - img.get_width()) // 2
            dy = maze_coord_y + self.pixel_y + (self.tile_size - img.get_height()) // 2
            surface.blit(img, (dx, dy))