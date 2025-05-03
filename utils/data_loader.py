import os
import cv2
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from tensorflow.keras.utils import to_categorical  # type: ignore
import config  # Import cấu hình

def load_train_data(train_dir, img_height, img_width, num_classes):
    """
    Tải dữ liệu huấn luyện từ cấu trúc thư mục.
    Ảnh sẽ được đọc, resize và chuyển sang định dạng RGB.
    """
    images = []
    labels = []
    print(f"Loading training data from: {train_dir}")

    if not os.path.isdir(train_dir):
        print(f"ERROR: Training directory not found: {train_dir}")
        return None, None

    for class_id in range(num_classes):
        class_path = os.path.join(train_dir, str(class_id))
        if not os.path.isdir(class_path):
            continue  # Skip if class directory is missing

        for img_name in os.listdir(class_path):
            img_path = os.path.join(class_path, img_name)
            try:
                # Đọc ảnh bằng OpenCV (mặc định là BGR)
                img_bgr = cv2.imread(img_path)
                if img_bgr is None:
                    continue

                # Thay đổi kích thước ảnh
                img_resized_bgr = cv2.resize(img_bgr, (img_width, img_height), interpolation=cv2.INTER_AREA)

                # *** CHUYỂN ĐỔI SANG RGB ***
                img_rgb = cv2.cvtColor(img_resized_bgr, cv2.COLOR_BGR2RGB)

                # Thêm ảnh RGB vào danh sách
                images.append(img_rgb)
                labels.append(class_id)
            except Exception as e:
                print(f"Error loading/processing image {img_path}: {e}")
                continue  # Bỏ qua ảnh lỗi

    if not images:
        print(f"ERROR: No images were loaded from {train_dir}.")
        return None, None

    print(f"Loaded {len(images)} training images (as RGB).")
    return np.array(images, dtype=np.uint8), np.array(labels, dtype=np.int32)

def load_test_data(test_dir, csv_path, img_height, img_width):
    """
    Tải dữ liệu kiểm thử từ thư mục ảnh và file CSV.
    Ảnh sẽ được đọc, resize và chuyển sang định dạng RGB.
    """
    images = []
    labels = []
    print(f"Loading test data from: {test_dir} and {csv_path}")

    if not os.path.isfile(csv_path) or not os.path.isdir(test_dir):
        print(f"ERROR: Test directory or CSV file not found.")
        return None, None

    try:
        test_df = pd.read_csv(csv_path, delimiter=';')
        filenames = test_df.iloc[:, 0].values
        class_ids = test_df.iloc[:, -1].values.astype(int)
    except Exception as e:
        print(f"Error reading CSV {csv_path}: {e}")
        return None, None

    loaded_count = 0
    skipped_count = 0
    for filename, class_id in zip(filenames, class_ids):
        img_path = os.path.join(test_dir, filename)
        if not os.path.isfile(img_path):
            skipped_count += 1
            continue

        try:
            img_bgr = cv2.imread(img_path)
            if img_bgr is None:
                skipped_count += 1
                continue

            img_resized_bgr = cv2.resize(img_bgr, (img_width, img_height), interpolation=cv2.INTER_AREA)
            img_rgb = cv2.cvtColor(img_resized_bgr, cv2.COLOR_BGR2RGB)

            images.append(img_rgb)
            labels.append(class_id)
            loaded_count += 1
        except Exception as e:
            print(f"Error loading/processing image {img_path}: {e}")
            skipped_count += 1
            continue

    if not images:
        print(f"ERROR: No test images were successfully loaded.")
        return None, None

    print(f"Loaded {loaded_count} test images (as RGB), skipped {skipped_count}.")
    return np.array(images, dtype=np.uint8), np.array(labels, dtype=np.int32)

def preprocess_data(images, labels, num_classes):
    """
    Chuẩn hóa ảnh về [0, 1] (dạng float32) và chuyển nhãn sang one-hot encoding.
    Loại bỏ các nhãn >= num_classes để tránh lỗi.
    """
    valid_mask = labels < num_classes
    if not np.all(valid_mask):
        invalid_count = np.sum(~valid_mask)
        print(f"  WARNING: Found {invalid_count} invalid label(s) >= {num_classes}. These will be filtered out.")
        images = images[valid_mask]
        labels = labels[valid_mask]

    images_processed = images.astype('float32') / 255.0
    labels_one_hot = to_categorical(labels, num_classes=num_classes)
    return images_processed, labels_one_hot

def split_data(images, labels, test_size=0.2, random_state=42):
    """Chia dữ liệu thành tập train và validation, giữ nguyên tỷ lệ lớp."""
    stratify_labels = labels
    if len(labels.shape) > 1 and labels.shape[1] > 1:
        stratify_labels = np.argmax(labels, axis=1)

    return train_test_split(
        images, labels,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify_labels
    )

def load_data_npy(file_path):
    """Tải dữ liệu từ file .npy (dạng dictionary)."""
    if not os.path.isfile(file_path):
        print(f"ERROR: NPY file not found: {file_path}")
        return None
    try:
        # Dùng np.load và truy cập các key trực tiếp từ đối tượng NpzFile
        data = np.load(file_path, allow_pickle=True)
        
        # Kiểm tra xem các key cần thiết có trong file không
        if 'images' in data and 'labels' in data:
            print(f"Data loaded successfully from {file_path}")
            return data['images'], data['labels']
        else:
            print(f"ERROR: Invalid data structure in NPY file: {file_path}")
            return None
    except Exception as e:
        print(f"ERROR: Failed to load data from {file_path}. Reason: {e}")
        return None

