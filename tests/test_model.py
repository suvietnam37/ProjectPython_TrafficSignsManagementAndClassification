# tests/test_model.py

import unittest
import sys
import os
import numpy as np

# --- Thêm thư mục gốc vào sys.path ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Import các thành phần cần test và config ---
try:
    import tensorflow as tf
    from tensorflow import keras
    from models.model_cnn import build_basic_cnn, build_improved_cnn
    import config
    TF_KERAS_AVAILABLE = True
except ImportError:
    TF_KERAS_AVAILABLE = False
    print("WARNING: TensorFlow/Keras not found. Skipping model build tests.")

# --- Lớp Test ---
# Bỏ qua toàn bộ lớp nếu không có TensorFlow/Keras
@unittest.skipUnless(TF_KERAS_AVAILABLE, "TensorFlow/Keras not installed")
class TestModelCNN(unittest.TestCase):

    def test_build_basic_cnn_structure(self):
        """Kiểm tra xem build_basic_cnn có trả về một model Keras hợp lệ không."""
        print("\nTesting basic_cnn build...") # Thêm print để dễ theo dõi
        input_shape = (config.IMG_HEIGHT, config.IMG_WIDTH, 3)
        num_classes = config.NUM_CLASSES

        model = build_basic_cnn(input_shape=input_shape, num_classes=num_classes)

        self.assertIsNotNone(model)
        self.assertIsInstance(model, keras.Model)
        print("Basic model built successfully.")

    def test_build_basic_cnn_input_output_shape(self):
        """Kiểm tra input/output shape của mô hình basic_cnn."""
        print("\nTesting basic_cnn input/output shapes...")
        input_shape = (config.IMG_HEIGHT, config.IMG_WIDTH, 3)
        num_classes = config.NUM_CLASSES
        batch_size = 4 # Kích thước batch giả định để kiểm tra

        model = build_basic_cnn(input_shape=input_shape, num_classes=num_classes)

        # Kiểm tra input shape mong đợi
        # model.input_shape là (None, H, W, C) với None là batch size
        self.assertEqual(model.input_shape, (None,) + input_shape)

        # Kiểm tra output shape mong đợi
        # model.output_shape là (None, num_classes)
        self.assertEqual(model.output_shape, (None, num_classes))

        # Thử tạo dữ liệu giả và gọi predict để chắc chắn shape hoạt động
        dummy_input = np.random.rand(batch_size, *input_shape).astype(np.float32)
        try:
             output = model.predict(dummy_input, verbose=0) # verbose=0 để không in progress bar
             self.assertEqual(output.shape, (batch_size, num_classes))
             print("Basic model input/output shapes verified.")
        except Exception as e:
             self.fail(f"Model prediction failed with shape error: {e}")


    def test_build_improved_cnn_structure(self):
        """Kiểm tra xem build_improved_cnn có trả về một model Keras hợp lệ không."""
        print("\nTesting improved_cnn build...")
        input_shape = (config.IMG_HEIGHT, config.IMG_WIDTH, 3)
        num_classes = config.NUM_CLASSES

        model = build_improved_cnn(input_shape=input_shape, num_classes=num_classes)

        self.assertIsNotNone(model)
        self.assertIsInstance(model, keras.Model)
        print("Improved model built successfully.")

    def test_build_improved_cnn_input_output_shape(self):
        """Kiểm tra input/output shape của mô hình improved_cnn."""
        print("\nTesting improved_cnn input/output shapes...")
        input_shape = (config.IMG_HEIGHT, config.IMG_WIDTH, 3)
        num_classes = config.NUM_CLASSES
        batch_size = 4

        model = build_improved_cnn(input_shape=input_shape, num_classes=num_classes)

        self.assertEqual(model.input_shape, (None,) + input_shape)
        self.assertEqual(model.output_shape, (None, num_classes))

        # Thử tạo dữ liệu giả và gọi predict
        dummy_input = np.random.rand(batch_size, *input_shape).astype(np.float32)
        try:
            output = model.predict(dummy_input, verbose=0)
            self.assertEqual(output.shape, (batch_size, num_classes))
            print("Improved model input/output shapes verified.")
        except Exception as e:
            self.fail(f"Model prediction failed with shape error: {e}")

    def test_model_compilation_possible(self):
        """Kiểm tra xem các mô hình có thể được biên dịch không."""
        print("\nTesting model compilation...")
        models_to_test = [
            build_basic_cnn(),
            build_improved_cnn()
        ]
        optimizer = 'adam'
        loss = 'categorical_crossentropy'
        metrics = ['accuracy']

        for i, model in enumerate(models_to_test):
            model_name = model.name # Lấy tên từ model
            print(f"Compiling model: {model_name}")
            try:
                model.compile(optimizer=optimizer, loss=loss, metrics=metrics)
                print(f"Model {model_name} compiled successfully.")
            except Exception as e:
                self.fail(f"Failed to compile model {model_name}: {e}")


# --- Chạy Test ---
if __name__ == '__main__':
    print("Running Model Build Unit Tests...")
    if TF_KERAS_AVAILABLE:
        unittest.main()
    else:
        print("\nSKIPPING TESTS: TensorFlow/Keras is not installed.")