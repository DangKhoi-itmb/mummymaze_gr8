import pygame
import os
from api.io.Lightning.utils.ConfigFile import UI_PATH
from api.io.Lightning.manager.Spritesheet import Spritesheet

class ButtonManager:
    def __init__(self):
        # Load sprite nút bấm
        buttonstrip_path = os.path.join(UI_PATH, 'buttonstrip.jpg')
        if not os.path.exists(buttonstrip_path):
            print(f"Warning: Missing buttonstrip at {buttonstrip_path}")
            self.buttons = {}
            self.button_rects = {}
            return

        spritesheet = Spritesheet(buttonstrip_path)
        button_width = 135
        button_height = 42

        # Cắt ảnh từ spritesheet
        self.buttons = {
            'undo_move_hover': spritesheet.get_image(0, 0 * button_height, button_width, button_height),
            'undo_move_clicked': spritesheet.get_image(0, 1 * button_height, button_width, button_height),
            'reset_maze_hover': spritesheet.get_image(0, 2 * button_height, button_width, button_height),
            'reset_maze_clicked':  spritesheet.get_image(0, 3 * button_height, button_width, button_height),
            'options_hover': spritesheet.get_image(0, 4 * button_height, button_width, button_height),
            'options_clicked': spritesheet.get_image(0, 5 * button_height, button_width, button_height),
            'world_map_disabled': spritesheet.get_image(0, 8 * button_height, button_width, button_height),
            'quit_to_main_hover': spritesheet.get_image(0, 9 * button_height, button_width, button_height),
            'quit_to_main_clicked': spritesheet.get_image(0, 10 * button_height, button_width, button_height),
        }

        # Định nghĩa vùng bấm (Hitbox)
        self.button_rects = {
            'undo': pygame.Rect(8, 130, button_width, button_height),
            'reset': pygame.Rect(8, 172, button_width, button_height),
            'option': pygame.Rect(8, 225, button_width, button_height),
            'quit': pygame.Rect(8, 430, button_width, button_height),
        }
        self.clicked_button = None

    def set_clicked(self, button_name):
        self.clicked_button = button_name

    def clear_clicked(self):
        self.clicked_button = None

    def draw_buttons(self, screen, hovered=None, clicked=None):
        if not self.buttons: return

        # Helper vẽ nút
        def draw(name, rect_key, y):
            if clicked == rect_key:
                screen.blit(self.buttons[f'{name}_clicked'], (8, y))
            elif hovered == rect_key:
                screen.blit(self.buttons[f'{name}_hover'], (8, y))

        draw('undo_move', 'undo', 130)
        draw('reset_maze', 'reset', 172)
        draw('options', 'option', 225)
        
        # World map luôn hiển thị disabled (do chưa làm map)
        screen.blit(self.buttons['world_map_disabled'], (8, 267))
        
        draw('quit_to_main', 'quit', 430)