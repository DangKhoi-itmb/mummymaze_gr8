import pygame
import os
from api.io.Lightning.manager.TextDesigner import TextDesigner
from api.io.Lightning.manager.StorageManager import storage_manager
from api.io.Lightning.utils.ConfigFile import UI_PATH, fps

class InputBox:
    def __init__(self, x, y, w, h, font, text='', is_password=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = (100, 100, 100)
        self.color_active = (255, 215, 0)
        self.color = self.color_inactive
        self.text = text
        self.font = font
        self.is_password = is_password
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = self.color_active if self.active else self.color_inactive
            
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return "submit"
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                # CHỈ NHẬN KÝ TỰ CHỮ VÀ SỐ (A-Z, 0-9)
                if len(self.text) < 15 and event.unicode.isalnum():
                    self.text += event.unicode
        return None

    def draw(self, screen):
        disp = "*" * len(self.text) if self.is_password else self.text
        pygame.draw.rect(screen, (30, 30, 40), self.rect)
        pygame.draw.rect(screen, self.color, self.rect, 2)
        surf = self.font.render(disp, True, (255, 255, 255))
        screen.blit(surf, (self.rect.x+5, self.rect.y+5))

def login_screen(screen, clock):
    # Load background
    bg_path = os.path.join(UI_PATH, 'menuback.jpg')
    if os.path.exists(bg_path):
        bg = pygame.image.load(bg_path)
    else:
        bg = pygame.Surface((640, 480)); bg.fill((20, 20, 20))
    
    logo_path = os.path.join(UI_PATH, 'menulogo.png')
    logo = pygame.image.load(logo_path) if os.path.exists(logo_path) else None

    # Font riêng cho Input Box (Arial)
    input_font = pygame.font.SysFont("arial", 24)
    
    # Designer cho UI Text (Style Game)
    designer = TextDesigner(size=28)
    err_designer = TextDesigner(size=24, color=(255, 50, 50))
    
    user_box = InputBox(220, 200, 200, 35, input_font)
    pass_box = InputBox(220, 260, 200, 35, input_font, is_password=True)
    
    msg = ""
    
    while True:
        mouse_pos = pygame.mouse.get_pos()
        events = pygame.event.get()
        submit_action = None

        for event in events:
            if event.type == pygame.QUIT: return "__QUIT__"
            
            if user_box.handle_event(event) == "submit" or pass_box.handle_event(event) == "submit":
                submit_action = "login"

        screen.blit(bg, (0,0))
        if logo: screen.blit(logo, (92, 20))
        
        # Labels
        designer.render_default("USER:", screen, 160, 217)
        designer.render_default("PASS:", screen, 160, 277)
        
        user_box.draw(screen)
        pass_box.draw(screen)
        
        clicked = pygame.mouse.get_pressed()[0]
        
        if designer.draw_button(screen, "LOGIN", 250, 340, mouse_pos, clicked):
            submit_action = "login"
            
        if designer.draw_button(screen, "REGISTER", 390, 340, mouse_pos, clicked):
            submit_action = "register"

        if submit_action:
            u, p = user_box.text, pass_box.text
            if not u or not p:
                msg = "MISSING INFO"
            else:
                if submit_action == "login":
                    res = storage_manager.login(u, p)
                    if res == "success": return "success"
                    msg = res
                else:
                    res = storage_manager.register(u, p, u)
                    if res == "success": return "success"
                    msg = res
            pygame.time.wait(250)

        if msg:
            err_designer.render_default(msg.upper(), screen, 320, 400)

        pygame.display.flip()
        clock.tick(fps)