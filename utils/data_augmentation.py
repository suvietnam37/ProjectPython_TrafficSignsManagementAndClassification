# utils/data_augmentation.py

import cv2
import numpy as np
import random
from typing import Tuple, Optional, List, Union

# --- Các hàm Augmentation riêng lẻ ---

def random_rotation(image: np.ndarray, rotation_range: float) -> np.ndarray:
    """Áp dụng xoay ngẫu nhiên cho ảnh."""
    if rotation_range <= 0:
        return image
    rows, cols = image.shape[:2]
    angle = np.random.uniform(-rotation_range, rotation_range)
    M = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle, 1)
    # Dùng BORDER_REPLICATE để lặp lại pixel biên, tránh viền đen
    rotated_image = cv2.warpAffine(image, M, (cols, rows), borderMode=cv2.BORDER_REPLICATE)
    return rotated_image

def random_shift(image: np.ndarray, width_shift_range: float, height_shift_range: float) -> np.ndarray:
    """Áp dụng dịch chuyển ngang và dọc ngẫu nhiên."""
    if width_shift_range <= 0 and height_shift_range <= 0:
        return image
    rows, cols = image.shape[:2]
    tx = np.random.uniform(-width_shift_range * cols, width_shift_range * cols)
    ty = np.random.uniform(-height_shift_range * rows, height_shift_range * rows)
    M = np.float32([[1, 0, tx], [0, 1, ty]])
    shifted_image = cv2.warpAffine(image, M, (cols, rows), borderMode=cv2.BORDER_REPLICATE)
    return shifted_image

def random_zoom(image: np.ndarray, zoom_range: Union[float, Tuple[float, float]]) -> np.ndarray:
    """Áp dụng zoom ngẫu nhiên (giữ nguyên tâm ảnh)."""
    if isinstance(zoom_range, float):
        if zoom_range <= 0: return image
        zx = zy = np.random.uniform(1 - zoom_range, 1 + zoom_range)
    elif isinstance(zoom_range, (list, tuple)) and len(zoom_range) == 2:
        if zoom_range[0] >= zoom_range[1]: return image # Khoảng không hợp lệ
        zx = zy = np.random.uniform(zoom_range[0], zoom_range[1])
    else:
        return image # Không zoom nếu tham số không hợp lệ

    rows, cols = image.shape[:2]
    # Tạo ma trận zoom quanh tâm
    M = cv2.getRotationMatrix2D((cols / 2, rows / 2), 0, zx) # angle=0, scale=zx
    # Điều chỉnh phần dịch chuyển để giữ tâm
    M[0, 2] += (1 - zx) * cols / 2
    M[1, 2] += (1 - zy) * rows / 2
    zoomed_image = cv2.warpAffine(image, M, (cols, rows), borderMode=cv2.BORDER_REPLICATE)
    return zoomed_image

def random_brightness(image: np.ndarray, brightness_range: Tuple[float, float]) -> np.ndarray:
    """Điều chỉnh độ sáng ngẫu nhiên."""
    if brightness_range[0] >= brightness_range[1] or brightness_range[0] < 0:
        return image

    # Chuyển sang float nếu là uint8 để nhân
    dtype_orig = image.dtype
    is_float = np.issubdtype(dtype_orig, np.floating)

    if not is_float:
        image_float = image.astype(np.float32)
    else:
        image_float = image.copy()

    brightness_factor = np.random.uniform(brightness_range[0], brightness_range[1])
    bright_image = image_float * brightness_factor

    # Clip giá trị và chuyển về kiểu cũ
    if is_float:
        # Nếu đầu vào là float (thường là [0, 1]), clip về [0, 1]
        bright_image = np.clip(bright_image, 0.0, 1.0)
    else:
        # Nếu đầu vào là uint8, clip về [0, 255] và chuyển đổi lại
        bright_image = np.clip(bright_image, 0, 255)
        bright_image = bright_image.astype(dtype_orig)

    return bright_image

# --- Hàm Augmentation Tổng hợp ---

def augment_image(
    image: np.ndarray,
    rotation: float = 5.0,       # Độ xoay tối đa (+/-)
    width_shift: float = 0.05,   # Tỷ lệ dịch ngang tối đa (+/-)
    height_shift: float = 0.05,  # Tỷ lệ dịch dọc tối đa (+/-)
    zoom: float = 0.05,          # Tỷ lệ zoom tối đa ([1-zoom, 1+zoom])
    brightness: Tuple[float, float] = (0.95, 1.05) # Khoảng thay đổi độ sáng
) -> np.ndarray:
    """
    Áp dụng một chuỗi các phép tăng cường ngẫu nhiên cho ảnh.

    Args:
        image (np.ndarray): Ảnh đầu vào (dạng NumPy array, uint8 hoặc float).
        rotation (float): Phạm vi xoay ngẫu nhiên (độ).
        width_shift (float): Phạm vi dịch chuyển ngang (tỷ lệ so với chiều rộng).
        height_shift (float): Phạm vi dịch chuyển dọc (tỷ lệ so với chiều cao).
        zoom (float): Phạm vi zoom ngẫu nhiên (tỷ lệ).
        brightness (Tuple[float, float]): Khoảng điều chỉnh độ sáng [min_factor, max_factor].

    Returns:
        np.ndarray: Ảnh đã được tăng cường.
    """
    augmented = image.copy() # Làm việc trên bản sao

    # Áp dụng các phép biến đổi theo thứ tự ngẫu nhiên hoặc cố định
    # (Thứ tự có thể ảnh hưởng kết quả cuối cùng)
    augmented = random_rotation(augmented, rotation)
    augmented = random_shift(augmented, width_shift, height_shift)
    augmented = random_zoom(augmented, zoom)
    augmented = random_brightness(augmented, brightness)
    # Có thể thêm các phép khác ở đây (shear, noise, etc.)

    return augmented


# --- Chạy thử (khi chạy file này trực tiếp) ---
if __name__ == "__main__":
    print("--- Testing Data Augmentation Utils ---")

    # Thử tải ảnh thật hoặc tạo ảnh giả
    try:
        # Cần có matplotlib để hiển thị ảnh test
        import matplotlib.pyplot as plt
        VISUALIZE = True
        # Tạo ảnh giả gradient màu xám
        dummy_image_uint8 = np.zeros((64, 64, 3), dtype=np.uint8)
        dummy_image_uint8[:, :, 0] = np.tile(np.linspace(0, 255, 64), (64, 1)) # Red gradient
        dummy_image_uint8[:, :, 1] = np.tile(np.linspace(0, 255, 64).reshape(-1,1), (1, 64)) # Green gradient
        print("Created dummy uint8 image.")
        dummy_image_float32 = dummy_image_uint8.astype(np.float32) / 255.0
        print("Created dummy float32 image.")

    except ImportError:
        print("Matplotlib not found. Cannot visualize augmentation results.")
        VISUALIZE = False
        dummy_image_float32 = np.random.rand(32, 32, 3).astype(np.float32) # Ảnh float random nếu không vẽ được

    print("\nApplying augmentations...")
    augmented_img = augment_image(
        dummy_image_float32,
        rotation=15,
        width_shift=0.1,
        height_shift=0.1,
        zoom=0.15,
        brightness=(0.8, 1.2)
    )
    print(f"Augmented image shape: {augmented_img.shape}, dtype: {augmented_img.dtype}")

    if VISUALIZE:
        plt.figure(figsize=(8, 4))
        plt.subplot(1, 2, 1)
        plt.imshow(dummy_image_float32) # Ảnh gốc là float [0, 1]
        plt.title("Original (Float32)")
        plt.axis('off')

        plt.subplot(1, 2, 2)
        plt.imshow(np.clip(augmented_img, 0, 1)) # Clip lại phòng trường hợp float vượt 0-1 nhẹ
        plt.title("Augmented")
        plt.axis('off')

        plt.tight_layout()
        plt.show()

    print("\n--- Test Finished ---")