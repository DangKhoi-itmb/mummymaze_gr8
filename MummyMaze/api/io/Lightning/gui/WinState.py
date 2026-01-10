import pygame
import os
from api.io.Lightning.manager.TextDesigner import TextDesigner
from api.io.Lightning.utils.ConfigFile import UI_PATH, fps
from api.io.Lightning.gui import GameUI

def format_time_text(ms):
    total_sec = int(ms / 1000)
    mins = total_sec // 60
    secs = total_sec % 60
    return f"{mins}m {secs}s"

def win_screen(screen, clock, score=0, time_ms=0):
    background = pygame.image.load(os.path.join(UI_PATH, 'nextlevel.jpg')).convert()
    bg_x, bg_y = 152, 5
    bg_width = background.get_width()
    bg_center_x = bg_x + (bg_width // 2)

    designer = TextDesigner()
    gold_designer = TextDesigner(color=(255, 215, 0))

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        clicked = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: clicked = True
            
            action = GameUI.handle_game_input(event, mouse_pos)
            if action: return action

        hovered = GameUI.get_hover_state(mouse_pos)
        
        # Vẽ nền game
        GameUI.draw_screen(screen, hovered, None)
        # Vẽ overlay thắng
        screen.blit(background, (bg_x, bg_y))

        # Text
        gold_designer.render_header("LEVEL CLEARED!", screen, bg_center_x, bg_y + 50)
        designer.render_label(f"SCORE: {score}", screen, bg_center_x, bg_y + 120)
        designer.render_label(f"TIME: {format_time_text(time_ms)}", screen, bg_center_x, bg_y + 160)

        # Button
        if designer.draw_button(screen, "NEXT LEVEL", bg_center_x, bg_y + 320, mouse_pos, clicked):
            return "next_level"

        pygame.display.flip()
        clock.tick(fps)
    return "quit"