import pygame
import os
import random
from collections import deque
from enum import Enum
from api.io.Lightning.entities.EntityLoader import Entity
from api.io.Lightning.manager.SoundReader import sfx_manager
from api.io.Lightning.utils.ConfigFile import ENTITIES_PATH, maze_coord_x, maze_coord_y, UI_PATH, OBJECTS_PATH
from api.io.Lightning.utils.Pathfinder import Pathfinder

class EnemyAI:
    def __init__(self, maze_size, walls, gate=None):
        self.maze_size = maze_size
        self.walls = walls
        self.gate = gate

    def _is_valid_move_callback(self, curr, nxt):
        return Entity.validate_move(curr[0], curr[1], nxt[0], nxt[1], self.maze_size, self.walls, self.gate)

    def _is_valid_move(self, from_pos, to_pos):
        return Entity.validate_move(from_pos[0], from_pos[1], to_pos[0], to_pos[1], self.maze_size, self.walls, self.gate)

    def _get_classic_path(self, start_pos, target_pos, steps, priority="horizontal"):
        path = []
        cur_x, cur_y = start_pos
        target_x, target_y = target_pos
        for _ in range(steps):
            dist_x = target_x - cur_x
            dist_y = target_y - cur_y
            moved = False
            check = [('x', dist_x), ('y', dist_y)] if priority == "horizontal" else [('y', dist_y), ('x', dist_x)]
            
            for axis, dist in check:
                if axis == 'x' and dist != 0:
                    nx = cur_x + (1 if dist > 0 else -1)
                    if self._is_valid_move([cur_x, cur_y], [nx, cur_y]):
                        cur_x = nx; path.append([cur_x, cur_y]); moved = True; break
                elif axis == 'y' and dist != 0:
                    ny = cur_y + (1 if dist > 0 else -1)
                    if self._is_valid_move([cur_x, cur_y], [cur_x, ny]):
                        cur_y = ny; path.append([cur_x, cur_y]); moved = True; break
            if not moved: break
        return path

    def get_move_path(self, enemy, player_pos, difficulty='medium'):
        etype = enemy['type']
        curr = enemy['pos']
        # Hard Mode: Red Scorpion dùng A*
        if difficulty == 'hard' and 'red_scorpion' in etype:
            path = Pathfinder.astar_search(curr, player_pos, self.maze_size, self._is_valid_move_callback)
            if path: return path[:1]
            return []

        steps = 2 if 'mummy' in etype else 1
        if etype == 'white_mummy': return self._get_classic_path(curr, player_pos, steps, "horizontal")
        elif etype == 'red_mummy': return self._get_classic_path(curr, player_pos, steps, "vertical")
        else: return self._get_classic_path(curr, player_pos, 1, "horizontal")
        return []

class EnemyState(Enum):
    IDLE = "idle"; WALK = "walk"; DIE = "die"
    AFK_LISTEN = "listen"; AFK_DANCE = "dance"; AFK_SPIN = "spin"

class Enemy(Entity):
    def __init__(self, x, y, enemy_type, maze_size, tile_size, walls, gate=None):
        super().__init__(x, y)
        self.type = enemy_type; self.maze_size = maze_size; self.tile_size = tile_size
        self.ai = EnemyAI(maze_size, walls, gate)
        self.state = EnemyState.IDLE; self.direction = 'down'
        self.is_dead = False; self.strength = 0; self._set_stats()
        self.pixel_x = x * tile_size; self.pixel_y = y * tile_size
        self.target_x = self.pixel_x; self.target_y = self.pixel_y
        self.move_queue = deque(); self.move_speed = 3; self.is_moving = False
        self.paused = False; self.is_retreating = False; self.locked_direction = None
        self.is_turning = False; self.turn_timer = 0; self.current_walk_variant = None
        self.last_afk_time = 0; self.frame_index = 0; self.animation_speed = 0.05
        self.last_update_time = pygame.time.get_ticks(); self.animations = {}; self._load_assets()

    def _set_stats(self):
        if self.type == 'scorpion': self.strength = 1
        elif self.type == 'red_scorpion': self.strength = 2
        elif self.type == 'white_mummy': self.strength = 3
        elif self.type == 'red_mummy': self.strength = 4

    def _load_assets(self):
        def load_img(name):
            for folder in [ENTITIES_PATH, UI_PATH, OBJECTS_PATH]:
                for sz in [self.maze_size, 6, ""]:
                    for ext in [".png", ".gif"]:
                        path = os.path.join(folder, f"{name}{sz}{ext}")
                        if os.path.exists(path): return pygame.image.load(path).convert_alpha()
            return None
        def load_grid(sheet):
            if not sheet: return {'up': [], 'right': [], 'down': [], 'left': []}
            w, h = sheet.get_size(); fw, fh = w // 5, h // 4
            anims = {'up': [], 'right': [], 'down': [], 'left': []}
            for row, d in enumerate(['up', 'right', 'down', 'left']):
                for col in range(5): anims[d].append(sheet.subsurface((col * fw, row * fh, fw, fh)))
            return anims
        def load_strip(sheet):
            if not sheet: return []
            h = sheet.get_height(); count = sheet.get_width() // h
            return [sheet.subsurface((i * h, 0, h, h)) for i in range(count)]

        base_name = {'scorpion': 'scorpion', 'red_scorpion': 'redscorpion', 'white_mummy': 'mummy', 'red_mummy': 'redmummy'}.get(self.type, 'mummy')
        sheet = load_img(base_name)
        if not sheet and self.type == 'red_mummy':
            sheet = load_img('mummy')
            if sheet:
                tint = pygame.Surface(sheet.get_size(), pygame.SRCALPHA); tint.fill((255, 100, 100))
                sheet.blit(tint, (0, 0), special_flags=pygame.BLEND_MULT)
        if sheet:
            walks = load_grid(sheet)
            self.animations['walk_up'] = walks['up']; self.animations['walk_right'] = walks['right']
            self.animations['walk_down'] = walks['down']; self.animations['walk_left'] = walks['left']
        if 'mummy' in self.type:
            pre = "white" if self.type == 'white_mummy' else "red"
            self.animations[EnemyState.AFK_LISTEN] = load_strip(load_img(f"{pre}listen")) or load_strip(load_img("whitelisten"))
            self.animations[EnemyState.AFK_DANCE] = load_strip(load_img(f"{pre}dance")) or load_strip(load_img("whitedance"))
            self.animations[EnemyState.AFK_SPIN] = load_strip(load_img(f"{pre}spin")) or load_strip(load_img("whitespin"))
        self.animations[EnemyState.DIE] = load_strip(load_img("dust"))

    def move_logic(self, player_pos, difficulty='medium'):
        if self.state == EnemyState.DIE: return
        path = self.ai.get_move_path({'type': self.type, 'pos': [self.x, self.y]}, player_pos, difficulty)
        for step in path:
            if step != [self.x, self.y]: self.move_queue.append(step)

    def face_target(self, target_x, target_y):
        if self.is_dead: return
        dx = target_x - self.x; dy = target_y - self.y
        new_dir = self.direction
        if abs(dx) > abs(dy): new_dir = 'right' if dx > 0 else 'left'
        elif abs(dy) > abs(dx): new_dir = 'down' if dy > 0 else 'up'
        if new_dir != self.direction:
            self.direction = new_dir
            if not self.is_moving:
                self.is_turning = True; self.turn_timer = pygame.time.get_ticks(); self.state = EnemyState.WALK

    def retreat_to(self, target_x, target_y):
        self.is_retreating = True; self.locked_direction = self.direction
        self.move_queue.clear(); self.move_queue.append([target_x, target_y])

    def trigger_afk(self):
        if pygame.time.get_ticks() - self.last_afk_time < 14000: return
        if 'mummy' in self.type and not self.is_moving and not self.move_queue and self.state != EnemyState.DIE:
            self.state = random.choice([EnemyState.AFK_LISTEN, EnemyState.AFK_DANCE, EnemyState.AFK_SPIN]); self.frame_index = 0

    def trigger_die(self, instant=False):
        if instant: self.is_dead = True
        else: self.state = EnemyState.DIE; self.frame_index = 0; self.is_moving = False; self.move_queue.clear()

    def update(self):
        if self.is_turning:
            if pygame.time.get_ticks() - self.turn_timer > 50:
                self.is_turning = False
                if not self.is_moving and self.state == EnemyState.WALK: self.state = EnemyState.IDLE; self.frame_index = 0

        can_start = (not self.is_moving and self.move_queue and not self.paused)
        if can_start:
            next_pos = self.move_queue.popleft()
            dx, dy = next_pos[0] - self.x, next_pos[1] - self.y
            self.current_walk_variant = sfx_manager.play_walk_start(self.type)
            if not self.is_retreating:
                if dx > 0: self.direction = 'right'
                elif dx < 0: self.direction = 'left'
                elif dy > 0: self.direction = 'down'
                elif dy < 0: self.direction = 'up'
            elif self.locked_direction: self.direction = self.locked_direction
            self.x, self.y = next_pos
            self.target_x = self.x * self.tile_size; self.target_y = self.y * self.tile_size
            self.is_moving = True; self.state = EnemyState.WALK; self.is_turning = False

        if self.is_moving:
            if self.pixel_x < self.target_x: self.pixel_x = min(self.pixel_x + self.move_speed, self.target_x)
            elif self.pixel_x > self.target_x: self.pixel_x = max(self.pixel_x - self.move_speed, self.target_x)
            if self.pixel_y < self.target_y: self.pixel_y = min(self.pixel_y + self.move_speed, self.target_y)
            elif self.pixel_y > self.target_y: self.pixel_y = max(self.pixel_y - self.move_speed, self.target_y)

            if self.pixel_x == self.target_x and self.pixel_y == self.target_y:
                self.is_moving = False
                if self.current_walk_variant: sfx_manager.play_walk_end(self.type, self.current_walk_variant); self.current_walk_variant = None
                if not self.move_queue and not self.is_turning:
                    if self.state == EnemyState.WALK: self.state = EnemyState.IDLE
                if self.is_retreating: self.is_retreating = False; self.locked_direction = None

        current_time = pygame.time.get_ticks()
        if current_time - self.last_update_time > (self.animation_speed * 1000):
            self.last_update_time = current_time
            if self.state == EnemyState.WALK:
                anim = self.animations.get(f'walk_{self.direction}', [])
                if anim: self.frame_index = (self.frame_index + 1) % len(anim)
            elif self.state == EnemyState.IDLE:
                anim = self.animations.get(f'walk_{self.direction}', [])
                if anim: self.frame_index = 0
            elif "AFK" in self.state.name:
                anim = self.animations.get(self.state, [])
                if anim:
                    if self.frame_index < len(anim) - 1: self.frame_index += 1
                    else: self.state = EnemyState.IDLE; self.direction = 'down'; self.frame_index = 0
            elif self.state == EnemyState.DIE:
                anim = self.animations.get(self.state, [])
                if anim:
                    if self.frame_index < len(anim) - 1: self.frame_index += 1
                    else: self.is_dead = True

    def draw(self, surface):
        if self.is_dead: return
        key = f'walk_{self.direction}' if self.state in [EnemyState.WALK, EnemyState.IDLE] else self.state
        anim = self.animations.get(key, [])
        if anim:
            idx = int(self.frame_index) if self.frame_index < len(anim) else 0
            img = anim[idx]
            dx = maze_coord_x + self.pixel_x + (self.tile_size - img.get_width()) // 2
            dy = maze_coord_y + self.pixel_y + (self.tile_size - img.get_height()) // 2
            surface.blit(img, (dx, dy))