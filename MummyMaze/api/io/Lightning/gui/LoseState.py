import pygame
import os
from api.io.Lightning.manager.TextDesigner import TextDesigner
from api.io.Lightning.utils.ConfigFile import UI_PATH, fps
from api.io.Lightning.manager.SoundReader import sfx_manager

def lose_screen(screen, clock):
    sfx_manager.play('mummyhowl')
    
    menuback = pygame.image.load(os.path.join(UI_PATH, 'menuback.jpg'))
    menufront = pygame.image.load(os.path.join(UI_PATH, 'menufront.png'))
    
    designer = TextDesigner(color=(200, 200, 200), hover_color=(255, 50, 50))
    
    # Animation
    menu_y = 480
    target_y = 0
    progress = 0.0
    
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        clicked = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "quit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: clicked = True

        # Update Anim
        if progress < 1.0:
            progress += 0.02
            menu_y = 480 * (1 - progress) * (1 - progress) # Ease out
        else:
            menu_y = 0

        screen.blit(menuback, (0, 0))
        screen.blit(menufront, (0, menu_y))
        
        # Chỉ vẽ nút khi bảng hiện lên gần hết
        if progress > 0.8:
            offset_y = menu_y
            
            if designer.draw_button(screen, "TRY AGAIN", 320, 360 + offset_y, mouse_pos, clicked):
                return "retry"
            
            if designer.draw_button(screen, "MAIN MENU", 320, 400 + offset_y, mouse_pos, clicked):
                return "menu"
            
            if designer.draw_button(screen, "QUIT GAME", 320, 440 + offset_y, mouse_pos, clicked):
                return "quit"

        pygame.display.flip()
        clock.tick(fps)
    return "quit"