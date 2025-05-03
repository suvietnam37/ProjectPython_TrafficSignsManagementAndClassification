# data/cleaned/clean_data.py
import os
import cv2
import numpy as np
import shutil
from tqdm import tqdm # Thư viện tạo thanh tiến trình (pip install tqdm)
import config

# --- Cấu hình ---
SOURCE_TRAIN_DIR = config.TRAIN_DATA_DIR # data/raw/GTSRB/Train
CLEANED_TRAIN_DIR = os.path.join(config.DATA_DIR, 'cleaned', 'GTSRB', 'Train')
BLUR_THRESHOLD = 100.0 # Ngưỡng phương sai Laplacian, cần thử nghiệm!
REMOVE_BLURRY = True # Đặt thành False nếu chỉ muốn báo cáo mà không xóa/bỏ qua
MIN_SIZE = (10, 10) # Kích thước tối thiểu (pixel) mà ảnh phải có

def variance_of_laplacian(image):
    """Tính phương sai của toán tử Laplace để đo độ mờ."""
    if image is None:
        return 0
    # Chuyển sang ảnh xám nếu là ảnh màu
    if len(image.shape) == 3:
         gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
         gray = image
    # Tính toán Laplacian và trả về phương sai
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def clean_dataset(source_dir, target_dir, blur_threshold, remove_blurry, min_size):
    """Quét qua dataset, phát hiện ảnh mờ/nhỏ và sao chép ảnh sạch."""
    print(f"Starting data cleaning process...")
    print(f"Source Directory: {source_dir}")
    print(f"Target Directory: {target_dir}")
    print(f"Blurry Threshold (Laplacian Variance): {blur_threshold}")
    print(f"Remove Blurry Images: {remove_blurry}")
    print(f"Minimum Image Size: {min_size}")

    if os.path.exists(target_dir):
        print(f"Warning: Target directory {target_dir} already exists. It might contain old data.")
        # Quyết định: Xóa thư mục cũ hay không? (Ở đây không xóa)
        # shutil.rmtree(target_dir)
    os.makedirs(target_dir, exist_ok=True)

    total_images = 0
    kept_images = 0
    blurry_count = 0
    small_count = 0
    error_count = 0

    # Duyệt qua từng lớp (thư mục 0-42)
    for class_id in tqdm(os.listdir(source_dir), desc="Processing Classes"):
        source_class_path = os.path.join(source_dir, class_id)
        target_class_path = os.path.join(target_dir, class_id)

        if not os.path.isdir(source_class_path):
            continue

        os.makedirs(target_class_path, exist_ok=True)

        # Duyệt qua từng ảnh trong lớp
        for img_name in os.listdir(source_class_path):
            source_img_path = os.path.join(source_class_path, img_name)
            target_img_path = os.path.join(target_class_path, img_name)
            total_images += 1

            try:
                img = cv2.imread(source_img_path)
                if img is None:
                    # print(f"Warning: Could not read image {source_img_path}")
                    error_count += 1
                    continue

                # Kiểm tra kích thước ảnh
                h, w = img.shape[:2]
                if h < min_size[1] or w < min_size[0]:
                     # print(f"Info: Image too small {source_img_path} ({w}x{h})")
                     small_count += 1
                     continue # Bỏ qua ảnh quá nhỏ

                # Kiểm tra độ mờ
                fm = variance_of_laplacian(img)
                is_blurry = fm < blur_threshold

                if is_blurry:
                     blurry_count += 1
                    #  print(f"Info: Image potentially blurry {source_img_path} (Variance: {fm:.2f})")

                # Quyết định giữ lại ảnh
                keep_image = True
                if is_blurry and remove_blurry:
                    keep_image = False

                if keep_image:
                    shutil.copy2(source_img_path, target_img_path) # copy2 giữ lại metadata
                    kept_images += 1

            except Exception as e:
                print(f"Error processing image {source_img_path}: {e}")
                error_count += 1

    print("\n--- Cleaning Summary ---")
    print(f"Total images scanned: {total_images}")
    print(f"Images kept (copied to target): {kept_images}")
    print(f"Images potentially blurry: {blurry_count}" + (" (skipped)" if remove_blurry else " (kept)"))
    print(f"Images too small (skipped): {small_count}")
    print(f"Images with read/processing errors (skipped): {error_count}")
    print(f"Cleaned data saved in: {target_dir}")

if __name__ == "__main__":
    # Cài đặt tqdm nếu chưa có: pip install tqdm
    clean_dataset(SOURCE_TRAIN_DIR, CLEANED_TRAIN_DIR, BLUR_THRESHOLD, REMOVE_BLURRY, MIN_SIZE)
