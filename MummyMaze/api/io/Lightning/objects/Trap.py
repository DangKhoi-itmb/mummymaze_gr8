import os
import pygame

from api.io.Lightning.manager.Spritesheet import Spritesheet
from api.io.Lightning.utils.ConfigFile import OBJECTS_PATH, maze_coord_x, maze_coord_y

class Trap:
    def __init__(self, x, y, cell_size, maze_size):
        self.grid_x = x
        self.grid_y = y
        self.cell_size = cell_size
        self.maze_size = maze_size

        self.is_triggered = False
        self.frames = []
        self.animation_frame = 0
        self.animation_speed = 0.15
        self.animation_timer = 0

        self._load_sprites()

    def _load_sprites(self):
        self.trap_base = pygame.image.load(
            os.path.join(OBJECTS_PATH, f'trap{self.maze_size}.png')
        )

        sparkle_sheet = Spritesheet(
            os.path.join(OBJECTS_PATH, f'trapsparkle{self.maze_size}.png')
        )

        sheet_width = sparkle_sheet.sheet.get_width() // 14
        sheet_height = sparkle_sheet.sheet.get_height()

        for i in range(14):
            frame = sparkle_sheet.get_image(
                i * sheet_width, 0, sheet_width, sheet_height
            )
            self.frames.append(frame)

    def update(self):
        if not self.is_triggered:
            self.animation_timer += self.animation_speed
            if self.animation_timer >= 1:
                self.animation_timer = 0
                self.animation_frame = (self.animation_frame + 1) % len(self.frames)

    def trigger(self):
        self.is_triggered = True
        print(f"[Game] Trap triggered at ({self.grid_x}, {self.grid_y})")

    def check_collision(self, entity_x, entity_y):
        return entity_x == self.grid_x and entity_y == self.grid_y

    def draw(self, surface):
        pixel_x = maze_coord_x + self.grid_x * self.cell_size
        pixel_y = maze_coord_y + self.grid_y * self.cell_size

        trap_x = pixel_x + (self.cell_size - self.trap_base.get_width()) // 2
        trap_y = pixel_y + (self.cell_size - self.trap_base.get_height()) // 2
        surface.blit(self.trap_base, (trap_x, trap_y))

        if not self.is_triggered and len(self.frames) > 0:
            sparkle = self.frames[self.animation_frame]
            s_w = sparkle.get_width()
            s_h = sparkle.get_height()

            center_x = pixel_x + self.cell_size // 2
            center_y = pixel_y + self.cell_size // 2

            eye_offset_x = int(self.cell_size * 0.13)
            eye_offset_y = int(self.cell_size * 0.04)

            left_x = center_x - eye_offset_x - (s_w // 2)
            left_y = center_y - eye_offset_y - (s_h // 2)

            right_x = center_x + eye_offset_x - (s_w // 2)
            right_y = center_y - eye_offset_y - (s_h // 2)

            surface.blit(sparkle, (left_x, left_y))
            surface.blit(sparkle, (right_x, right_y))
    
    def draw_active_block(self, surface):
        pass # Optional: Draw visual effect when triggered