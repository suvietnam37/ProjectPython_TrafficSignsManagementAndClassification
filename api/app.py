# api/app.py

from fastapi import FastAPI
import uvicorn
import sys
import os

# --- Thêm thư mục gốc vào sys.path để import các module khác ---
# Cách này thường dùng khi chạy `python api/app.py` trực tiếp
# Nếu chạy bằng `uvicorn api.app:app`, nó thường tự tìm được, nhưng thêm vào cho chắc chắn
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) # Đi lên 1 cấp từ api/ -> thư mục gốc
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added project root to sys.path: {project_root}")

# --- Import router từ file predict.py ---
# Đảm bảo rằng việc import này không gây lỗi (ví dụ: lỗi load model trong predict.py)
try:
    from api.routes import predict # Import module predict từ thư mục routes
    print("Successfully imported predict router.")
except ImportError as e:
    print(f"ERROR: Could not import predict router. Check imports or errors in api/routes/predict.py")
    print(f"ImportError: {e}")
    # Thoát nếu không import được router chính
    sys.exit(1)
except FileNotFoundError as e:
    # Bắt lỗi FileNotFoundError nếu model không tìm thấy khi predict.py được import
    print(f"ERROR during initial import: {e}")
    print("Please ensure the model file exists at the configured path before starting the API.")
    sys.exit(1)
except Exception as e:
     # Bắt các lỗi khác có thể xảy ra khi predict.py được import (ví dụ lỗi tensorflow)
     print(f"ERROR: An unexpected error occurred during initial import of predict.py: {e}")
     sys.exit(1)


# --- Khởi tạo ứng dụng FastAPI ---
app = FastAPI(
    title="GTSRB Sign Recognition API",
    description="API to predict German Traffic Sign Recognition Benchmark classes from images.",
    version="1.0.0"
)

# --- Gắn (Include) Router ---
# Thêm tất cả các routes (endpoints) từ module predict vào ứng dụng chính
# Có thể thêm prefix nếu muốn, ví dụ prefix="/api/v1"
app.include_router(predict.router)
print("Predict router included in FastAPI app.")

# --- Định nghĩa route gốc (tùy chọn) ---
@app.get("/")
async def read_root():
    """Cung cấp một endpoint gốc đơn giản."""
    return {"message": "Welcome to the GTSRB Sign Recognition API. Go to /docs for documentation."}

# --- Điểm khởi chạy khi chạy file này trực tiếp (chủ yếu để debug) ---
# Cách chạy chuẩn thường là dùng uvicorn từ command line:
# uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    print("Attempting to run application directly using uvicorn...")
    # Cấu hình host và port ở đây hoặc dùng giá trị mặc định
    # host="127.0.0.1" (chỉ truy cập từ local) hoặc "0.0.0.0" (truy cập từ network)
    # port=8000 (cổng mặc định)
    uvicorn.run(app, host="127.0.0.1", port=8000)
    # Lưu ý: Khi chạy kiểu này, reload thường không hoạt động hiệu quả bằng chạy từ command line.