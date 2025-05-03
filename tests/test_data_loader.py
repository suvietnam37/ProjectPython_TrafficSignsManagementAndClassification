# tests/test_data_loader.py

import unittest
import os
import numpy as np
import pandas as pd
import sys

# --- Thêm thư mục gốc vào sys.path để import các module dự án ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) # Đi lên 1 cấp từ tests/
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import config
from utils.data_loader import (
    load_train_data,
    load_test_data,
    preprocess_data,
    split_data,
    load_data_npy
)

# --- Tạo dữ liệu giả để test (Quan trọng!) ---
# Thay vì dựa vào dữ liệu thật, tốt nhất là tạo dữ liệu giả trong thư mục test
TEST_DATA_ROOT = os.path.join(project_root, 'tests', 'test_data')
FAKE_TRAIN_DIR = os.path.join(TEST_DATA_ROOT, 'fake_gtsrb', 'Train')
FAKE_TEST_DIR = os.path.join(TEST_DATA_ROOT, 'fake_gtsrb', 'Test')
FAKE_TEST_CSV = os.path.join(TEST_DATA_ROOT, 'fake_gtsrb', 'fake_gt.csv')
FAKE_NPY_FILE = os.path.join(TEST_DATA_ROOT, 'fake_processed.npz')

def setup_fake_data():
    """Tạo cấu trúc thư mục và file dữ liệu giả cho việc test."""
    print("Setting up fake data for tests...")
    os.makedirs(FAKE_TRAIN_DIR, exist_ok=True)
    os.makedirs(os.path.join(FAKE_TRAIN_DIR, '0'), exist_ok=True) # Lớp 0
    os.makedirs(os.path.join(FAKE_TRAIN_DIR, '1'), exist_ok=True) # Lớp 1
    os.makedirs(FAKE_TEST_DIR, exist_ok=True)

    # Tạo ảnh giả (ảnh nhỏ màu đen)
    dummy_img = np.zeros((10, 10, 3), dtype=np.uint8)
    # Lưu ảnh giả cho train
    cv2.imwrite(os.path.join(FAKE_TRAIN_DIR, '0', 'img0_1.png'), dummy_img)
    cv2.imwrite(os.path.join(FAKE_TRAIN_DIR, '0', 'img0_2.png'), dummy_img)
    cv2.imwrite(os.path.join(FAKE_TRAIN_DIR, '1', 'img1_1.png'), dummy_img)
    # Lưu ảnh giả cho test
    cv2.imwrite(os.path.join(FAKE_TEST_DIR, 'test_img1.png'), dummy_img)
    cv2.imwrite(os.path.join(FAKE_TEST_DIR, 'test_img2.png'), dummy_img)

    # Tạo file CSV giả cho test
    fake_csv_data = {'Filename': ['test_img1.png', 'test_img2.png'], 'ClassId': [0, 1]}
    pd.DataFrame(fake_csv_data).to_csv(FAKE_TEST_CSV, index=False, sep=';')

    # Tạo file NPZ giả
    fake_images = np.random.rand(5, 32, 32, 3).astype(np.float32)
    fake_labels = np.eye(config.NUM_CLASSES)[np.random.randint(0, config.NUM_CLASSES, 5)].astype(np.float32)
    np.savez(FAKE_NPY_FILE, images=fake_images, labels=fake_labels)
    print("Fake data setup complete.")

def teardown_fake_data():
    """Xóa dữ liệu giả sau khi test."""
    import shutil
    if os.path.exists(TEST_DATA_ROOT):
        print("Tearing down fake data...")
        shutil.rmtree(TEST_DATA_ROOT)
        print("Fake data removed.")

# --- Lớp Test ---
class TestDataLoader(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Chạy một lần trước tất cả các test trong lớp này."""
        # Chỉ import cv2 nếu cần thiết để tránh lỗi nếu chưa cài
        try:
             global cv2
             import cv2
             cls.cv2_available = True
             setup_fake_data()
        except ImportError:
             cls.cv2_available = False
             print("WARNING: OpenCV (cv2) not found. Skipping tests requiring fake image creation/loading.")

    @classmethod
    def tearDownClass(cls):
        """Chạy một lần sau tất cả các test trong lớp này."""
        if cls.cv2_available:
             teardown_fake_data()

    # --- Test load_train_data ---
    @unittest.skipUnless(lambda: hasattr(TestDataLoader, 'cv2_available') and TestDataLoader.cv2_available, "cv2 not available")
    def test_load_train_data_fake(self):
        """Kiểm thử load_train_data với dữ liệu giả."""
        images, labels = load_train_data(FAKE_TRAIN_DIR, 32, 32, 2) # Chỉ có 2 lớp giả
        self.assertIsNotNone(images)
        self.assertIsNotNone(labels)
        self.assertEqual(images.shape, (3, 32, 32, 3)) # 3 ảnh, size 32x32, 3 kênh màu RGB
        self.assertEqual(labels.shape, (3,))
        self.assertTrue(np.issubdtype(images.dtype, np.uint8)) # Kiểm tra kiểu dữ liệu gốc
        self.assertTrue(np.all(np.unique(labels) == [0, 1])) # Kiểm tra nhãn

    def test_load_train_data_not_found(self):
        """Kiểm thử load_train_data khi thư mục không tồn tại."""
        images, labels = load_train_data("/path/to/nonexistent/dir", 32, 32, 43)
        self.assertIsNone(images)
        self.assertIsNone(labels)

    # --- Test load_test_data ---
    @unittest.skipUnless(lambda: hasattr(TestDataLoader, 'cv2_available') and TestDataLoader.cv2_available, "cv2 not available")
    def test_load_test_data_fake(self):
        """Kiểm thử load_test_data với dữ liệu giả."""
        images, labels = load_test_data(FAKE_TEST_DIR, FAKE_TEST_CSV, 32, 32)
        self.assertIsNotNone(images)
        self.assertIsNotNone(labels)
        self.assertEqual(images.shape, (2, 32, 32, 3)) # 2 ảnh
        self.assertEqual(labels.shape, (2,))
        self.assertTrue(np.all(np.unique(labels) == [0, 1]))

    def test_load_test_data_files_not_found(self):
        """Kiểm thử load_test_data khi file/thư mục không tồn tại."""
        # Thiếu dir
        images, labels = load_test_data("/path/to/nonexistent/dir", FAKE_TEST_CSV, 32, 32)
        self.assertIsNone(images)
        self.assertIsNone(labels)
        # Thiếu csv
        images, labels = load_test_data(FAKE_TEST_DIR, "/path/to/nonexistent.csv", 32, 32)
        self.assertIsNone(images)
        self.assertIsNone(labels)

    # --- Test preprocess_data ---
    def test_preprocess_data(self):
        """Kiểm thử chuẩn hóa và one-hot encoding."""
        # Ảnh uint8
        dummy_images = (np.random.rand(5, 32, 32, 3) * 255).astype(np.uint8)
        dummy_labels = np.array([0, 1, 2, 1, 0])
        processed_images, processed_labels = preprocess_data(dummy_images, dummy_labels, 3)

        self.assertIsNotNone(processed_images)
        self.assertIsNotNone(processed_labels)
        self.assertTrue(np.issubdtype(processed_images.dtype, np.floating)) # Phải là float
        self.assertLessEqual(processed_images.max(), 1.0) # Giá trị max <= 1.0
        self.assertGreaterEqual(processed_images.min(), 0.0) # Giá trị min >= 0.0
        self.assertEqual(processed_labels.shape, (5, 3)) # Shape one-hot
        self.assertTrue(np.all((processed_labels == 0) | (processed_labels == 1))) # Chỉ chứa 0 và 1
        self.assertTrue(np.all(processed_labels.sum(axis=1) == 1)) # Tổng mỗi hàng là 1

    def test_preprocess_data_invalid_labels(self):
        """Kiểm thử việc lọc bỏ nhãn không hợp lệ."""
        dummy_images = (np.random.rand(5, 32, 32, 3) * 255).astype(np.uint8)
        dummy_labels = np.array([0, 1, 45, 1, 0]) # Nhãn 45 không hợp lệ với num_classes=3
        processed_images, processed_labels = preprocess_data(dummy_images, dummy_labels, 3)
        self.assertEqual(processed_images.shape[0], 4) # Chỉ còn 4 mẫu
        self.assertEqual(processed_labels.shape[0], 4)

    # --- Test split_data ---
    def test_split_data(self):
        """Kiểm thử việc chia dữ liệu."""
        num_samples = 100
        dummy_images = np.random.rand(num_samples, 32, 32, 3)
        dummy_labels = np.random.randint(0, 5, size=num_samples) # 5 lớp
        test_ratio = 0.3

        train_img, val_img, train_lbl, val_lbl = split_data(
            dummy_images, dummy_labels, test_size=test_ratio, random_state=42
        )

        expected_val_count = int(num_samples * test_ratio)
        expected_train_count = num_samples - expected_val_count

        self.assertEqual(train_img.shape[0], expected_train_count)
        self.assertEqual(val_img.shape[0], expected_val_count)
        self.assertEqual(train_lbl.shape[0], expected_train_count)
        self.assertEqual(val_lbl.shape[0], expected_val_count)

        # Kiểm tra stratify (tỷ lệ lớp nên tương tự nhau) - kiểm tra đơn giản
        _, train_counts = np.unique(train_lbl, return_counts=True)
        _, val_counts = np.unique(val_lbl, return_counts=True)
        # Tỷ lệ không cần chính xác tuyệt đối do làm tròn số nguyên
        self.assertTrue(np.allclose(train_counts / expected_train_count,
                                     val_counts / expected_val_count, atol=0.1))

    # --- Test load_data_npy ---
    def test_load_data_npy_fake(self):
        """Kiểm thử tải dữ liệu từ file NPZ giả."""
        images, labels = load_data_npy(FAKE_NPY_FILE)
        self.assertIsNotNone(images)
        self.assertIsNotNone(labels)
        self.assertEqual(images.shape[0], 5)
        self.assertEqual(labels.shape[0], 5)
        self.assertTrue(np.issubdtype(images.dtype, np.floating))
        self.assertTrue(np.issubdtype(labels.dtype, np.floating)) # one-hot float

    def test_load_data_npy_not_found(self):
        """Kiểm thử khi file NPZ không tồn tại."""
        data = load_data_npy("/path/to/nonexistent.npz")
        self.assertIsNone(data)

    def test_load_data_npy_invalid_structure(self):
        """Kiểm thử khi file NPZ thiếu key 'images' hoặc 'labels'."""
        # Tạo file NPZ lỗi
        error_npy_path = os.path.join(TEST_DATA_ROOT, 'error.npz')
        dummy_data = {'image_data': np.random.rand(2,2), 'label_data': np.random.rand(2)}
        np.savez(error_npy_path, **dummy_data)

        data = load_data_npy(error_npy_path)
        self.assertIsNone(data)
        # os.remove(error_npy_path) # Xóa file lỗi


# --- Chạy Test ---
if __name__ == '__main__':
    # Cần cài đặt OpenCV để tạo dữ liệu giả: pip install opencv-python pandas
    print("Running Data Loader Unit Tests...")
    # Kiểm tra xem có nên chạy setup/teardown không
    try:
        import cv2
        unittest.main() # Chạy tất cả các test trong file này
    except ImportError:
         print("\nSKIPPING TESTS requiring OpenCV as it is not installed.")
         # Chỉ chạy các test không yêu cầu dữ liệu giả
         suite = unittest.TestSuite()
         suite.addTest(unittest.makeSuite(TestDataLoader, "test_load_train_data_not_found"))
         suite.addTest(unittest.makeSuite(TestDataLoader, "test_load_test_data_files_not_found"))
         suite.addTest(unittest.makeSuite(TestDataLoader, "test_preprocess_data"))
         suite.addTest(unittest.makeSuite(TestDataLoader, "test_preprocess_data_invalid_labels"))
         suite.addTest(unittest.makeSuite(TestDataLoader, "test_split_data"))
         suite.addTest(unittest.makeSuite(TestDataLoader, "test_load_data_npy_not_found"))
         # Không thể chạy test_load_data_npy_fake và test_load_data_npy_invalid_structure nếu không có setup
         runner = unittest.TextTestRunner()
         runner.run(suite)