import pygame
import os
from api.io.Lightning.manager.TextDesigner import TextDesigner
from api.io.Lightning.manager.StorageManager import storage_manager
from api.io.Lightning.utils.ConfigFile import UI_PATH

# Biến lưu trạng thái nội bộ của màn hình Leaderboard (đang xem Level mấy)
_current_view_level = 1

def leaderboard_screen(screen, clock, mouse_pos, clicked):
    global _current_view_level
    
    # 1. Vẽ hình nền
    bg_path = os.path.join(UI_PATH, 'menuback.jpg')
    if os.path.exists(bg_path):
        bg = pygame.image.load(bg_path)
        screen.blit(bg, (0,0))
    else:
        screen.fill((20, 20, 20))
    
    gd = TextDesigner(color=(255, 215, 0)) # Màu vàng kim
    wd = TextDesigner() # Màu trắng mặc định
    
    # 2. Tiêu đề
    gd.render_header("LEADERBOARD", screen, 320, 50)
    
    # 3. Các nút chọn Level (Tab)
    # Vẽ 3 nút LV 1, LV 2, LV 3
    start_x = 160
    for i in range(1, 4):
        x = start_x + (i-1) * 160
        y = 120
        label = f"LV {i}"
        
        # Highlight nút đang chọn
        if _current_view_level == i:
            color = (255, 215, 0)
        else:
            color = (150, 150, 150)
            
        td = TextDesigner(color=color, size=28)
        
        if td.draw_button(screen, label, x, y, mouse_pos, clicked):
            _current_view_level = i

    # 4. Vẽ bảng danh sách điểm (Lấy từ StorageManager)
    data = storage_manager.get_leaderboard_data(_current_view_level)
    
    list_start_y = 180
    
    # Vẽ Header cột
    header_font = TextDesigner(size=24, color=(255, 100, 100))
    # Vẽ tiêu đề cột thủ công để căn chỉnh
    header_font.render_default("RANK", screen, 180, list_start_y)
    header_font.render_default("NAME", screen, 320, list_start_y)
    header_font.render_default("SCORE", screen, 460, list_start_y)
    
    if not data:
        wd.render_default("NO RECORDS YET", screen, 320, 250, color=(200,200,200))
    else:
        # Vẽ từng dòng
        row_font = TextDesigner(size=24)
        for idx, entry in enumerate(data):
            y = list_start_y + 40 + (idx * 35)
            
            rank_str = f"{idx+1}."
            name_str = entry['name'][:10] # Cắt tên nếu quá dài
            score_str = str(entry['score'])
            
            # Tô màu cho Top 3
            row_color = (255, 255, 255)
            if idx == 0: row_color = (255, 215, 0) # Vàng
            elif idx == 1: row_color = (192, 192, 192) # Bạc
            elif idx == 2: row_color = (205, 127, 50) # Đồng
            
            rf = TextDesigner(size=24, color=row_color)
            
            # Vẽ từng cột
            rf.render_default(rank_str, screen, 180, y)
            rf.render_default(name_str, screen, 320, y)
            rf.render_default(score_str, screen, 460, y)

    # 5. Nút Back
    if wd.draw_button(screen, "BACK", 320, 440, mouse_pos, clicked):
        return "BACK"
        
    return "STAY"