import pygame
import os
from enum import Enum
from api.io.Lightning.gui.MapTracker import WorldMapPanel
from api.io.Lightning.manager.SoundReader import sfx_manager, music_manager
from api.io.Lightning.manager.TextDesigner import TextDesigner
from api.io.Lightning.maze.MazeLoader import MazeLoader
from api.io.Lightning.listener.AnimatedListener import initialize_torch_animation
from api.io.Lightning.utils.ConfigFile import *
from api.io.Lightning.manager.ButtonManager import ButtonManager
from api.io.Lightning.entities.Player import Player, PlayerState
from api.io.Lightning.manager.StorageManager import storage_manager

class TurnState(Enum):
    PLAYER_INPUT = 0
    PLAYER_MOVING = 1
    ENEMY_TURN = 2
    ENEMY_MOVING = 3
    PLAYER_DYING = 4
    FIGHT_PAUSE = 5

_button_manager = None
_torch_animation = None
_maze_loader = None
_maze_size = None
_player = None
_world_map = None
_turn_state = TurnState.PLAYER_INPUT
_death_timer = 0
_killer_ref = None
_death_step = 0
_death_step_timer = 0
_fight_pause_timer = 0
_show_options = False
_level_start_time = 0
_steps_taken = 0
_snake_img = None
_mumlogo_img = None
_msg_timer = 0
_status_msg = "" 

def _get_ui_images():
    global _snake_img, _mumlogo_img
    if _snake_img is None:
        _snake_img = pygame.image.load(os.path.join(UI_PATH, "snake.png")).convert_alpha()
    if _mumlogo_img is None:
        _mumlogo_img = pygame.image.load(os.path.join(UI_PATH, "mumlogo.png")).convert_alpha()
    return _snake_img, _mumlogo_img

def _reset_runtime_state(full_reset=True):
    global _turn_state, _death_timer, _killer_ref, _death_step, _death_step_timer, _fight_pause_timer, _show_options, _steps_taken, _level_start_time
    _turn_state = TurnState.PLAYER_INPUT
    _death_timer = 0
    _killer_ref = None
    _death_step = 0
    _death_step_timer = 0
    _fight_pause_timer = 0
    _show_options = False
    if full_reset:
        _steps_taken = 0
        _level_start_time = pygame.time.get_ticks()

def initialize_ui(mode="random", level_id=1, size=8, difficulty="medium", saved_state=None):
    global _button_manager, _torch_animation, _maze_loader, _player, _turn_state, _world_map, _snake_img, _mumlogo_img, _maze_size
    _snake_img = None
    _mumlogo_img = None
    
    if saved_state:
        size = saved_state.get('maze_size', 8)
    
    _maze_size = size
    _reset_runtime_state(full_reset=True)
    _button_manager = ButtonManager()
    _torch_animation = initialize_torch_animation()
    sfx_manager.initialize()
    music_manager.initialize()
    _world_map = WorldMapPanel(x=8, y=320)

    if saved_state:
        _maze_loader = MazeLoader(generate_infinite=False, saved_state=saved_state)
    elif mode == "campaign":
        print(f"Loading Campaign Level {level_id}...")
        _maze_loader = MazeLoader(level_id=level_id, difficulty=None, generate_infinite=False)
    else:
        print(f"Generating Random Level ({size}x{size})...")
        _maze_loader = MazeLoader(level_id=None, difficulty=difficulty, generate_infinite=True, maze_size=size)

    if _maze_loader and _maze_loader.parsed:
        p = _maze_loader.parsed["player"]
        _player = Player(p["x"], p["y"], _maze_loader.maze_size, _maze_loader.cell_size)
        if saved_state:
            _player.direction = p['direction']
    else:
        print("❌ CRITICAL ERROR: Could not load level data!")
    
    _turn_state = TurnState.PLAYER_INPUT

def handle_game_input(event, mouse_pos):
    global _button_manager, _player, _maze_loader, _turn_state, _show_options, _status_msg, _msg_timer
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            _show_options = not _show_options
            return "option"
    
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if _show_options:
            action = _check_options_click(mouse_pos)
            if action == "resume":
                _show_options = False
            elif action == "quit":
                return "quit"
            elif action == "save":
                if _maze_loader and _player:
                    state_data = _maze_loader.serialize_state(_player)
                    if storage_manager.save_game_state(state_data):
                        _status_msg = "GAME SAVED!"
                        _msg_timer = pygame.time.get_ticks()
            return None
        
        clicked_btn = None
        for name, rect in _button_manager.button_rects.items():
            if rect.collidepoint(mouse_pos):
                clicked_btn = name
                _button_manager.set_clicked(name)
                break
        
        if clicked_btn == "option":
            _show_options = True
            return "option"
        if clicked_btn == "quit":
            return "quit"
        if clicked_btn == "reset":
            restart_level()
            return "reset"
        if clicked_btn == "undo":
            undo_move()
            return "undo"
        
    if _show_options: return None
    
    if _turn_state == TurnState.PLAYER_INPUT:
        if _player and _maze_loader:
            move = _player.handle_input()
            if move:
                _execute_player_move(move[0], move[1])
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if _player and _maze_loader:
                mx, my = mouse_pos
                gx = (mx - maze_coord_x) // _maze_loader.cell_size
                gy = (my - maze_coord_y) // _maze_loader.cell_size
                if 0 <= gx < _maze_loader.maze_size and 0 <= gy < _maze_loader.maze_size:
                    dx = gx - _player.x
                    dy = gy - _player.y
                    if (abs(dx) + abs(dy) == 1) or (dx == 0 and dy == 0):
                        _execute_player_move(dx, dy)
    
    if event.type == pygame.MOUSEBUTTONUP:
        _button_manager.clear_clicked()
    return None

def _draw_options_menu(screen):
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    cx, cy = screen.get_width() // 2, screen.get_height() // 2
    rect = pygame.Rect(cx - 160, cy - 150, 320, 300)
    pygame.draw.rect(screen, (40, 30, 10), rect)
    pygame.draw.rect(screen, (150, 100, 50), rect, 4)
    
    designer = TextDesigner(size=32, color=(255, 215, 0))
    designer.render_header("OPTIONS", screen, cx, rect.y + 30)
    
    btn_designer = TextDesigner(size=24)
    mouse_pos = pygame.mouse.get_pos()
    
    btn_designer.draw_button(screen, "RESUME", cx, rect.y + 70, mouse_pos)
    btn_designer.draw_button(screen, "SAVE GAME", cx, rect.y + 110, mouse_pos)
    
    y_mus = rect.y + 160
    designer.render_default("MUSIC", screen, cx - 80, y_mus)
    btn_designer.draw_button(screen, "[-]", cx - 10, y_mus, mouse_pos)
    vol_mus = int(music_manager.get_volume() * 100)
    designer.render_default(f"{vol_mus}%", screen, cx + 40, y_mus, color=(200, 200, 200))
    btn_designer.draw_button(screen, "[+]", cx + 90, y_mus, mouse_pos)

    y_sfx = rect.y + 200
    designer.render_default("SFX", screen, cx - 80, y_sfx)
    btn_designer.draw_button(screen, "[-]", cx - 10, y_sfx, mouse_pos)
    vol_sfx = int(sfx_manager.get_volume() * 100)
    designer.render_default(f"{vol_sfx}%", screen, cx + 40, y_sfx, color=(200, 200, 200))
    btn_designer.draw_button(screen, "[+]", cx + 90, y_sfx, mouse_pos)

    btn_designer.draw_button(screen, "QUIT TO MENU", cx, rect.y + 260, mouse_pos)
    
    global _status_msg, _msg_timer
    if _status_msg:
        if pygame.time.get_ticks() - _msg_timer < 2000:
            succ_designer = TextDesigner(size=20, color=(0, 255, 0))
            succ_designer.render_default(_status_msg, screen, cx, rect.y + 285)
        else:
            _status_msg = ""

def _check_options_click(mouse_pos):
    cx, cy = 320, 240
    top_y = cy - 150 
    
    def is_center_btn(y):
        return (cx - 100 < mouse_pos[0] < cx + 100) and (y - 15 < mouse_pos[1] < y + 15)
    
    def is_small_btn(x, y):
        return (x - 20 < mouse_pos[0] < x + 20) and (y - 15 < mouse_pos[1] < y + 15)

    if is_center_btn(top_y + 70): return "resume"
    if is_center_btn(top_y + 110): return "save"
    
    y_mus = top_y + 160
    if is_small_btn(cx - 10, y_mus):
        v = music_manager.get_volume()
        music_manager.set_volume(max(0.0, v - 0.1))
        return "vol_change"
    if is_small_btn(cx + 90, y_mus): 
        v = music_manager.get_volume()
        music_manager.set_volume(min(1.0, v + 0.1))
        return "vol_change"

    y_sfx = top_y + 200
    if is_small_btn(cx - 10, y_sfx):
        v = sfx_manager.get_volume()
        sfx_manager.set_volume(max(0.0, v - 0.1))
        return "vol_change"
    if is_small_btn(cx + 90, y_sfx):
        v = sfx_manager.get_volume()
        sfx_manager.set_volume(min(1.0, v + 0.1))
        return "vol_change"

    if is_center_btn(top_y + 260): return "quit"
    return None

def _execute_player_move(dx, dy):
    global _player, _maze_loader, _turn_state, _steps_taken
    if not _player.is_ready(): return
    if dx == 0 and dy == 0:
        _maze_loader.save_state(_player); _player.move_player(0, 0); _turn_state = TurnState.ENEMY_TURN; _maze_loader.init_enemy_turn_sequence(); return
    tx = _player.x + dx; ty = _player.y + dy
    for e in _maze_loader.enemies_list:
        if e.x == tx and e.y == ty: return
    if _player.check_eligible_move(tx, ty, _maze_loader.maze_size, _maze_loader.parsed["walls"], _maze_loader.gate_obj):
        _maze_loader.save_state(_player); _player.move_player(dx, dy); _steps_taken += 1; _turn_state = TurnState.PLAYER_MOVING

def restart_level():
    global _player, _maze_loader, _turn_state; _reset_runtime_state(full_reset=True)
    if _maze_loader:
        _maze_loader.reset()
        if _maze_loader.parsed: p = _maze_loader.parsed["player"]; _player = Player(p["x"], p["y"], _maze_loader.maze_size, _maze_loader.cell_size)
    _turn_state = TurnState.PLAYER_INPUT; reset_input()

def undo_move():
    global _player, _maze_loader, _turn_state, _death_timer, _killer_ref, _steps_taken
    if _maze_loader and _player:
        if _maze_loader.undo_last_move(_player):
            _turn_state = TurnState.PLAYER_INPUT; _death_timer = 0; _killer_ref = None; _player.state = PlayerState.IDLE; _player.frame_index = 0; _steps_taken = max(0, _steps_taken - 1)

def reset_input():
    if _button_manager: _button_manager.clear_clicked()

def _is_win():
    global _maze_loader, _player
    if not _maze_loader or not _player: return False
    win = _maze_loader.get_win_cell()
    if not win: return False
    return (_player.x == win[0] and _player.y == win[1])

def draw_screen(screen, hovered=None, clicked=None, draw_mumlogo=True, mumlogo_y=None):
    global _torch_animation, _maze_loader, _player, _turn_state, _death_step, _death_step_timer, _fight_pause_timer, _killer_ref
    snake, mumlogo = _get_ui_images()
    if not _show_options and _player and _maze_loader:
        _player.update(); _maze_loader.update()
        if _turn_state == TurnState.PLAYER_MOVING:
            if not _player.is_moving:
                _maze_loader.check_key_collision(_player.x, _player.y)
                if _maze_loader.check_trap_collision(_player.x, _player.y): _maze_loader.pause_enemies(); _player.state = PlayerState.DIE_TRAP; _player.frame_index = 0; _turn_state = TurnState.PLAYER_DYING; _death_step = 3; _death_step_timer = 0; _killer_ref = None; return None
                if _is_win():
                    elapsed_ms = pygame.time.get_ticks() - _level_start_time
                    # --- CÔNG THỨC TÍNH ĐIỂM CHUẨN ---
                    score = max(0, 10000 - (elapsed_ms // 100) - (_steps_taken * 50))
                    return ("win", score, elapsed_ms)
                _turn_state = TurnState.ENEMY_TURN; _maze_loader.init_enemy_turn_sequence()
        elif _turn_state == TurnState.ENEMY_TURN:
            for e in _maze_loader.enemies_list: e.prev_x = e.x; e.prev_y = e.y
            _maze_loader.init_enemy_turn_sequence(); _turn_state = TurnState.ENEMY_MOVING
        elif _turn_state == TurnState.ENEMY_MOVING:
            kill = False
            for e in _maze_loader.enemies_list:
                if e.x == _player.x and e.y == _player.y: sfx_manager.play("pummel"); e.move_queue.clear(); _killer_ref = e; _maze_loader.spawn_fight_cloud(_player.x, _player.y); _killer_ref.face_target(_player.x, _player.y); _turn_state = TurnState.PLAYER_DYING; _death_step = 1; _death_step_timer = pygame.time.get_ticks(); kill = True; break
            if not kill:
                if _maze_loader.resolve_enemy_collisions(): _maze_loader.pause_enemies(); _turn_state = TurnState.FIGHT_PAUSE; _fight_pause_timer = pygame.time.get_ticks()
                else:
                    if _maze_loader.update_turn_sequence(_player.get_pos()): _maze_loader.face_enemies_to_player(_player); _turn_state = TurnState.PLAYER_INPUT; _player.last_input_time = pygame.time.get_ticks(); _maze_loader.check_solvability(_player)
        elif _turn_state == TurnState.FIGHT_PAUSE:
            if pygame.time.get_ticks() - _fight_pause_timer > 500: _maze_loader.process_pending_deaths(); _maze_loader.resume_enemies(); _turn_state = TurnState.ENEMY_MOVING
        elif _turn_state == TurnState.PLAYER_DYING:
            now = pygame.time.get_ticks()
            if _death_step == 1:
                if now - _death_step_timer > 550:
                    if _killer_ref and "scorpion" in _killer_ref.type: _killer_ref.retreat_to(_killer_ref.prev_x, _killer_ref.prev_y); _death_step = 2
                    else:
                        if _killer_ref and "mummy" in _killer_ref.type: _player.state = (PlayerState.DIE_RED_MUMMY if _killer_ref.type == "red_mummy" else PlayerState.DIE_WHITE_MUMMY); 
                        if _killer_ref in _maze_loader.enemies_list: _maze_loader.enemies_list.remove(_killer_ref)
                        _player.frame_index = 0; _death_step = 3
            elif _death_step == 2:
                if _killer_ref and not _killer_ref.is_moving: _player.state = PlayerState.DIE_STUNG; sfx_manager.play("poison"); _player.frame_index = 0; _death_step = 3; _death_step_timer = now
            elif _death_step == 3:
                anim = _player.animations.get(_player.state, [])
                if anim and _player.frame_index >= len(anim) - 1:
                    if _death_step_timer == 0: _death_step_timer = now
                    if now - _death_step_timer > 1000: return "lose"
        elif _turn_state == TurnState.PLAYER_INPUT:
            if "AFK" in _player.state.name: _maze_loader.trigger_enemy_afk()

    if _maze_loader: _maze_loader.draw_background(screen)
    if _torch_animation and _torch_animation.loaded and _maze_loader:
        _torch_animation.update(); ms = _maze_loader.maze_size
        if ms == 6: _torch_animation.draw(screen, 300, 40); _torch_animation.draw(screen, 475, 40)
        elif ms == 8: _torch_animation.draw(screen, 320, 40); _torch_animation.draw(screen, 455, 40)
        elif ms == 10: _torch_animation.draw(screen, 295, 40); _torch_animation.draw(screen, 475, 40)
    if _maze_loader:
        m = pygame.mouse.get_pos() if _turn_state == TurnState.PLAYER_INPUT else None
        _maze_loader.draw(screen, _player, None, m)
    screen.blit(snake, (8, 80))
    if draw_mumlogo: screen.blit(mumlogo, (14, mumlogo_y if mumlogo_y else 14))
    if _world_map and _maze_loader: current_lvl = int(_maze_loader.level_id) if _maze_loader.level_id else 15; _world_map.draw(screen, current_lvl)
    if _maze_loader: _maze_loader.draw_ankh(screen)
    if _button_manager: _button_manager.draw_buttons(screen, hovered, clicked)
    if _show_options: _draw_options_menu(screen)
    return None

def get_hover_state(mouse_pos):
    if not _button_manager: return None
    for name, rect in _button_manager.button_rects.items():
        if rect.collidepoint(mouse_pos): return name
    return None

def get_clicked_state(): return _button_manager.clicked_button if _button_manager else None