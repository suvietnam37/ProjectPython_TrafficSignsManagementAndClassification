# tests/test_api.py

import unittest
import sys
import os
import io # Để tạo file ảnh giả trong bộ nhớ
from PIL import Image # Dùng Pillow để tạo ảnh giả

# --- Thêm thư mục gốc vào sys.path ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Import các thành phần cần test và config ---
try:
    from fastapi.testclient import TestClient
    from api.app import app # Import đối tượng FastAPI chính
    import config # Cần để lấy NUM_CLASSES
    FASTAPI_CLIENT_AVAILABLE = True
    # Import thêm predict để kiểm tra model có load được không (gián tiếp)
    try:
        from api.routes import predict
        MODEL_LOADED_SUCCESSFULLY = predict.model is not None
        if not MODEL_LOADED_SUCCESSFULLY:
             print("WARNING in test_api: Model in api.routes.predict is None. /predict tests might fail as expected.")
    except Exception as import_err:
         print(f"WARNING in test_api: Could not import api.routes.predict or access model. Tests may fail. Error: {import_err}")
         MODEL_LOADED_SUCCESSFULLY = False

except ImportError as e:
    print(f"WARNING: fastapi, TestClient or related dependencies not found ({e}). Skipping API tests.")
    FASTAPI_CLIENT_AVAILABLE = False
    MODEL_LOADED_SUCCESSFULLY = False # Không thể kiểm tra model

# --- Lớp Test ---
@unittest.skipUnless(FASTAPI_CLIENT_AVAILABLE, "fastapi and TestClient not available")
class TestAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Khởi tạo TestClient một lần cho cả lớp."""
        cls.client = TestClient(app)
        # Tạo ảnh giả (ảnh PNG 1x1 màu đen)
        cls.dummy_image_bytes = io.BytesIO()
        img = Image.new('RGB', (10, 10), color='black')
        img.save(cls.dummy_image_bytes, format='PNG')
        cls.dummy_image_bytes.seek(0) # Đưa con trỏ về đầu file BytesIO

        # Dữ liệu không phải ảnh
        cls.invalid_file_content = b"this is not an image"

    # --- Test Endpoint Gốc ---
    def test_read_root(self):
        """Kiểm tra endpoint GET /"""
        print("\nTesting GET / endpoint...")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Welcome to the GTSRB Sign Recognition API. Go to /docs for documentation."})
        print("GET / endpoint OK.")

    # --- Test Endpoint Health Check ---
    def test_health_check(self):
        """Kiểm tra endpoint GET /health"""
        print("\nTesting GET /health endpoint...")
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "API is running!"})
        print("GET /health endpoint OK.")

    # --- Test Endpoint Predict thành công ---
    @unittest.skipUnless(MODEL_LOADED_SUCCESSFULLY, "Model not loaded successfully, skipping successful prediction test.")
    def test_predict_image_success(self):
        """Kiểm tra endpoint POST /predict với ảnh hợp lệ."""
        print("\nTesting POST /predict endpoint (success case)...")
        files = {'file': ('test_image.png', self.dummy_image_bytes, 'image/png')}
        response = self.client.post("/predict", files=files)

        # In ra nội dung response nếu lỗi để debug
        if response.status_code != 200:
            print(f"Response Status Code: {response.status_code}")
            try:
                print(f"Response JSON: {response.json()}")
            except Exception:
                print(f"Response Text: {response.text}")

        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("predicted_class", result)
        self.assertIn("confidence", result)
        self.assertIsInstance(result["predicted_class"], int)
        self.assertIsInstance(result["confidence"], float)
        self.assertGreaterEqual(result["predicted_class"], 0)
        self.assertLess(result["predicted_class"], config.NUM_CLASSES) # Nhỏ hơn 43
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 1.0)
        print("POST /predict endpoint (success case) OK.")

    # --- Test Endpoint Predict khi thiếu file ---
    def test_predict_image_no_file(self):
        """Kiểm tra POST /predict khi không gửi file."""
        print("\nTesting POST /predict endpoint (no file)...")
        # Không gửi `files=...`
        response = self.client.post("/predict")
        # FastAPI thường trả về 422 Unprocessable Entity cho lỗi validation input
        self.assertEqual(response.status_code, 422)
        # Kiểm tra nội dung lỗi (tùy chọn, cấu trúc có thể thay đổi)
        # result = response.json()
        # self.assertIn("detail", result)
        # self.assertTrue(any("field required" in err.get("msg", "").lower() for err in result['detail']))
        print("POST /predict endpoint (no file) OK - returned 422.")

    # --- Test Endpoint Predict với file không hợp lệ ---
    @unittest.skipUnless(MODEL_LOADED_SUCCESSFULLY, "Model not loaded successfully, irrelevant to test invalid file.")
    def test_predict_image_invalid_file(self):
        """Kiểm tra POST /predict với nội dung file không phải ảnh."""
        print("\nTesting POST /predict endpoint (invalid file content)...")
        files = {'file': ('invalid.txt', self.invalid_file_content, 'text/plain')}
        response = self.client.post("/predict", files=files)
        # Mong đợi lỗi 400 Bad Request vì tiền xử lý ảnh sẽ thất bại
        self.assertEqual(response.status_code, 400)
        result = response.json()
        self.assertIn("detail", result)
        self.assertTrue("preprocess" in result["detail"].lower()) # Kiểm tra thông báo lỗi
        print("POST /predict endpoint (invalid file content) OK - returned 400.")

    # --- Test Endpoint Predict khi model không được load (khó thực hiện trực tiếp) ---
    # Để test trường hợp này, bạn cần đảm bảo predict.model là None khi chạy test.
    # Cách tốt nhất là xóa hoặc đổi tên file model trước khi chạy test.
    @unittest.skipIf(MODEL_LOADED_SUCCESSFULLY, "Model loaded successfully, cannot test 500 error directly.")
    def test_predict_image_model_not_loaded(self):
        """Kiểm tra POST /predict khi model không load được (trả về 500)."""
        print("\nTesting POST /predict endpoint (model not loaded)...")
        files = {'file': ('test_image.png', self.dummy_image_bytes, 'image/png')}
        response = self.client.post("/predict", files=files)
        self.assertEqual(response.status_code, 500)
        result = response.json()
        self.assertIn("detail", result)
        self.assertTrue("model is not loaded" in result["detail"].lower())
        print("POST /predict endpoint (model not loaded) OK - returned 500.")


# --- Chạy Test ---
if __name__ == '__main__':
    print("Running API Unit Tests...")
    if FASTAPI_CLIENT_AVAILABLE:
        # Chạy test thông thường
        unittest.main()
    else:
        print("\nSKIPPING TESTS: fastapi or TestClient dependencies not installed.")