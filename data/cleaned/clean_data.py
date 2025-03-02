import os
from PIL import Image

# Đường dẫn đến thư mục chứa ảnh thô
raw_dir = '../raw/'  # Thay đổi đường dẫn để trỏ đến thư mục raw
cleaned_dir = '.'  # Thư mục hiện tại (cleaned) nơi lưu tệp mã nguồn

# Định nghĩa các thông số hợp lệ cho ảnh
valid_formats = ['JPEG', 'JPG', 'PNG']  # Các định dạng hợp lệ
min_size = (100, 100)  # Kích thước tối thiểu (width, height)

# Hàm kiểm tra tính hợp lệ của ảnh
def is_valid_image(image):
    # Kiểm tra định dạng
    if image.format not in valid_formats:
        return False
    # Kiểm tra kích thước
    if image.size[0] < min_size[0] or image.size[1] < min_size[1]:
        return False
    return True

# Đọc và xử lý từng ảnh trong thư mục raw
for filename in os.listdir(raw_dir):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):  # Kiểm tra định dạng file
        file_path = os.path.join(raw_dir, filename)
        try:
            with Image.open(file_path) as img:
                if is_valid_image(img):
                    # Lưu ảnh hợp lệ vào thư mục cleaned
                    img.save(os.path.join(cleaned_dir, filename))
                    print(f"Đã lưu ảnh hợp lệ: {filename}")
                else:
                    print(f"Ảnh không hợp lệ: {filename}")
        except Exception as e:
            print(f"Không thể mở ảnh {filename}: {e}")

print("Hoàn thành quá trình làm sạch dữ liệu.")