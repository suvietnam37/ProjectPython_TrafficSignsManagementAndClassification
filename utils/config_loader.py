# utils/config_loader.py

import json
import os

# Xác định đường dẫn file settings.json trong thư mục gốc của dự án
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE = os.path.join(BASE_DIR, 'settings.json')

# Cài đặt mặc định
DEFAULT_SETTINGS = {
    "api_url": "http://127.0.0.1:8000/predict",
    "class_images_dir": os.path.join(BASE_DIR, 'gui', 'assets', 'class_images'),
    "database_path": os.path.join(BASE_DIR, 'database', 'history.db')
}

def load_settings():
    """Tải cài đặt từ file JSON. Nếu file không tồn tại hoặc lỗi, trả về cài đặt mặc định."""
    if not os.path.exists(SETTINGS_FILE):
        print(f"Settings file not found at {SETTINGS_FILE}. Using default settings.")
        # Tạo file với cài đặt mặc định nếu chưa có
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            # Đảm bảo các key cần thiết tồn tại, nếu thiếu thì dùng mặc định
            for key, value in DEFAULT_SETTINGS.items():
                if key not in settings:
                    settings[key] = value
            print(f"Settings loaded successfully from {SETTINGS_FILE}")
            return settings
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {SETTINGS_FILE}. Using default settings.")
        # Nếu file JSON lỗi, ghi đè bằng mặc định
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    except Exception as e:
        print(f"Error loading settings from {SETTINGS_FILE}: {e}. Using default settings.")
        return DEFAULT_SETTINGS

def save_settings(settings_dict):
    """Lưu dictionary cài đặt vào file JSON."""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings_dict, f, indent=4, ensure_ascii=False)
        print(f"Settings saved successfully to {SETTINGS_FILE}")
        return True
    except Exception as e:
        print(f"Error saving settings to {SETTINGS_FILE}: {e}")
        return False

# --- Chạy thử (khi chạy file này trực tiếp) ---
if __name__ == "__main__":
    print("--- Testing Config Loader ---")
    # Tải cài đặt (sẽ tạo file nếu chưa có)
    current_settings = load_settings()
    print("\nCurrent Settings:")
    print(current_settings)

    # Thử thay đổi một cài đặt
    current_settings['api_url'] = "http://192.168.1.100:8000/predict_new"
    print("\nAttempting to save modified settings...")
    save_settings(current_settings)

    # Tải lại để kiểm tra
    print("\nReloading settings after save...")
    reloaded_settings = load_settings()
    print(reloaded_settings)
    print("--- Test Finished ---")