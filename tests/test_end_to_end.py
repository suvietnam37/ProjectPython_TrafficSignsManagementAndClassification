# tests/test_end_to_end.py

import unittest
import sys
import os
import time
import subprocess # Để chạy API server và GUI client
import requests # Để kiểm tra API và tương tác
import io
from PIL import Image

# --- Thêm thư mục gốc ---
# ... (Giống các file test khác) ...
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ...

# --- Các biến cấu hình cho test ---
API_HOST = "127.0.0.1"
API_PORT = 8001 # Dùng cổng khác để tránh xung đột với chạy thông thường
API_URL = f"http://{API_HOST}:{API_PORT}"
PREDICT_URL = f"{API_URL}/predict"
HEALTH_URL = f"{API_URL}/health"

# Giả sử có ảnh test hợp lệ
TEST_IMAGE_PATH = os.path.join(project_root, 'tests', 'test_data', 'sample_sign.png') # Cần tạo ảnh này

class TestEndToEnd(unittest.TestCase):

    api_process = None

    @classmethod
    def setUpClass(cls):
        """Khởi động API server trước khi chạy test E2E."""
        print("\nStarting API server for E2E tests...")
        # Lệnh để chạy API server trên cổng test
        # Lưu ý: Đường dẫn python và uvicorn có thể cần điều chỉnh
        api_command = [
            sys.executable, # Đường dẫn đến python interpreter hiện tại
            "-m", "uvicorn",
            "api.app:app",
            "--host", API_HOST,
            "--port", str(API_PORT),
            # "--log-level", "warning" # Giảm output log của server
        ]
        try:
            # Chạy server trong tiến trình nền
            cls.api_process = subprocess.Popen(api_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Đợi một chút để server khởi động
            time.sleep(5) # Có thể cần điều chỉnh thời gian chờ
            # Kiểm tra health check để đảm bảo server sẵn sàng
            response = requests.get(HEALTH_URL, timeout=5)
            if response.status_code != 200:
                raise RuntimeError("API server failed to start properly.")
            print("API server started successfully.")
        except Exception as e:
            print(f"ERROR starting API server: {e}")
            # Dừng tiến trình nếu có lỗi
            if cls.api_process:
                cls.api_process.terminate()
                cls.api_process.wait()
            cls.api_process = None # Đánh dấu là chưa khởi động được
            raise # Ném lại lỗi để unittest biết setup thất bại

        # Tạo ảnh test nếu chưa có
        if not os.path.exists(TEST_IMAGE_PATH):
             os.makedirs(os.path.dirname(TEST_IMAGE_PATH), exist_ok=True)
             img = Image.new('RGB', (32, 32), color = (255, 0, 0)) # Ảnh đỏ 32x32
             img.save(TEST_IMAGE_PATH)
             print(f"Created dummy test image at: {TEST_IMAGE_PATH}")

    @classmethod
    def tearDownClass(cls):
        """Dừng API server sau khi chạy xong test E2E."""
        if cls.api_process:
            print("\nStopping API server...")
            cls.api_process.terminate()
            try:
                # Đợi tiến trình kết thúc hoàn toàn
                cls.api_process.wait(timeout=5)
                print("API server stopped.")
            except subprocess.TimeoutExpired:
                print("API server did not terminate gracefully, killing.")
                cls.api_process.kill()
                cls.api_process.wait()

    @unittest.skipIf(api_process is None, "API Server failed to start, skipping E2E tests.")
    def test_full_prediction_flow(self):
        """Kiểm tra luồng: gửi ảnh -> API xử lý -> nhận kết quả."""
        print("\nTesting full prediction flow (E2E)...")
        self.assertTrue(os.path.exists(TEST_IMAGE_PATH), "Test image file not found.")

        try:
            with open(TEST_IMAGE_PATH, 'rb') as f:
                files = {'file': (os.path.basename(TEST_IMAGE_PATH), f, 'image/png')}
                response = requests.post(PREDICT_URL, files=files, timeout=15)

            self.assertEqual(response.status_code, 200)
            result = response.json()
            self.assertIn("predicted_class", result)
            self.assertIn("confidence", result)
            print(f"E2E Prediction Result: {result}")
            # Có thể thêm assert về kết quả dự đoán cụ thể nếu biết trước ảnh test

        except requests.exceptions.RequestException as e:
            self.fail(f"E2E test failed during API request: {e}")
        except Exception as e:
             self.fail(f"E2E test failed with unexpected error: {e}")

    # Có thể thêm các test E2E khác:
    # - Test luồng GUI (phức tạp hơn, cần điều khiển GUI tự động)
    # - Test luồng ghi vào database sau khi dự đoán thành công

if __name__ == '__main__':
    print("Running End-to-End Tests...")
    # Cần tạo ảnh test trước hoặc đảm bảo nó tồn tại
    # Ví dụ: Tạo ảnh đỏ 32x32 lưu tại tests/test_data/sample_sign.png
    # if not os.path.exists(TEST_IMAGE_PATH):
    #      # Tạo ảnh ở đây nếu cần
    #      pass
    unittest.main()