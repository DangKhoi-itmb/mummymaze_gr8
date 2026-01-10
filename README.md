# Mummy Maze 
## Yêu cầu hệ thống
- Python 3.10 trở lên
- Thư viện: pygame-ce
## Cài đặt và Chạy game
1. Cài đặt thư viện cần thiết:
   ```bash
   pip install pygame-ce>=2.5.6

2. Chạy game từ thư mục gốc của dự án:
   ```bash
   python -m MummyMaze.dist.main

Hướng dẫn sử dụng
1. Màn hình đăng nhập
Register (Đăng ký): Nhập tên đăng nhập và mật khẩu, sau đó nhấn nút Register để tạo tài khoản mới.

Login (Đăng nhập): Nhập thông tin tài khoản đã đăng ký để vào game. Dữ liệu điểm số và file lưu sẽ gắn liền với tài khoản này.

Guest (Chơi thử): Chọn chế độ này để chơi ngay mà không cần tài khoản (không lưu được điểm lên bảng xếp hạng).

2. Menu chính
Enter: Chơi mới (New Game) - Bắt đầu từ Level 1.

Phím L: Tiếp tục (Load Game) - Tải lại màn chơi từ lần lưu gần nhất.

Phím Q: Thoát game.

3. Điều khiển trong game
Di chuyển: Sử dụng các phím mũi tên (Lên, Xuống, Trái, Phải) hoặc cụm phím W, A, S, D.

Lưu game (Save): Nhấn phím S. Trạng thái nhân vật và màn chơi hiện tại sẽ được lưu lại.

Quay về Menu: Nhấn phím ESC.

Cấu trúc thư mục
MummyMaze/dist/: Chứa mã nguồn chính và dữ liệu màn chơi.

MummyMaze/api/: Các module xử lý logic game.

MummyMaze/resources/: Tài nguyên hình ảnh và âm thanh.

MummyMaze/data/: Nơi lưu trữ dữ liệu người dùng (profiles.json).
