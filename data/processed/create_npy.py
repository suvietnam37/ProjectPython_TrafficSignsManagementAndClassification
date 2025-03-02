import os
import cv2
import numpy as np
from sklearn.model_selection import train_test_split

# Đường dẫn thư mục chứa ảnh đã tăng cường
AUGMENTED_DIR = "data/augmented"
PROCESSED_DIR = "data/processed"

# Kích thước chuẩn của ảnh
IMG_SIZE = 32

# Tạo thư mục processed nếu chưa có
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Danh sách chứa dữ liệu và nhãn
data = []
labels = []

# Đọc ảnh từ thư mục augmented/
for filename in os.listdir(AUGMENTED_DIR):
    if filename.endswith(('.png', '.jpg', '.jpeg')):
        img_path = os.path.join(AUGMENTED_DIR, filename)
        
        # Đọc ảnh và resize về 32x32
        img = cv2.imread(img_path)
        img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
        
        # Chuyển đổi ảnh thành numpy array và chuẩn hóa về [0,1]
        img = img.astype(np.float32) / 255.0
        
        # Lấy nhãn từ tên file (giả sử nhãn nằm ở đầu tên file, ví dụ: "00001_rotate.jpg" → nhãn = 00001)
        label = int(filename.split('_')[0])  # Chuyển nhãn từ string sang số nguyên
        
        data.append(img)
        labels.append(label)

# Chuyển danh sách thành numpy array
data = np.array(data)
labels = np.array(labels)

# Chia dữ liệu thành train (70%), validation (15%), test (15%)
X_train, X_temp, y_train, y_temp = train_test_split(data, labels, test_size=0.3, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

# Lưu dữ liệu đã chuẩn hóa vào file .npy
np.save(os.path.join(PROCESSED_DIR, "train.npy"), (X_train, y_train))
np.save(os.path.join(PROCESSED_DIR, "val.npy"), (X_val, y_val))
np.save(os.path.join(PROCESSED_DIR, "test.npy"), (X_test, y_test))

print(" Dữ liệu đã được chuẩn hóa và lưu vào thư mục processed/")
