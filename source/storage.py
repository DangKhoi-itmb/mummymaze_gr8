from .models import Profile


def get_guest_profile() -> Profile:
    """
    tạo một profile guest tạm để chơi nhanh.

    sau này sẽ thay bằng logic đăng nhập, đọc từ profiles.json.
    """
    return Profile(username="guest", display_name="Guest")
