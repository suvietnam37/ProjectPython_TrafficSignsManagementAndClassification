# utils/model_utils.py

import os
import tensorflow as tf
from tensorflow import keras
import json
import datetime
import config # Để lấy đường dẫn mặc định

# --- Lưu/Tải Mô hình Keras ---

def save_keras_model(model, filepath=config.MODEL_SAVE_PATH):
    """Lưu mô hình Keras vào đường dẫn chỉ định (định dạng .keras)."""
    try:
        # Đảm bảo thư mục đích tồn tại
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        model.save(filepath)
        print(f"Model saved successfully to: {filepath}")
        return True
    except Exception as e:
        print(f"Error saving Keras model to {filepath}: {e}")
        return False

def load_keras_model(filepath=config.MODEL_SAVE_PATH):
    """Tải mô hình Keras từ đường dẫn chỉ định."""
    if not os.path.exists(filepath):
        print(f"Error: Model file not found at {filepath}")
        return None
    try:
        model = keras.models.load_model(filepath)
        print(f"Model loaded successfully from: {filepath}")
        return model
    except Exception as e:
        print(f"Error loading Keras model from {filepath}: {e}")
        return None

# --- Lưu Lịch sử Huấn luyện (Ví dụ: lưu dưới dạng JSON) ---

def save_training_history(history, filepath):
    """
    Lưu đối tượng history (từ model.fit) vào file JSON.
    Lưu ý: history.history chứa các mảng numpy, cần chuyển đổi sang list.
    """
    if not hasattr(history, 'history') or not history.history:
        print("Error: Invalid history object provided.")
        return False

    history_dict = {}
    for key, value in history.history.items():
        # Chuyển đổi numpy array thành list để có thể lưu JSON
        if isinstance(value, np.ndarray):
            history_dict[key] = value.tolist()
        elif isinstance(value, list):
             history_dict[key] = value # Giữ nguyên nếu đã là list
        else:
             print(f"Warning: Skipping non-list/array history key '{key}' of type {type(value)}")

    # Thêm các thông tin khác nếu cần (ví dụ: thời gian, params)
    history_dict['epoch'] = history.epoch # Danh sách các epoch đã chạy
    history_dict['params'] = history.params # Tham số huấn luyện
    history_dict['save_time'] = datetime.datetime.now().isoformat()

    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(history_dict, f, indent=4, ensure_ascii=False)
        print(f"Training history saved successfully to: {filepath}")
        return True
    except Exception as e:
        print(f"Error saving training history to {filepath}: {e}")
        return False

def load_training_history(filepath):
    """Tải lịch sử huấn luyện từ file JSON."""
    if not os.path.exists(filepath):
        print(f"Error: History file not found at {filepath}")
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            history_dict = json.load(f)
        print(f"Training history loaded successfully from: {filepath}")
        # Có thể chuyển đổi lại thành đối tượng giống Keras History nếu cần,
        # nhưng thường dùng dictionary là đủ để vẽ đồ thị hoặc phân tích.
        return history_dict
    except Exception as e:
        print(f"Error loading training history from {filepath}: {e}")
        return None

# --- Các hàm tiện ích khác (Ví dụ) ---

def get_model_summary_text(model):
    """Lấy model summary dưới dạng text."""
    if model is None:
        return "Model not loaded."
    stringlist = []
    model.summary(print_fn=lambda x: stringlist.append(x))
    return "\n".join(stringlist)


# --- Chạy thử (khi chạy file này trực tiếp) ---
if __name__ == "__main__":
    print("--- Testing Model Utils ---")

    # Tạo một mô hình đơn giản để test lưu/tải
    print("\n1. Testing Save/Load Model:")
    dummy_model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(10,)),
        tf.keras.layers.Dense(5, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    test_model_path = os.path.join(config.MODELS_DIR, 'dummy_test_model.keras')
    save_success = save_keras_model(dummy_model, test_model_path)

    if save_success:
        loaded_model = load_keras_model(test_model_path)
        if loaded_model:
            print("Dummy model summary after loading:")
            loaded_model.summary()
        # Xóa file test
        # os.remove(test_model_path)

    # Tạo một đối tượng history giả để test
    print("\n2. Testing Save/Load History:")
    class DummyHistory:
        def __init__(self):
            self.history = {
                'loss': np.array([0.5, 0.3, 0.2]),
                'accuracy': np.array([0.8, 0.9, 0.95]),
                'val_loss': np.array([0.6, 0.4, 0.35]),
                'val_accuracy': np.array([0.75, 0.85, 0.91])
            }
            self.epoch = [0, 1, 2]
            self.params = {'verbose': 1, 'epochs': 3, 'steps': 100}

    dummy_history = DummyHistory()
    test_history_path = os.path.join(config.MODELS_DIR, 'dummy_test_history.json')
    save_hist_success = save_training_history(dummy_history, test_history_path)

    if save_hist_success:
        loaded_history = load_training_history(test_history_path)
        if loaded_history:
            print("Loaded history (first few items):")
            print({k: v[:2] if isinstance(v, list) else v for k, v in loaded_history.items()})
        # Xóa file test
        # os.remove(test_history_path)

    print("\n--- Test Finished ---")