from .ui_pygame import run_game_loop


def main() -> int:
    """
    hàm main của project.

    chỉ đơn giản gọi vòng lặp game pygame.
    sau này nếu có thêm mode console / test khác thì có thể điều hướng từ đây.
    """
    run_game_loop()
    return 0


if __name__ == "__main__":
    # cho phép chạy trực tiếp file main.py
    raise SystemExit(main())
