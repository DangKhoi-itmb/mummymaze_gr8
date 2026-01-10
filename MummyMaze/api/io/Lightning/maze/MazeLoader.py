import os
import json
import pygame
import random
import math
from collections import deque

from api.io.Lightning.manager.SoundReader import sfx_manager
from api.io.Lightning.manager.Spritesheet import Spritesheet
from api.io.Lightning.maze.MazeGenerator import MazeGenerator
from api.io.Lightning.utils.ConfigFile import LEVELS_PATH, UI_PATH, OBJECTS_PATH, maze_coord_x, maze_coord_y
from api.io.Lightning.objects.Key import Key
from api.io.Lightning.objects.Gate import Gate
from api.io.Lightning.objects.Trap import Trap
from api.io.Lightning.entities.Enemy import Enemy

class FightEffect:
    def __init__(self, x, y, dust_frames, star_img, cell_size):
        self.x = x
        self.y = y
        self.cell_size = cell_size
        self.dust_frames = dust_frames
        self.frame_index = 0
        self.anim_speed = 0.45
        self.star_img = star_img
        self.stars = []
        if self.star_img:
            center = cell_size // 2
            for _ in range(5):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(1.5, 3.5)
                self.stars.append({'x': center, 'y': center, 'vx': math.cos(angle)*speed, 'vy': math.sin(angle)*speed-1, 'visible': False, 'spawn': random.randint(1,3)})
        self.finished = False

    def update(self):
        self.frame_index += self.anim_speed
        for s in self.stars:
            if self.frame_index >= s['spawn']:
                s['visible'] = True
                s['x'] += s['vx']
                s['y'] += s['vy']
                s['vx'] *= 0.95
                s['vy'] *= 0.95
        if self.frame_index >= len(self.dust_frames) + 3:
            self.finished = True

    def draw(self, surface):
        if self.finished: return
        idx = int(self.frame_index)
        if idx < len(self.dust_frames):
            img = self.dust_frames[idx]
            dx = maze_coord_x + self.x * self.cell_size + (self.cell_size - img.get_width()) // 2
            dy = maze_coord_y + self.y * self.cell_size + (self.cell_size - img.get_height()) // 2
            surface.blit(img, (dx, dy))
        if self.star_img:
            bx = maze_coord_x + self.x * self.cell_size
            by = maze_coord_y + self.y * self.cell_size
            for s in self.stars:
                if s['visible']:
                    surface.blit(self.star_img, (bx + int(s['x']) - self.star_img.get_width()//2, by + int(s['y']) - self.star_img.get_height()//2))

class MazeLoader:
    def __init__(self, level_id=None, difficulty='medium', generate_infinite=False, maze_size=None, saved_state=None):
        self.level_id = level_id
        self.difficulty = difficulty
        self.target_size = maze_size if maze_size else 8
        self.data = None
        self.parsed = None

        if saved_state:
            print("[System] Loading game from Save File...")
            self.parsed = saved_state 
            self.level_id = saved_state.get('level_id')
            self.difficulty = saved_state.get('difficulty')
            self.target_size = saved_state.get('maze_size', 8)
        
        elif generate_infinite:
            print(f"[System] Generating procedural level (Size: {self.target_size})...")
            gen = MazeGenerator()
            self.data = gen.generate_level(difficulty, maze_size=self.target_size)
            self.parsed = self._parse_level_data(self.data)
        else:
            self.data = self._load_level()
            self.parsed = self._parse_level_from_json()

        if not self.parsed:
            print("[Error] Failed to parse level data. Creating empty dummy level.")
            self.parsed = self._create_dummy_level(self.target_size)

        self.maze_pixel_size = 360
        self.maze_size = self.parsed.get("maze_size", self.target_size)
        self.stair_pos = self.parsed.get("exit")
        self.cell_size = self.maze_pixel_size // self.maze_size
        
        self.wall_sprites = {}
        self.stair_sprites = {}
        self.arrow_sprites = []
        self.dust_frames = []
        self.active_effects = []
        self.enemies_list = []
        self.traps = []
        self.key_obj = None
        self.gate_obj = None
        
        self.enemies_on_key = set()
        self.last_turn_time = 0
        self.history_stack = []
        self.pending_deaths = []
        self.turn_queue = deque()
        self.ankh_frames = []
        self.is_current_state_solvable = True
        self.generator_instance = MazeGenerator()
        self.ankh_timer = 0
        
        self._load_assets()
        self._create_objects()
        
        # Restore Gate Open state if loading
        if saved_state and self.gate_obj and saved_state.get('gate_open'):
            self.gate_obj.state = self.gate_obj.STATE_OPEN
            self.gate_obj.current_frame = len(self.gate_obj.frames) - 1

    def serialize_state(self, player):
        return {
            "level_id": self.level_id,
            "difficulty": self.difficulty,
            "maze_size": self.maze_size,
            "player": {"x": player.x, "y": player.y, "direction": player.direction},
            "enemies": [{'type': e.type, 'x': e.x, 'y': e.y, 'dir': e.direction} for e in self.enemies_list if not e.is_dead],
            "key": {'x': self.key_obj.grid_x, 'y': self.key_obj.grid_y} if self.key_obj else None,
            "gate": {'x': self.gate_obj.grid_x, 'y': self.gate_obj.grid_y} if self.gate_obj else None,
            "gate_open": not self.gate_obj.is_blocking() if self.gate_obj else True,
            "traps": [{'x': t.grid_x, 'y': t.grid_y} for t in self.traps],
            "walls": self.parsed['walls'],
            "exit": self.parsed['exit'],
            "is_custom": (self.level_id is None)
        }

    def _create_dummy_level(self, size):
        return {
            'difficulty': 'medium',
            'maze_size': size,
            'player': {'x': 0, 'y': 0, 'direction': 'down'},
            'exit': {'x': size-1, 'y': size-1},
            'enemies': [],
            'key': None,
            'gate': None,
            'traps': [],
            'walls': []
        }

    def _load_level(self):
        try:
            path = os.path.join(LEVELS_PATH, f'level_{self.level_id}.json')
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return json.load(f)
            else:
                print(f"[Error] File not found: {path}")
        except Exception as e:
            print(f"[Error] Error loading level file: {e}")
        return None

    def _parse_level_from_json(self):
        return self._parse_level_data(self.data)

    @staticmethod
    def _parse_level_data(data):
        if not data: return None
        mz_type = data.get('mazeType', 8)
        try:
            mz_size = int(mz_type)
        except:
            mz_size = 8
        return {
            'difficulty': data.get('difficulty', 'medium'),
            'maze_size': mz_size,
            'player': data.get('player'),
            'exit': data.get('exit'),
            'enemies': data.get('enemies', []),
            'key': data.get('key'),
            'gate': data.get('gate'),
            'traps': data.get('traps', []),
            'walls': data.get('walls', [])
        }

    def reset(self):
        self._create_objects()
        self.active_effects = []
        self.pending_deaths = []
        self.turn_queue.clear()
        self.is_current_state_solvable = True
        self.history_stack.clear()

    def save_state(self, player):
        state = {
            'player': {'x': player.x, 'y': player.y, 'dir': player.direction},
            'gate_open': not self.gate_obj.is_blocking() if self.gate_obj else True,
            'solvable': self.is_current_state_solvable,
            'enemies': [{'type': e.type, 'x': e.x, 'y': e.y, 'dir': e.direction} for e in self.enemies_list if not e.is_dead],
            'traps': [t.is_triggered for t in self.traps]
        }
        self.history_stack.append(state)

    def undo_last_move(self, player):
        if not self.history_stack: return False
        state = self.history_stack.pop()
        player.x = state['player']['x']
        player.y = state['player']['y']
        player.direction = state['player']['dir']
        player.target_x = player.x * player.tile_size
        player.target_y = player.y * player.tile_size
        player.pixel_x = player.target_x
        player.pixel_y = player.target_y
        player.is_moving = False
        
        if self.gate_obj:
            self.gate_obj.state = self.gate_obj.STATE_OPEN if state['gate_open'] else self.gate_obj.STATE_CLOSED
        
        self.is_current_state_solvable = state['solvable']
        self.enemies_list.clear()
        self.enemies_on_key.clear()
        
        for e in state['enemies']:
            en = Enemy(e['x'], e['y'], e['type'], self.maze_size, self.cell_size, self.parsed['walls'], self.gate_obj)
            en.direction = e['dir']
            self.enemies_list.append(en)
            
        for i, triggered in enumerate(state.get('traps', [])):
            if i < len(self.traps) and self.traps[i].is_triggered and not triggered:
                self.traps[i].reset()
        
        self.turn_queue.clear()
        self.pending_deaths.clear()
        self.active_effects.clear()
        return True

    def _create_objects(self):
        if self.parsed['key']:
            self.key_obj = Key(self.parsed['key']['x'], self.parsed['key']['y'], self.cell_size, self.maze_size)
        if self.parsed['gate']:
            self.gate_obj = Gate(self.parsed['gate']['x'], self.parsed['gate']['y'], self.cell_size, self.maze_size)
        self.traps = [Trap(t['x'], t['y'], self.cell_size, self.maze_size) for t in self.parsed['traps']]
        self.enemies_list = [Enemy(e['x'], e['y'], e['type'], self.maze_size, self.cell_size, self.parsed['walls'], self.gate_obj) for e in self.parsed['enemies']]

    def _load_assets(self):
        self.backdrop_img = pygame.image.load(os.path.join(UI_PATH, 'backdrop.jpg'))
        self.floor_img = pygame.image.load(os.path.join(OBJECTS_PATH, f'floor{self.maze_size}.jpg'))
        ws = Spritesheet(os.path.join(OBJECTS_PATH, f'walls{self.maze_size}.gif'))
        if self.maze_size == 6:
            self.wall_sprites['h'] = ws.get_image(12, 0, 72, 18)
            self.wall_sprites['v'] = ws.get_image(0, 0, 12, 78)
        elif self.maze_size == 8:
            self.wall_sprites['h'] = ws.get_image(12, 0, 57, 18)
            self.wall_sprites['v'] = ws.get_image(0, 0, 12, 63)
        elif self.maze_size == 10:
            self.wall_sprites['h'] = ws.get_image(8, 0, 44, 12)
            self.wall_sprites['v'] = ws.get_image(0, 0, 8, 48)
        else:
            self.wall_sprites['h'] = ws.get_image(0, 0, 1, 1)
            self.wall_sprites['v'] = ws.get_image(0, 0, 1, 1)

        ss = Spritesheet(os.path.join(OBJECTS_PATH, f"stairs{self.maze_size}.gif"))
        sw = ss.sheet.get_width() // 4
        sh = ss.sheet.get_height()
        self.stair_sprites = {'up': ss.get_image(0,0,sw,sh), 'right': ss.get_image(sw,0,sw,sh), 'down': ss.get_image(2*sw,0,sw,sh), 'left': ss.get_image(3*sw,0,sw,sh)}
        
        try:
            self.circle_img = pygame.image.load(os.path.join(UI_PATH, f'circle{self.maze_size}.png')).convert_alpha()
            aws = pygame.image.load(os.path.join(UI_PATH, f'arrows{self.maze_size}.png')).convert_alpha()
            aw, ah = aws.get_width(), aws.get_height() // 4
            self.arrow_sprites = [aws.subsurface((0, i*ah, aw, ah)) for i in [0, 2, 1, 3]]
        except:
            pass
        
        ankh = pygame.image.load(os.path.join(UI_PATH, 'ankh.png')).convert_alpha()
        for i in range(4):
            self.ankh_frames.append(ankh.subsurface((0, i*(ankh.get_height()//4), ankh.get_width(), ankh.get_height()//4)))
        
        self.star_img = pygame.image.load(os.path.join(UI_PATH, 'star.png')).convert_alpha()
        dpath = os.path.join(UI_PATH, f'dust{self.maze_size}.png')
        if not os.path.exists(dpath):
            dpath = os.path.join(UI_PATH, 'dust6.png')
        ds = pygame.image.load(dpath).convert_alpha()
        h = ds.get_height()
        for i in range(ds.get_width() // h):
            self.dust_frames.append(ds.subsurface((i*h, 0, h, h)))

    def get_solution_path(self, player):
        if not player: return None
        snap = {
            'player': {'x': player.x, 'y': player.y},
            'exit': self.parsed['exit'],
            'enemies': [{'type':e.type, 'x':e.x, 'y':e.y} for e in self.enemies_list if not e.is_dead],
            'walls': self.parsed['walls'],
            'traps': self.parsed['traps'],
            'gate': {'x': self.gate_obj.grid_x, 'y': self.gate_obj.grid_y} if self.gate_obj else None,
            'key': {'x': self.key_obj.grid_x, 'y': self.key_obj.grid_y} if self.key_obj else None,
            'difficulty': self.parsed['difficulty']
        }
        return self.generator_instance._is_level_solvable(snap, self.maze_size)

    def check_solvability(self, player):
        if not player: return
        was_solvable = self.is_current_state_solvable
        path = self.get_solution_path(player)
        self.is_current_state_solvable = (path is not None)
        if was_solvable and not self.is_current_state_solvable:
            sfx_manager.play('badankh')

    def draw_ankh(self, surface):
        if not self.ankh_frames: return
        base = 0 if self.is_current_state_solvable else 2
        surface.blit(self.ankh_frames[base], (90, 320))
        self.ankh_timer += 0.08
        alpha = int(((math.sin(self.ankh_timer) + 1) / 2) * 255)
        glow = self.ankh_frames[base+1].copy()
        glow.set_alpha(alpha)
        surface.blit(glow, (90, 320))

    def spawn_fight_cloud(self, x, y):
        self.active_effects.append(FightEffect(x, y, self.dust_frames, self.star_img, self.cell_size))

    def init_enemy_turn_sequence(self):
        active = [e for e in self.enemies_list if not e.is_dead]
        order = {'scorpion': 0, 'red_scorpion': 1, 'white_mummy': 2, 'red_mummy': 3}
        active.sort(key=lambda e: order.get(e.type, 99))
        self.turn_queue = deque(active)
        self.last_turn_time = 0

    def update_turn_sequence(self, player_pos):
        if any(e.paused for e in self.enemies_list): return False
        if any(e.is_moving or len(e.move_queue)>0 for e in self.enemies_list):
            self.last_turn_time = pygame.time.get_ticks()
            return False
        if self.pending_deaths: return False
        if pygame.time.get_ticks() - self.last_turn_time < 50: return False
        
        if not self.turn_queue: return True
        
        nxt = self.turn_queue[0]
        if nxt.is_dead or nxt not in self.enemies_list:
            self.turn_queue.popleft()
            return self.update_turn_sequence(player_pos)
            
        self.turn_queue.popleft()
        nxt.move_logic([player_pos[0], player_pos[1]], self.parsed['difficulty'])
        
        if not nxt.move_queue: return self.update_turn_sequence(player_pos)
        return False

    def trigger_enemy_afk(self):
        for e in self.enemies_list: e.trigger_afk()

    def pause_enemies(self):
        for e in self.enemies_list: e.paused = True
    def resume_enemies(self):
        for e in self.enemies_list: e.paused = False

    def resolve_enemy_collisions(self):
        pos_map = {}
        for e in self.enemies_list:
            if e.state.name == "DIE": continue
            p = (e.x, e.y)
            if p not in pos_map: pos_map[p] = []
            pos_map[p].append(e)
        
        col = False
        for p, ens in pos_map.items():
            if len(ens) > 1:
                sfx_manager.play('pummel')
                self.spawn_fight_cloud(p[0], p[1])
                ens.sort(key=lambda x: x.strength, reverse=True)
                self.pending_deaths.extend(ens[1:])
                col = True
        return col

    def process_pending_deaths(self):
        for v in self.pending_deaths: v.trigger_die(instant=True)
        self.pending_deaths.clear()

    def update(self):
        if self.key_obj: self.key_obj.update()
        if self.gate_obj: self.gate_obj.update()
        for t in self.traps: t.update()
        for e in self.enemies_list: e.update()
        self.enemies_list = [e for e in self.enemies_list if not e.is_dead]
        for eff in self.active_effects: eff.update()
        self.active_effects = [e for e in self.active_effects if not e.finished]
        
        if self.key_obj and self.gate_obj:
            kx, ky = self.key_obj.grid_x, self.key_obj.grid_y
            for e in self.enemies_list:
                if e.x == kx and e.y == ky:
                    if e not in self.enemies_on_key:
                        self.gate_obj.toggle()
                        self.key_obj.activate()
                        sfx_manager.play('gate')
                        self.enemies_on_key.add(e)
                else:
                    if e in self.enemies_on_key: self.enemies_on_key.remove(e)

    def draw_background(self, surface):
        surface.blit(self.backdrop_img, (0,0))
        surface.blit(self.floor_img, (maze_coord_x, maze_coord_y))

    def draw(self, surface, player=None, enemies=None, mouse_pos=None):
        self.draw_stairs(surface)
        for t in self.traps: t.draw(surface)
        
        current_enemies = enemies if enemies else self.enemies_list
        for row in range(self.maze_size + 1):
            if self.gate_obj and self.gate_obj.grid_y == row: self.gate_obj.draw(surface)
            self._draw_walls(surface, row)
            if self.key_obj and self.key_obj.grid_y == row: self.key_obj.draw(surface)
            
            if player and player.is_ready() and mouse_pos:
                mx, my = mouse_pos
                gx = (mx - maze_coord_x) // self.cell_size
                gy = (my - maze_coord_y) // self.cell_size
                if gy == row and 0 <= gx < self.maze_size:
                    dx, dy = gx - player.x, gy - player.y
                    if (gx, gy) == (player.x, player.y) and self.circle_img:
                        surface.blit(self.circle_img, (maze_coord_x + gx*self.cell_size, maze_coord_y + gy*self.cell_size))
                    elif abs(dx)+abs(dy)==1 and self.arrow_sprites:
                        blocked = False
                        for e in current_enemies:
                            if e.x == gx and e.y == gy: blocked = True
                        if not blocked and player.check_eligible_move(gx, gy, self.maze_size, self.parsed['walls'], self.gate_obj):
                            idx = 2 if dx==1 else 1 if dx==-1 else 0 if dy==1 else 3 
                            surface.blit(self.arrow_sprites[idx], (maze_coord_x + gx*self.cell_size, maze_coord_y + gy*self.cell_size))

            entities = []
            if player and player.y == row: entities.append(player)
            for e in current_enemies: 
                if e.y == row: entities.append(e)
            for t in self.traps:
                if t.grid_y == row and t.is_triggered: entities.append(t)
            
            entities.sort(key=lambda x: 1 if isinstance(x, Trap) else 0)
            
            for ent in entities:
                if isinstance(ent, Trap): ent.draw_active_block(surface)
                else: ent.draw(surface)
            
            for eff in self.active_effects:
                if eff.y == row: eff.draw(surface)

    def _draw_walls(self, surface, row):
        for w in self.parsed['walls']:
            if w['y'] != row: continue
            wx, d = w['x'], w['dir']
            bx = maze_coord_x + wx*self.cell_size
            by = maze_coord_y + row*self.cell_size
            ox, oy = int(self.cell_size*0.08), int(self.cell_size*0.27)
            dx, dy = bx - ox, by - oy
            
            if d in ['horizontal', 'both'] and row > 0:
                surface.blit(self.wall_sprites['h'], (dx, dy))
            if d in ['vertical', 'both'] and wx > 0:
                surface.blit(self.wall_sprites['v'], (dx, dy))

    def draw_stairs(self, surface):
        if not self.stair_pos: return
        gx, gy = self.stair_pos['x'], self.stair_pos['y']
        s = self.stair_sprites
        cx, cy = maze_coord_x, maze_coord_y
        cs = self.cell_size
        img = None
        dx, dy = 0, 0
        
        if gx >= self.maze_size - 1:
            img = s['right']
            dx = cx + self.maze_size * cs - (15 if gx < self.maze_size else 0)
            dy = cy + gy*cs + (cs-img.get_height())//2
        elif gx <= 0:
            img = s['left']
            dx = cx - img.get_width() + (15 if gx >= 0 else 0)
            dy = cy + gy*cs + (cs-img.get_height())//2
        elif gy <= 0:
            img = s['up']
            dx = cx + gx*cs + (cs-img.get_width())//2
            dy = cy - img.get_height() + (15 if gy >= 0 else 0)
        else:
            img = s['down']
            dx = cx + gx*cs + (cs-img.get_width())//2
            dy = cy + self.maze_size*cs - (15 if gy < self.maze_size else 0)
            
        if img:
            surface.blit(img, (dx, dy))

    def check_trap_collision(self, x, y):
        for t in self.traps:
            if t.check_collision(x, y): return t
        return None

    def check_key_collision(self, x, y):
        if self.key_obj and self.key_obj.check_collision(x, y):
            self.key_obj.activate()
            if self.gate_obj:
                self.gate_obj.toggle()
            sfx_manager.play('gate')
            return True
        return False

    def face_enemies_to_player(self, player):
        for e in self.enemies_list:
            if not e.is_moving and not e.is_dead and e.state.name != 'DIE':
                e.face_target(player.x, player.y)

    def get_win_cell(self):
        if not self.stair_pos: return None
        ex, ey = int(self.stair_pos['x']), int(self.stair_pos['y'])
        return max(0, min(self.maze_size - 1, ex)), max(0, min(self.maze_size - 1, ey))