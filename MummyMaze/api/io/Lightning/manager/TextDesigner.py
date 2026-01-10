import pygame

class TextDesigner:
    def __init__(self, font_name="arial", size=28, color=(255, 255, 255), hover_color=(255, 255, 0)):
        # Sử dụng font hệ thống đậm để dễ đọc và hỗ trợ nhiều ký tự
        self.base_font = pygame.font.SysFont(font_name, size, bold=True)
        # Font cho tiêu đề lớn hơn
        self.header_font = pygame.font.SysFont(font_name, int(size * 1.5), bold=True)
        self.color = color
        self.hover_color = hover_color

    def _create_text_surface(self, text, font, color, outline=True):
        """Tạo text có viền đen (Outline) để nổi bật trên nền game"""
        txt_surf = font.render(str(text), True, color)
        if not outline:
            return txt_surf
        
        # Tạo viền đen bằng cách vẽ text đen ở 8 hướng xung quanh
        outline_surf = font.render(str(text), True, (0, 0, 0))
        w = txt_surf.get_width() + 4
        h = txt_surf.get_height() + 4
        final_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        
        # Vẽ viền
        for dx in range(3):
            for dy in range(3):
                if dx == 1 and dy == 1: continue
                final_surf.blit(outline_surf, (dx, dy))
        
        # Vẽ chữ chính đè lên tâm
        final_surf.blit(txt_surf, (1, 1))
        return final_surf

    def render_header(self, text, surface, x, y):
        """Vẽ tiêu đề lớn màu vàng kim loại"""
        gold = (255, 215, 0)
        surf = self._create_text_surface(text, self.header_font, gold)
        rect = surf.get_rect(center=(x, y))
        surface.blit(surf, rect)

    def render_default(self, text, surface, x, y, color=None):
        """Vẽ nhãn thông thường"""
        c = color if color else self.color
        surf = self._create_text_surface(text, self.base_font, c)
        rect = surf.get_rect(center=(x, y))
        surface.blit(surf, rect)

    def render_label(self, text, surface, x, y, color=None):
        """Alias cho render_default"""
        self.render_default(text, surface, x, y, color)

    # Hàm render trả về surface (cho MapTracker/WinState dùng)
    def render(self, text, color=None, outline=True, hovered=False, outline_thickness=None):
        c = self.hover_color if hovered else (color if color else self.color)
        return self._create_text_surface(text, self.base_font, c, outline)

    def draw_button(self, surface, text, x, y, mouse_pos, clicked=False):
        """Vẽ nút bấm tương tác (đổi màu khi hover)"""
        # Tính toán rect dựa trên text mẫu
        temp_surf = self.base_font.render(str(text), True, self.color)
        rect = temp_surf.get_rect(center=(x, y))
        
        is_hovered = rect.collidepoint(mouse_pos)
        color = self.hover_color if is_hovered else self.color
        
        final_surf = self._create_text_surface(text, self.base_font, color)
        # Cập nhật lại rect do surface có viền lớn hơn
        draw_rect = final_surf.get_rect(center=(x, y))
        
        surface.blit(final_surf, draw_rect)
        
        if is_hovered:
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            return clicked
        return False