import pygame
import os
from api.io.Lightning.gui import GameUI
from api.io.Lightning.manager.TextDesigner import TextDesigner
from api.io.Lightning.utils.ConfigFile import UI_PATH, SOUNDS_PATH, fps
from api.io.Lightning.manager.SoundReader import music_manager
from api.io.Lightning.manager.StorageManager import storage_manager

def init():
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    pygame.display.set_caption("Mummy Maze Ultimate 1.0")
    GameUI.initialize_ui()
    return screen

def main_menu(screen, clock):
    bg_path = os.path.join(UI_PATH, 'menuback.jpg')
    bg = pygame.image.load(bg_path) if os.path.exists(bg_path) else pygame.Surface((640, 480))

    logo_path = os.path.join(UI_PATH, 'menulogo.png')
    logo = pygame.image.load(logo_path) if os.path.exists(logo_path) else None

    try: pygame.mixer.Sound(os.path.join(SOUNDS_PATH, 'tombslide.wav')).play()
    except: pass

    designer = TextDesigner(size=36)
    anim_progress = 0.0
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        clicked = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "__QUIT__"
            music_manager.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: clicked = True

        screen.blit(bg, (0, 0))
        if anim_progress < 1.0: anim_progress += 0.03
        
        if logo:
            logo_y = -100 + (130 * anim_progress) if anim_progress < 1.0 else 30
            screen.blit(logo, (92, int(logo_y)))
        
        # Render Menu
        if anim_progress > 0.8:
            cx = 320; start_y = 200; gap = 55
            
            # 1. CONTINUE
            if storage_manager.has_saved_game():
                if designer.draw_button(screen, "CONTINUE", cx, start_y, mouse_pos, clicked):
                    return "continue_game"
                start_y += gap

            # 2. PLAY RANDOM
            if designer.draw_button(screen, "PLAY RANDOM", cx, start_y, mouse_pos, clicked):
                return "classic_mode"
            
            # 3. CAMPAIGN
            if designer.draw_button(screen, "CAMPAIGN", cx, start_y + gap, mouse_pos, clicked):
                return "campaign_mode"
            
            # 4. LEADERBOARD
            if designer.draw_button(screen, "LEADERBOARD", cx, start_y + gap*2, mouse_pos, clicked):
                return "leaderboard"
            
            # 5. QUIT
            if designer.draw_button(screen, "QUIT", cx, start_y + gap*3, mouse_pos, clicked):
                return "__QUIT__"

        pygame.display.flip()
        clock.tick(fps)
    return "__QUIT__"