import random
from collections import deque
from api.io.Lightning.entities.Enemy import EnemyAI
import api.io.Lightning.utils.ConfigFile as cf

class SimGate:
    def __init__(self, x, y, is_open):
        self.grid_x = x
        self.grid_y = y
        self.open = is_open
    def is_blocking(self):
        return not self.open

class MazeGenerator:
    def __init__(self):
        self.min_loops = 0

    def generate_level(self, difficulty, maze_size=None):
        config = self._get_config(difficulty)
        if maze_size:
            try:
                config['size'] = int(maze_size)
            except:
                pass
        
        size = config['size']
        attempts = 0
        max_attempts = 10 
        
        while attempts < max_attempts:
            attempts += 1
            walls_layout = self._generate_layout(size)
            self._braid_maze(walls_layout, size, config['braid_factor'])
            raw_walls = self._get_raw_walls(walls_layout, size)
            pruned = self._smart_prune_walls(raw_walls, size, config['wall_density'])
            
            level_data = self._place_entities(size, pruned, config)
            if not level_data:
                continue
            
            level_data['walls'] = self._merge_walls(level_data['walls'])
            
            if self._is_level_solvable(level_data, size):
                print(f"[Info] Map generated successfully (Size {size}, Diff {difficulty})")
                return level_data

        print(f"[Warning] Generator timed out. Using Fallback map.")
        return self._generate_fallback_level(size, difficulty)

    def _get_config(self, difficulty):
        if difficulty == 'easy':
            return {
                'size': 6,
                'min_enemies': 1,
                'max_enemies': 2,
                'enemy_pool': ['white_mummy', 'red_mummy', 'scorpion'],
                'traps': 0,
                'use_key_gate': False,
                'braid_factor': 0.1,
                'wall_density': 0.6,
                'difficulty_str': 'easy'
            }
        elif difficulty == 'hard':
            return {
                'size': 10,
                'min_enemies': 2,
                'max_enemies': 3,
                'enemy_pool': ['white_mummy', 'red_mummy', 'scorpion', 'red_scorpion'],
                'traps': 2,
                'use_key_gate': True,
                'braid_factor': 0.5,
                'wall_density': 0.55,
                'difficulty_str': 'hard'
            }
        
        # Medium config
        return {
            'size': 8,
            'min_enemies': 2,
            'max_enemies': 3,
            'enemy_pool': ['white_mummy', 'red_mummy', 'scorpion'],
            'traps': 1,
            'use_key_gate': True,
            'braid_factor': 0.3,
            'wall_density': 0.6,
            'difficulty_str': 'medium'
        }

    def _generate_fallback_level(self, size, difficulty):
        walls = []
        for i in range(size):
            walls.append({'x':i, 'y':-1, 'dir':'horizontal'})
        
        enemies = [{'type': 'white_mummy', 'x': size-1, 'y': 0}]
        
        return {
            "difficulty": "fallback", "mazeType": str(size), "maze_size": size,
            "player": {'x': 0, 'y': 0, 'direction': 'down'}, "exit": {'x': size-1, 'y': size-1},
            "enemies": enemies, "traps": [], "walls": walls, "key": None, "gate": None
        }

    def _place_entities(self, size, walls, config):
        occupied = set()
        
        # Exit placement
        side = random.randint(0, 3)
        if side == 0: exit_pos = {'x': random.randint(0, size - 1), 'y': -1} # Top
        elif side == 1: exit_pos = {'x': random.randint(0, size - 1), 'y': size} # Bottom
        elif side == 2: exit_pos = {'x': -1, 'y': random.randint(0, size - 1)} # Left
        else: exit_pos = {'x': size, 'y': random.randint(0, size - 1)} # Right

        win_x, win_y = self._exit_to_win_cell(exit_pos, size)
        occupied.add((win_x, win_y))

        # Player placement
        player_pos = None
        best_p_dist = -1
        
        start_candidates = []
        for _ in range(20):
            rx, ry = random.randint(0, size-1), random.randint(0, size-1)
            if (rx, ry) not in occupied:
                start_candidates.append((rx, ry))
        
        if not start_candidates:
            start_candidates = [(0,0)]

        for (px, py) in start_candidates:
            dist = self._get_path_distance((px, py), (win_x, win_y), walls, size)
            if dist > best_p_dist:
                best_p_dist = dist
                player_pos = {'x': px, 'y': py, 'direction': 'down'}
        
        if not player_pos: return None
        occupied.add((player_pos['x'], player_pos['y']))

        # Enemy placement
        enemies = []
        count = random.randint(config['min_enemies'], config['max_enemies'])
        
        safe_dist_base = 3 if size <= 6 else 5

        for _ in range(count):
            e_type = random.choice(config.get('enemy_pool', ['white_mummy']))
            best_e_pos = None
            max_tries = 30
            current_safe_dist = safe_dist_base

            while max_tries > 0:
                ex, ey = random.randint(0, size-1), random.randint(0, size-1)
                if (ex, ey) in occupied:
                    max_tries -= 1
                    continue
                
                dist_to_player = self._get_path_distance((ex, ey), (player_pos['x'], player_pos['y']), walls, size)
                
                if dist_to_player >= current_safe_dist:
                    best_e_pos = {'type': e_type, 'x': ex, 'y': ey}
                    break
                
                max_tries -= 1
                if max_tries % 10 == 0 and current_safe_dist > 2:
                    current_safe_dist -= 1
            
            if best_e_pos:
                enemies.append(best_e_pos)
                occupied.add((best_e_pos['x'], best_e_pos['y']))

        # Key and Gate
        key_data = None
        gate_data = None
        if config.get('use_key_gate'):
            start = (player_pos['x'], player_pos['y'])
            target = (win_x, win_y)
            base_path = self._find_path_cells(start, target, walls, size)
            candidates = []
            if base_path and len(base_path) >= 5:
                for i in range(2, len(base_path) - 2):
                    ax, ay = base_path[i - 1]
                    bx, by = base_path[i]
                    if ax == bx and abs(ay - by) == 1:
                        gx = ax
                        gy = max(ay, by)
                        if 1 <= gy <= size - 1:
                            if not self._check_wall(ax, ay, bx, by, walls):
                                candidates.append((gx, gy))
            
            if candidates:
                random.shuffle(candidates)
                gx, gy = candidates[0]
                gate_data = {'x': gx, 'y': gy}
                reachable = self._reachable_set(start, walls, size, gate_info=(gx, gy), gate_open=False)
                key_cands = [p for p in reachable if p not in occupied and p != start]
                if key_cands:
                    kx, ky = random.choice(key_cands)
                    key_data = {'x': kx, 'y': ky}
                    occupied.add((kx, ky))
                else:
                    gate_data = None

        # Traps
        traps = []
        for _ in range(config.get('traps', 0)):
            for _ in range(10):
                tx, ty = random.randint(0, size - 1), random.randint(0, size - 1)
                if (tx, ty) not in occupied:
                    traps.append({'x': tx, 'y': ty})
                    occupied.add((tx, ty))
                    break

        return {
            "difficulty": config['difficulty_str'],
            "mazeType": str(size),
            "maze_size": size,
            "player": player_pos,
            "exit": exit_pos,
            "enemies": enemies,
            "traps": traps,
            "walls": walls,
            "key": key_data,
            "gate": gate_data
        }

    # --- Pathfinding Helpers ---
    def _is_level_solvable(self, level, size):
        try:
            start = (int(level['player']['x']), int(level['player']['y']))
            wx, wy = self._exit_to_win_cell(level['exit'], size)
            target = (wx, wy)
        except: return None
        
        walls = level['walls']
        enemies = level['enemies']
        
        gate_info = (int(level['gate']['x']), int(level['gate']['y'])) if level['gate'] else None
        key_pos = (int(level['key']['x']), int(level['key']['y'])) if level['key'] else None
        
        traps = set()
        for t in level['traps']:
            traps.add((int(t['x']), int(t['y'])))
            
        if start in traps or target in traps: return None
        
        ai = EnemyAI(size, walls, gate=None)
        start_state = (start[0], start[1], (gate_info is None), tuple((e['x'], e['y']) for e in enemies))
        q = deque([start_state])
        visited = {start_state}
        
        steps = 0
        while q:
            steps += 1
            if steps > 2500: return None 
            
            curr = q.popleft()
            px, py, g_open, e_pos = curr
            if (px, py) == target: return True
            
            for dx, dy in [(0,0), (0,1), (0,-1), (1,0), (-1,0)]:
                nx, ny = px+dx, py+dy
                
                if not (0<=nx<size and 0<=ny<size): continue
                if (nx, ny) in traps: continue
                if self._check_wall(px, py, nx, ny, walls): continue
                if gate_info and not g_open and self._gate_blocks(px, py, nx, ny, gate_info, False): continue
                if (nx, ny) in e_pos: continue
                
                n_g_open = g_open
                if not g_open and key_pos and (nx, ny) == key_pos: n_g_open = True
                
                ai.gate = SimGate(gate_info[0], gate_info[1], n_g_open) if gate_info else None
                next_e_pos = []
                dead = False
                
                for i, ep in enumerate(e_pos):
                    sim_enemy = {'type': enemies[i]['type'], 'pos': [ep[0], ep[1]]}
                    path = ai.get_move_path(sim_enemy, [nx, ny], difficulty='medium')
                    
                    final_ep = path[-1] if path else list(ep)
                    if final_ep[0] == nx and final_ep[1] == ny: dead = True
                    next_e_pos.append(tuple(final_ep))
                
                if dead: continue
                
                next_state = (nx, ny, n_g_open, tuple(next_e_pos))
                if next_state not in visited:
                    visited.add(next_state)
                    q.append(next_state)
        return None

    def _generate_layout(self, size):
        grid = [[set() for _ in range(size)] for _ in range(size)]
        stack = [(0, 0)]
        visited = {(0, 0)}
        while stack:
            cx, cy = stack[-1]
            neighbors = []
            for dx, dy, d, opp in [(0, -1, 'N', 'S'), (0, 1, 'S', 'N'), (-1, 0, 'W', 'E'), (1, 0, 'E', 'W')]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < size and 0 <= ny < size and (nx, ny) not in visited:
                    neighbors.append((nx, ny, d, opp))
            if neighbors:
                nx, ny, d, opp = random.choice(neighbors)
                grid[cx][cy].add(d); grid[nx][ny].add(opp)
                visited.add((nx, ny)); stack.append((nx, ny))
            else: stack.pop()
        return grid

    def _braid_maze(self, grid, size, factor):
        dead_ends = [(x, y) for x in range(size) for y in range(size) if len(grid[x][y]) == 1]
        random.shuffle(dead_ends)
        for i in range(int(len(dead_ends) * factor)):
            cx, cy = dead_ends[i]
            neighbors = []
            for dx, dy, d, opp in [(0, -1, 'N', 'S'), (0, 1, 'S', 'N'), (-1, 0, 'W', 'E'), (1, 0, 'E', 'W')]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < size and 0 <= ny < size and d not in grid[cx][cy]:
                    neighbors.append((nx, ny, d, opp))
            if neighbors:
                nx, ny, d, opp = random.choice(neighbors)
                grid[cx][cy].add(d); grid[nx][ny].add(opp)

    def _get_raw_walls(self, grid, size):
        walls = []
        for x in range(size):
            for y in range(size):
                if 'N' not in grid[x][y]: walls.append({'x': x, 'y': y, 'dir': 'horizontal'})
                if 'W' not in grid[x][y]: walls.append({'x': x, 'y': y, 'dir': 'vertical'})
        return walls

    def _smart_prune_walls(self, walls, size, density):
        target = int((size * size) * density)
        if len(walls) <= target: return walls
        walls_copy = walls.copy()
        random.shuffle(walls_copy)
        removed = 0
        to_remove = len(walls) - target
        for w in walls_copy:
            if removed >= to_remove: break
            test = [x for x in walls if x != w]
            if self._is_maze_connected(test, size):
                walls.remove(w)
                removed += 1
        return walls

    def _is_maze_connected(self, walls, size):
        visited = {(0,0)}
        q = deque([(0,0)])
        while q:
            cx, cy = q.popleft()
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                nx, ny = cx+dx, cy+dy
                if 0<=nx<size and 0<=ny<size and (nx,ny) not in visited:
                    if not self._check_wall(cx, cy, nx, ny, walls):
                        visited.add((nx,ny))
                        q.append((nx,ny))
        return len(visited) == size * size

    def _merge_walls(self, walls):
        merged = {}
        for w in walls:
            key = (w['x'], w['y'])
            if key not in merged: merged[key] = w['dir']
            else: merged[key] = 'both'
        return [{'x': x, 'y': y, 'dir': d} for (x, y), d in merged.items()]

    def _exit_to_win_cell(self, exit_pos, size):
        if not exit_pos: return 0, 0
        ex, ey = int(exit_pos['x']), int(exit_pos['y'])
        return max(0, min(size - 1, ex)), max(0, min(size - 1, ey))

    def _reachable_set(self, start, walls, size, gate_info=None, gate_open=True):
        visited = {start}
        q = deque([start])
        while q:
            cx, cy = q.popleft()
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < size and 0 <= ny < size:
                    if (nx, ny) not in visited:
                        if not self._check_wall(cx, cy, nx, ny, walls) and \
                           not self._gate_blocks(cx, cy, nx, ny, gate_info, gate_open):
                            visited.add((nx, ny))
                            q.append((nx, ny))
        return visited

    def _find_path_cells(self, start, end, walls, size):
        q = deque([start])
        parent = {start: None}
        while q:
            curr = q.popleft()
            if curr == end:
                path = []
                while curr:
                    path.append(curr)
                    curr = parent[curr]
                return path[::-1]
            cx, cy = curr
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < size and 0 <= ny < size and (nx, ny) not in parent:
                    if not self._check_wall(cx, cy, nx, ny, walls):
                        parent[(nx, ny)] = curr
                        q.append((nx, ny))
        return None

    def _check_wall(self, x1, y1, x2, y2, walls):
        if x2 > x1: check = (x2, y2, 'vertical')
        elif x2 < x1: check = (x1, y1, 'vertical')
        elif y2 > y1: check = (x2, y2, 'horizontal')
        elif y2 < y1: check = (x1, y1, 'horizontal')
        else: return False
        
        for w in walls:
            if w['x'] == check[0] and w['y'] == check[1] and w['dir'] in [check[2], 'both']:
                return True
        return False

    def _get_path_distance(self, start, end, walls, size):
        q = deque([(start[0], start[1], 0)])
        visited = {start}
        while q:
            cx, cy, d = q.popleft()
            if (cx, cy) == end: return d
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                nx, ny = cx+dx, cy+dy
                if 0<=nx<size and 0<=ny<size and (nx,ny) not in visited:
                    if not self._check_wall(cx, cy, nx, ny, walls):
                        visited.add((nx,ny))
                        q.append((nx, ny, d+1))
        return -1

    def _gate_blocks(self, fx, fy, tx, ty, gate_info, gate_open):
        if not gate_info or gate_open: return False
        gx, gy = gate_info
        return ((fx == gx and fy == gy - 1 and tx == gx and ty == gy) or
                (fx == gx and fy == gy and tx == gx and ty == gy - 1))