import os

def pack_project(root_dir, output_file):
    # Danh sách các thư mục và đuôi file cần loại bỏ để giảm dung lượng 
    ignored_dirs = {'.venv', '__pycache__', '.idea', '.git', 'resources', 'dist/levels'}
    allowed_extensions = {'.py', '.toml', '.md', '.json'}

    with open(output_file, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk(root_dir):
            # Loại bỏ các thư mục không cần thiết khỏi danh sách duyệt
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in allowed_extensions):
                    file_path = os.path.join(root, file)
                    
                    # Ghi tiêu đề file để mình dễ nhận diện cấu trúc 
                    outfile.write(f"\n\n{'='*30}\n")
                    outfile.write(f"PATH: {file_path}\n")
                    outfile.write(f"{'='*30}\n\n")
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                            outfile.write(infile.read())
                    except Exception as e:
                        outfile.write(f"Error reading file: {e}\n")

if __name__ == "__main__":
    # Chạy lệnh đóng gói thư mục MummyMaze
    pack_project('MummyMaze', 'full_source_code.txt')
    print("Đã đóng gói xong! Bạn hãy gửi file 'full_source_code.txt' cho mình nhé.")