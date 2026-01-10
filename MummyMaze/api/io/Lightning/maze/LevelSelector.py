import random

class LevelSystem:
    def __init__(self):
        self.max_levels = 15
        self.current_level_num = 1
        self.level_difficulties = {}
        self.generate_pyramid_structure()

    def generate_pyramid_structure(self):
        """Tính toán độ khó cho 15 tầng tháp"""
        self.level_difficulties.clear()
        options = ['easy', 'medium', 'hard']
        weights = [0.3, 0.5, 0.2]

        for level in range(1, self.max_levels + 1):
            if level <= 3:
                self.level_difficulties[level] = 'normal'
            elif level == 15:
                self.level_difficulties[level] = 'hard'
            else:
                diff = random.choices(options, weights=weights, k=1)[0]
                self.level_difficulties[level] = diff

    def get_current_difficulty(self):
        return self.level_difficulties.get(self.current_level_num, 'medium')

    def next_level(self):
        if self.current_level_num < self.max_levels:
            self.current_level_num += 1
            return True
        return False

    def get_current_level(self):
        return self.current_level_num

    def reset_progress(self):
        self.current_level_num = 1
        self.generate_pyramid_structure()