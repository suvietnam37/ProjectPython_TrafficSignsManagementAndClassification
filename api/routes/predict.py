# api/routes/predict.py

import io
import numpy as np
import cv2
import tensorflow as tf
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import os # Import os để dùng path join
import logging # <<< Thêm logging

# --- Setup Logger cho API route ---
logger = logging.getLogger("api.predict")
# logger.setLevel(logging.DEBUG) # Bật nếu cần xem log debug

# Import cấu hình và utils
import config
try:
    from utils.model_utils import load_keras_model
    MODEL_UTILS_AVAILABLE_API = True
except ImportError:
    MODEL_UTILS_AVAILABLE_API = False
    logger.warning("utils.model_utils not found. Model loading might fail.")
    def load_keras_model(path): return None

# --- Tải Mô Hình ---
MODEL_PATH = config.MODEL_SAVE_PATH
logger.info(f"Attempting to load model from: {MODEL_PATH}")
model = load_keras_model(MODEL_PATH) if MODEL_UTILS_AVAILABLE_API else None
if model:
    logger.info(f"Model loaded successfully from {MODEL_PATH}")
elif MODEL_UTILS_AVAILABLE_API:
     logger.error(f"Failed to load model from {MODEL_PATH} using model_utils.")
else:
     logger.error(f"Cannot load model because model_utils is unavailable.")

# --- Lấy Class Names ---
CLASS_NAMES = {
    0: 'Giới hạn tốc độ (20km/h)', 1: 'Giới hạn tốc độ (30km/h)', 2: 'Giới hạn tốc độ (50km/h)',
    3: 'Giới hạn tốc độ (60km/h)', 4: 'Giới hạn tốc độ (70km/h)', 5: 'Giới hạn tốc độ (80km/h)',
    6: 'Hết giới hạn tốc độ (80km/h)', 7: 'Giới hạn tốc độ (100km/h)', 8: 'Giới hạn tốc độ (120km/h)',
    9: 'Cấm vượt (xe con)', 10: 'Cấm vượt (xe tải > 3.5 tấn)', 11: 'Giao nhau với đường không ưu tiên',
    12: 'Đường ưu tiên', 13: 'Nhường đường', 14: 'Dừng lại', 15: 'Cấm xe',
    16: 'Cấm xe tải > 3.5 tấn', 17: 'Cấm đi ngược chiều', 18: 'Nguy hiểm khác',
    19: 'Chỗ ngoặt nguy hiểm (trái)', 20: 'Chỗ ngoặt nguy hiểm (phải)', 21: 'Nhiều chỗ ngoặt nguy hiểm liên tiếp',
    22: 'Đường không bằng phẳng', 23: 'Đường trơn trượt', 24: 'Đường bị thu hẹp (phải)',
    25: 'Công trường', 26: 'Tín hiệu đèn giao thông', 27: 'Đường người đi bộ',
    28: 'Trẻ em qua đường', 29: 'Đường xe đạp', 30: 'Cẩn thận băng tuyết',
    31: 'Động vật hoang dã qua đường', 32: 'Hết mọi lệnh cấm', 33: 'Hướng đi phải rẽ phải',
    34: 'Hướng đi phải rẽ trái', 35: 'Hướng đi thẳng', 36: 'Hướng đi thẳng hoặc rẽ phải',
    37: 'Hướng đi thẳng hoặc rẽ trái', 38: 'Hướng phải đi vòng chướng ngại vật (bên phải)',
    39: 'Hướng phải đi vòng chướng ngại vật (bên trái)', 40: 'Bùng binh/Nơi giao nhau chạy theo vòng xuyến',
    41: 'Hết cấm vượt (xe con)', 42: 'Hết cấm vượt (xe tải > 3.5 tấn)'
}

# --- Khởi tạo API Router ---
router = APIRouter()

# --- Hàm Tiền xử lý Ảnh Đầu vào ---
def preprocess_single_image(image_bytes: bytes, target_height: int, target_width: int):
    """Tiền xử lý một ảnh đầu vào (bytes) để đưa vào mô hình."""
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_bgr is None: raise ValueError("Could not decode image.")

        # === (TÙY CHỌN) TIỀN XỬ LÝ NÂNG CAO (Commented out) ===
        # img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        # clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        # img_clahe = clahe.apply(img_gray)
        # img_bgr_processed = cv2.cvtColor(img_clahe, cv2.COLOR_GRAY2BGR)
        # img_to_blur = img_bgr_processed
        # img_blurred = cv2.GaussianBlur(img_to_blur, (3, 3), 0)
        # img_to_resize = img_blurred
        img_to_resize = img_bgr # Dùng ảnh gốc nếu không xử lý thêm

        # Resize ảnh
        img_resized_bgr = cv2.resize(img_to_resize, (target_width, target_height), interpolation=cv2.INTER_AREA)
        # Chuyển đổi sang RGB
        img_rgb = cv2.cvtColor(img_resized_bgr, cv2.COLOR_BGR2RGB)
        # Chuẩn hóa về [0, 1]
        img_normalized = img_rgb.astype(np.float32) / 255.0
        # Mở rộng chiều batch
        img_batch = np.expand_dims(img_normalized, axis=0)

        logger.debug(f"Preprocessed image shape: {img_batch.shape}, dtype: {img_batch.dtype}, Min: {img_batch.min():.2f}, Max: {img_batch.max():.2f}")
        return img_batch
    except Exception as e:
        logger.error(f"Error during image preprocessing: {e}", exc_info=True)
        return None

# --- Định nghĩa Endpoint Dự đoán (Cập nhật xử lý ngưỡng) ---
@router.post("/predict", response_class=JSONResponse)
async def predict_image(file: UploadFile = File(...), top_n: int = 3):
    """
    Nhận file ảnh, thực hiện dự đoán và trả về top N kết quả.
    Nếu không có kết quả nào vượt ngưỡng, trả về kết quả Top 1 với cảnh báo.
    """
    global model
    if model is None:
        logger.critical("Model is not loaded or failed to load. API cannot process predictions.")
        raise HTTPException(status_code=503, detail="Model is not loaded. Cannot process predictions.")

    contents = await file.read()
    if not contents:
        logger.warning("Received empty file upload.")
        raise HTTPException(status_code=400, detail="No image file uploaded or file is empty.")

    logger.info(f"Preprocessing uploaded image: {file.filename}")
    try:
        preprocessed_image = preprocess_single_image(contents, config.IMG_HEIGHT, config.IMG_WIDTH)
        if preprocessed_image is None:
             logger.error(f"Failed to preprocess image: {file.filename}")
             raise HTTPException(status_code=400, detail="Could not preprocess image. Check image format or content.")
        logger.info(f"Image preprocessed successfully. Shape for prediction: {preprocessed_image.shape}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error preprocessing image: {e}")

    logger.info(f"Performing prediction for image: {file.filename}")
    try:
        predictions_prob = model.predict(preprocessed_image)[0]

        log_probs = [f"{p:.4f}" for p in predictions_prob]
        logger.debug(f"Raw prediction probabilities (rounded): {log_probs}")
        top_indices_debug = np.argsort(predictions_prob)[-10:][::-1]
        top_probs_debug = predictions_prob[top_indices_debug]
        logger.debug(f"Top 10 Probabilities: {list(zip(top_indices_debug, top_probs_debug))}")

        # --- Lấy top N kết quả ---
        top_n_indices = np.argsort(predictions_prob)[-top_n:][::-1]
        top_results = []
        for idx in top_n_indices:
            class_id = int(idx)
            confidence = float(predictions_prob[idx])
            class_name = CLASS_NAMES.get(class_id, f"Unknown Class ID: {class_id}")
            top_results.append({
                "class_id": class_id,
                "class_name": class_name,
                "confidence": confidence
            })

        # --- LỌC KẾT QUẢ THEO NGƯỠNG ĐỘ TIN CẬY ---
        MIN_CONFIDENCE_THRESHOLD = 0.75 # <<< ĐẶT NGƯỠNG TẠI ĐÂY (ví dụ: 75%) >>>

        filtered_results = [res for res in top_results if res['confidence'] >= MIN_CONFIDENCE_THRESHOLD]

        # <<< THAY ĐỔI: Xử lý khi không có kết quả nào vượt ngưỡng >>>
        if not filtered_results:
            # Kiểm tra xem có dự đoán nào không (dù thấp)
            if top_results:
                # Lấy kết quả có độ tin cậy cao nhất
                top_pred_low_conf = top_results[0]
                top_conf = top_pred_low_conf['confidence']
                top_id = top_pred_low_conf['class_id']
                top_name_orig = top_pred_low_conf['class_name']

                # Tạo tên lớp mới với cảnh báo
                warning_name = f"{top_name_orig} (Độ tin cậy thấp: {top_conf:.1%})"

                # Tạo kết quả cuối cùng chỉ chứa dự đoán này
                final_results = [{"class_id": top_id,
                                  "class_name": warning_name,
                                  "confidence": top_conf}]
                logger.warning(f"No prediction passed threshold {MIN_CONFIDENCE_THRESHOLD:.2f}. Returning top result (Class {top_id}) with low confidence warning.")
            else:
                # Trường hợp rất hiếm: không có dự đoán nào từ model
                final_results = [{"class_id": -1,
                                  "class_name": "Không thể xác định",
                                  "confidence": 0.0}]
                logger.error(f"Model did not produce any predictions for {file.filename}.")
        else:
             # Sử dụng kết quả đã lọc nếu có dự đoán vượt ngưỡng
             final_results = filtered_results
             logger.info(f"Found {len(final_results)} predictions above threshold {MIN_CONFIDENCE_THRESHOLD:.2f}. Top result: Class {final_results[0]['class_id']} ({final_results[0]['confidence']:.2%})")

        # Trả về danh sách các dự đoán cuối cùng
        return JSONResponse(content={"top_predictions": final_results})

    except Exception as e:
        logger.error(f"Error during model prediction for {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error during model prediction: {e}")

# --- Endpoint Health Check ---
@router.get("/health")
async def health_check():
    """Kiểm tra trạng thái hoạt động của API và xem model đã được tải chưa."""
    global model
    model_status = "loaded" if model is not None else "not loaded"
    logger.info(f"Health check requested. Model status: {model_status}")
    return {
        "status": "API is running!",
        "model_status": model_status
    }
