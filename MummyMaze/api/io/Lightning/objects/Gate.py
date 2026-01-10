import os
import pygame

from api.io.Lightning.utils.ConfigFile import OBJECTS_PATH, maze_coord_x, maze_coord_y

class Gate:
    STATE_OPEN = 'open'
    STATE_CLOSED = 'closed'

    STATE_OPENING = 'opening'
    STATE_CLOSING = 'closing'

    def __init__(self, x, y, cell_size, maze_size):
        self.grid_x = x
        self.grid_y = y
        self.cell_size = cell_size
        self.maze_size = maze_size

        self.frames = []
        self.current_frame = 0
        self.state = self.STATE_CLOSED
        self.animation_speed = 0.2
        self.animation_counter = 0

        self._load_frames()

    def _load_frames(self):
        try:
            gate_strip = pygame.image.load(os.path.join(OBJECTS_PATH, f'gate{self.maze_size}.gif')).convert_alpha()

            sheet_width = gate_strip.get_width() // 8
            sheet_height = gate_strip.get_height()

            for i in range(8):
                frame = pygame.Surface((sheet_width, sheet_height), pygame.SRCALPHA)
                frame.blit(gate_strip, (0, 0), (i * sheet_width, 0, sheet_width, sheet_height))
                self.frames.append(frame)

            print(f"[System] Loaded {len(self.frames)} gate animation frames")

        except Exception as e:
            print(f"[Error] Error loading gate frames: {e}")
            for i in range(8):
                dummy = pygame.Surface((self.cell_size, 10), pygame.SRCALPHA)
                alpha = 255 - (i * 32)
                dummy.fill((100, 100, 100))
                dummy.set_alpha(alpha)
                self.frames.append(dummy)

    def update(self):
        if self.state == self.STATE_CLOSED or self.state == self.STATE_OPEN:
            return

        self.animation_counter += self.animation_speed

        if self.animation_counter >= 1.0:
            self.animation_counter = 0

            if self.state == self.STATE_OPENING:
                self.current_frame += 1
                if self.current_frame >= len(self.frames) - 1:
                    self.current_frame = len(self.frames) - 1
                    self.state = self.STATE_OPEN

            elif self.state == self.STATE_CLOSING:
                self.current_frame -= 1
                if self.current_frame <= 0:
                    self.current_frame = 0
                    self.state = self.STATE_CLOSED

    def draw(self, surface):
        if not self.frames:
            return

        frame = self.frames[self.current_frame]

        base_x = maze_coord_x + self.grid_x * self.cell_size
        base_y = maze_coord_y + self.grid_y * self.cell_size

        offset_x = int(self.cell_size * 0.08)
        offset_y = int(self.cell_size * 0.27)

        gate_x = base_x - offset_x
        gate_y = base_y - offset_y

        surface.blit(frame, (gate_x, gate_y))

    def toggle(self):
        if self.state == self.STATE_CLOSED:
            self.state = self.STATE_OPENING
        elif self.state == self.STATE_OPEN:
            self.state = self.STATE_CLOSING

    def open(self):
        if self.state == self.STATE_CLOSED:
            self.state = self.STATE_OPENING

    def close(self):
        if self.state == self.STATE_OPEN:
            self.state = self.STATE_CLOSING

    def is_blocking(self):
        return self.state == self.STATE_CLOSED or self.state == self.STATE_CLOSING

    def is_open(self):
        return self.state == self.STATE_OPEN