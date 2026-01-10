import os
import sys
import pygame
from pathlib import Path

# Configure system path to include project root
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path: sys.path.insert(0, str(ROOT_DIR))

# Import application modules
import api.io.Lightning.utils.ConfigFile as cf
from api.io.Lightning.gui.Interface import init, main_menu
from api.io.Lightning.gui.GameUI import initialize_ui, draw_screen, handle_game_input, restart_level, get_hover_state, get_clicked_state
from api.io.Lightning.gui.WinState import win_screen
from api.io.Lightning.gui.LoseState import lose_screen
from api.io.Lightning.gui.LoginScreen import login_screen
from api.io.Lightning.manager.SoundReader import music_manager
from api.io.Lightning.manager.StorageManager import storage_manager
from api.io.Lightning.manager.TextDesigner import TextDesigner
from api.io.Lightning.gui.Leaderboard import leaderboard_screen

# Define Application States
STATE_LOGIN = "LOGIN"; STATE_MENU = "MENU"; STATE_RANDOM_CFG = "RANDOM_CFG"
STATE_CAMPAIGN_SEL = "CAMPAIGN_SEL"; STATE_GAME = "GAME"; STATE_WIN = "WIN"; STATE_LOSE = "LOSE"
STATE_LEADERBOARD = "LEADERBOARD"

# Shared context
ctx = {"size": 8, "difficulty": "medium", "level_id": 1, "mode": "random"}

def random_config_screen(screen, clock, mouse_pos, clicked):
    bg = pygame.image.load(os.path.join(cf.UI_PATH, 'menuback.jpg'))
    screen.blit(bg, (0,0))
    gd = TextDesigner(color=(255, 215, 0)); wd = TextDesigner()
    
    gd.render_header("CLASSIC CONFIG", screen, 320, 50)
    
    gd.render_default("SIZE:", screen, 100, 140)
    sizes = [6, 8, 10]
    for i, s in enumerate(sizes):
        col = (255, 215, 0) if ctx["size"] == s else (200, 200, 200)
        td = TextDesigner(color=col)
        if td.draw_button(screen, f"{s}x{s}", 260 + i*120, 140, mouse_pos, clicked): ctx["size"] = s

    gd.render_default("MODE:", screen, 100, 240)
    diffs = ["easy", "medium", "hard"]
    for i, d in enumerate(diffs):
        col = (255, 215, 0) if ctx["difficulty"] == d else (200, 200, 200)
        td = TextDesigner(color=col)
        if td.draw_button(screen, d.upper(), 260 + i*120, 240, mouse_pos, clicked): ctx["difficulty"] = d

    if wd.draw_button(screen, "START GAME", 320, 380, mouse_pos, clicked):
        pygame.event.clear()
        screen.fill((0,0,0)); 
        txt = wd.render("GENERATING...", color=(255,255,0)); screen.blit(txt, (250, 220))
        pygame.display.flip()
        
        ctx["mode"] = "random"
        initialize_ui(mode="random", size=ctx["size"], difficulty=ctx["difficulty"])
        music_manager.start_classic_mode_music()
        return STATE_GAME
        
    if wd.draw_button(screen, "BACK", 320, 440, mouse_pos, clicked): return STATE_MENU
    
    return STATE_RANDOM_CFG

def campaign_select_screen(screen, clock, mouse_pos, clicked):
    bg = pygame.image.load(os.path.join(cf.UI_PATH, 'menuback.jpg'))
    screen.blit(bg, (0,0))
    gd = TextDesigner(color=(255, 215, 0)); wd = TextDesigner()
    
    gd.render_header("CAMPAIGN", screen, 320, 50)
    
    unlocked = [1]
    if storage_manager.current_user:
        unlocked = storage_manager.current_user.data.get("unlocked_levels", [1])
    
    start_x = 160
    for i in range(1, 4): 
        x = start_x + (i-1)*160; y = 200; lvl_str = f"LV {i}"
        
        if i in unlocked:
            col = (255, 215, 0) if ctx.get("level_id") == i else (255, 255, 255)
            td = TextDesigner(color=col)
            if td.draw_button(screen, lvl_str, x, y, mouse_pos, clicked): ctx["level_id"] = i
        else:
            grey = TextDesigner(color=(100, 100, 100))
            grey.render_default(lvl_str, screen, x, y)

    if wd.draw_button(screen, f"PLAY LEVEL {ctx.get('level_id', 1)}", 320, 380, mouse_pos, clicked):
        pygame.event.clear()
        ctx["mode"] = "campaign"
        initialize_ui(mode="campaign", level_id=ctx.get('level_id', 1))
        music_manager.start_classic_mode_music()
        return STATE_GAME
        
    if wd.draw_button(screen, "BACK", 320, 440, mouse_pos, clicked): return STATE_MENU
    
    return STATE_CAMPAIGN_SEL

def main():
    screen = init()
    clock = pygame.time.Clock()
    state = STATE_LOGIN
    running = True
    last_score, last_time = 0, 0
    
    while running:
        mouse_pos = pygame.mouse.get_pos()
        clicked = False
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1: clicked = True
            
            if state == STATE_GAME:
                music_manager.handle_event(e)
                res = handle_game_input(e, mouse_pos)
                if res == "quit": state = STATE_MENU

        # State Machine Logic
        if state == STATE_LOGIN:
            res = login_screen(screen, clock)
            if res == "__QUIT__": running = False
            elif res == "success": 
                state = STATE_MENU
                pygame.event.clear()

        elif state == STATE_MENU:
            music_manager.start_menu_music()
            act = main_menu(screen, clock)
            
            if act == "__QUIT__": running = False
            
            elif act == "continue_game":
                saved_data = storage_manager.load_game_state()
                if saved_data:
                    pygame.event.clear()
                    initialize_ui(saved_state=saved_data)
                    music_manager.start_classic_mode_music()
                    state = STATE_GAME
            
            elif act == "leaderboard":
                state = STATE_LEADERBOARD
                pygame.event.clear()

            elif act == "classic_mode": 
                state = STATE_RANDOM_CFG
                pygame.event.clear()
            elif act == "campaign_mode": 
                state = STATE_CAMPAIGN_SEL
                pygame.event.clear()
            
        elif state == STATE_RANDOM_CFG:
            state = random_config_screen(screen, clock, mouse_pos, clicked)
            pygame.display.flip()
            clock.tick(60)
            
        elif state == STATE_CAMPAIGN_SEL:
            state = campaign_select_screen(screen, clock, mouse_pos, clicked)
            pygame.display.flip()
            clock.tick(60)
            
        elif state == STATE_LEADERBOARD:
            res = leaderboard_screen(screen, clock, mouse_pos, clicked)
            if res == "BACK": state = STATE_MENU
            pygame.display.flip()
            clock.tick(60)

        elif state == STATE_GAME:
            if not running: break
            hover = get_hover_state(mouse_pos)
            clk = get_clicked_state()
            res = draw_screen(screen, hover, clk)
            
            if res == "lose": state = STATE_LOSE
            elif isinstance(res, tuple) and res[0] == "win":
                last_score, last_time = res[1], res[2]
                if ctx["mode"] == "campaign":
                    storage_manager.unlock_level(ctx["level_id"]+1)
                    storage_manager.update_high_score(ctx["level_id"], last_score)
                state = STATE_WIN
            
            pygame.display.flip()
            clock.tick(60)
            
        elif state == STATE_LOSE:
            act = lose_screen(screen, clock)
            if act == "quit": running = False
            elif act == "menu": state = STATE_MENU
            elif act == "retry": 
                restart_level() 
                state = STATE_GAME
            
        elif state == STATE_WIN:
            act = win_screen(screen, clock, score=last_score, time_ms=last_time)
            if act == "quit": running = False
            elif act == "menu": state = STATE_MENU
            elif act == "next_level":
                if ctx["mode"] == "campaign":
                    ctx["level_id"] += 1
                    if ctx["level_id"] > 3: 
                        state = STATE_MENU; ctx["level_id"] = 1
                    else:
                        initialize_ui(mode="campaign", level_id=ctx["level_id"])
                        state = STATE_GAME
                else:
                    initialize_ui(mode="random", size=ctx["size"], difficulty=ctx["difficulty"])
                    state = STATE_GAME
            elif act == "reset": restart_level(); state = STATE_GAME

    pygame.quit()

if __name__ == "__main__":
    main()