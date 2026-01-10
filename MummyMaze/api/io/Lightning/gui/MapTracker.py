import pygame, os
from api.io.Lightning.manager.TextDesigner import TextDesigner
from api.io.Lightning.utils.ConfigFile import UI_PATH

class WorldMapPanel:
    def __init__(self, x=8, y=320):
        # 1. Load Assets
        self.bg_map = pygame.image.load(os.path.join(UI_PATH, 'map.png')).convert_alpha()
        self.label_pyramid = pygame.image.load(os.path.join(UI_PATH, 'pyramidtext.gif')).convert_alpha()
        self.icon_head = pygame.image.load(os.path.join(UI_PATH, 'maphead.png')).convert_alpha()
        self.icon_x = pygame.image.load(os.path.join(UI_PATH, 'mapx.png')).convert_alpha()
        
        # FIX: Dùng TextDesigner thay vì PyramidFont cũ
        self.number_font = TextDesigner(size=18, color=(255, 215, 0)) # Chữ vàng

        self.rect = self.bg_map.get_rect()
        self.rect.topleft = (x, y)

        # 2. Define Pyramid Node Positions
        col_w = 20
        row_h = 15
        bottom_y = 93
        manual_x_offset = -2
        center_x = (self.rect.width // 2) + manual_x_offset
        self.nodes = []

        # Row 1 (Bottom)
        y = bottom_y
        self.nodes.extend([(center_x - col_w*2, y), (center_x - col_w, y), (center_x, y), (center_x + col_w, y), (center_x + col_w*2, y)])
        # Row 2
        y -= row_h
        self.nodes.extend([(center_x - col_w*1.5, y), (center_x - col_w*0.5, y), (center_x + col_w*0.5, y), (center_x + col_w*1.5, y)])
        # Row 3
        y -= row_h
        self.nodes.extend([(center_x - col_w, y), (center_x, y), (center_x + col_w, y)])
        # Row 4
        y -= row_h
        self.nodes.extend([(center_x - col_w*0.5, y), (center_x + col_w*0.5, y)])
        # Row 5 (Top)
        y -= row_h
        self.nodes.append((center_x, y))

    def draw(self, screen, current_level_idx):
        screen.blit(self.bg_map, self.rect.topleft)
        screen.blit(self.label_pyramid, (self.rect.x + 10, self.rect.y + 10))

        # FIX: Render số 1 bằng hàm mới
        pyramid_num_surf = self.number_font.render("1", outline=True)
        screen.blit(pyramid_num_surf, (self.rect.x + 28, self.rect.y + 25))

        for i, (node_x, node_y) in enumerate(self.nodes):
            level_num = i + 1
            draw_pos_x = self.rect.x + node_x
            draw_pos_y = self.rect.y + node_y

            if level_num < current_level_idx:
                dest = (draw_pos_x - self.icon_x.get_width() // 2, draw_pos_y - self.icon_x.get_height() // 2)
                screen.blit(self.icon_x, dest)
            elif level_num == current_level_idx:
                dest = (draw_pos_x - self.icon_head.get_width() // 2, draw_pos_y - self.icon_head.get_height() // 2 - 2)
                screen.blit(self.icon_head, dest)