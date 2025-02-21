import os
import cv2
import numpy as np
import random

def augment_data():
    
    # Đọc ảnh từ thư mục cleaned/
    for filename in os.listdir('cleaned'):
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        img_path = os.path.join('cleaned', filename)
        img = cv2.imread(img_path)
        if img is None:
            print(f"Không thể đọc ảnh: {img_path}")
            continue
        rows, cols, _ = img.shape
        base_filename = os.path.splitext(filename)[0]

        # Xoay ảnh
        angle = random.randint(-30, 30)
        M = cv2.getRotationMatrix2D((cols / 2, rows / 2), angle, 1)
        dst = cv2.warpAffine(img, M, (cols, rows))
        cv2.imwrite(f'augmented/{base_filename}_rotate.jpg', dst)

        # Dịch chuyển ảnh
        shift_x = random.randint(-50, 50)
        shift_y = random.randint(-50, 50)
        M = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
        dst = cv2.warpAffine(img, M, (cols, rows))
        cv2.imwrite(f'augmented/{base_filename}_shift.jpg', dst)

        # Thay đổi độ sáng
        value = random.randint(-50, 50)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype('float32')
        hsv[:, :, 2] = cv2.add(hsv[:, :, 2], value)
        dst = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        cv2.imwrite(f'augmented/{base_filename}_bright.jpg', dst)

        # Thay đổi độ tương phản
        alpha = random.uniform(0.5, 1.5)
        beta = random.randint(-50, 50)
        dst = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)
        cv2.imwrite(f'augmented/{base_filename}_contrast.jpg', dst)

        # Lật ảnh
        dst = cv2.flip(img, 1)
        cv2.imwrite(f'augmented/{base_filename}_flip.jpg', dst)

        # Thay đổi kích thước (scale nhỏ hơn hoặc lớn hơn)
        scale = random.uniform(0.5, 1.5)
        dst = cv2.resize(img, (int(cols * scale), int(rows * scale)))
        cv2.imwrite(f'augmented/{base_filename}_resize.jpg', dst)

        # Chuyển đổi ảnh xám
        dst = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(f'augmented/{base_filename}_gray.jpg', dst)

    print('Tăng cường dữ liệu đã hoàn tất!')

augment_data()
