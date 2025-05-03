# gui/recognition_window.py

import sys
import os
import logging
from pathlib import Path
import traceback
import requests
from typing import Optional, Dict

try:
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
        QSizePolicy, QDialog, QFileDialog, QMessageBox, QSpacerItem
    )
    from PyQt6.QtGui import QPixmap, QFont
    from PyQt6.QtCore import Qt, QSize
    PYQT6_AVAILABLE_REC = True
except ImportError:
    print("RecognitionWindow FATAL ERROR: PyQt6 not found.")
    PYQT6_AVAILABLE_REC = False
    # Không cần sys.exit() ở đây, để cửa sổ cha xử lý

logger_rec = logging.getLogger(__name__) # Logger riêng cho module này

# --- Add project root ---
current_dir_rec = Path(__file__).resolve().parent
project_root_rec = current_dir_rec.parent
if str(project_root_rec) not in sys.path:
    sys.path.insert(0, str(project_root_rec))
    logger_rec.info(f"RecognitionWindow added project root: {project_root_rec}")

# --- Import Dependencies (tương tự main_window cũ) ---
try:
    from utils.config_loader import load_settings, save_settings, DEFAULT_SETTINGS
    CONFIG_LOADER_AVAILABLE_REC = True
except ImportError: CONFIG_LOADER_AVAILABLE_REC = False; logger_rec.warning("config_loader not found.")

try:
    from database.database_manager import add_prediction_to_history
    DATABASE_AVAILABLE_REC = True
except ImportError: DATABASE_AVAILABLE_REC = False; logger_rec.warning("database_manager not found.")

try: from .upload_window import UploadWindow; UPLOAD_WINDOW_AVAILABLE_REC = True
except ImportError: UPLOAD_WINDOW_AVAILABLE_REC = False; logger_rec.warning("upload_window not found.")

try: from .result_window import ResultWindow; RESULT_WINDOW_AVAILABLE_REC = True
except ImportError: RESULT_WINDOW_AVAILABLE_REC = False; logger_rec.warning("result_window not found.")

try:
    from .ui_helpers import show_error_message, show_warning_message, show_info_message, scale_pixmap
    UI_HELPERS_AVAILABLE_REC = True
except ImportError: UI_HELPERS_AVAILABLE_REC = False; logger_rec.warning("ui_helpers not found.")

# --- Fallbacks (nếu cần) ---
if not UI_HELPERS_AVAILABLE_REC:
    # Đảm bảo QMessageBox được import nếu cần fallback
    try: from PyQt6.QtWidgets import QMessageBox
    except ImportError: pass

    def show_message(p, t, m, i):
        try: msg = QMessageBox(parent=p); msg.setIcon(i); msg.setText(m); msg.setWindowTitle(t); msg.setStandardButtons(QMessageBox.StandardButton.Ok); msg.exec()
        except NameError: print(f"Fallback Msg Error: {t} - {m}") # In ra nếu QMessageBox lỗi
    def show_error_message(p, t, m): show_message(p, t, m, QMessageBox.Icon.Critical)
    def show_warning_message(p, t, m): show_message(p, t, m, QMessageBox.Icon.Warning)
    def show_info_message(p, t, m): show_message(p, t, m, QMessageBox.Icon.Information)
    def scale_pixmap_fallback(pixmap, target_size):
        try: return pixmap.scaled(target_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation) if not pixmap.isNull() else pixmap
        except NameError: return pixmap # Trả về gốc nếu Qt cũng lỗi
    scale_pixmap_func_rec = scale_pixmap_fallback
else:
    scale_pixmap_func_rec = scale_pixmap

# --- Constants ---
# Load settings và Constants
_settings = load_settings() if CONFIG_LOADER_AVAILABLE_REC else DEFAULT_SETTINGS
API_URL_REC = _settings.get("api_url", DEFAULT_SETTINGS.get('api_url', 'http://127.0.0.1:8000/predict')) # Fallback cứng
CLASS_IMAGES_DIR_REC = Path(_settings.get("class_images_dir", DEFAULT_SETTINGS.get('class_images_dir', './gui/assets/class_images'))) # Fallback cứng
# Lấy MODEL_PATH từ config.py nếu trong settings không có hoặc rỗng
_model_path_setting = _settings.get("model_path", None)
if not _model_path_setting:
    try: import config as cfg_rec; MODEL_PATH_REC = cfg_rec.MODEL_SAVE_PATH
    except (ImportError, AttributeError): MODEL_PATH_REC = DEFAULT_SETTINGS.get('model_path')
else: MODEL_PATH_REC = _model_path_setting


class RecognitionWindow(QWidget):
    def __init__(self, current_user: Optional[Dict] = None, parent=None):
        super().__init__(parent)
        if not PYQT6_AVAILABLE_REC:
            # Xử lý lỗi nghiêm trọng nếu PyQt6 không có
            try:
                 app_err = QApplication.instance() or QApplication(sys.argv)
                 QMessageBox.critical(None, "Lỗi nghiêm trọng", "PyQt6 không khả dụng. Không thể chạy cửa sổ nhận diện.")
            except Exception: print("Cannot show critical error for missing PyQt6 in RecognitionWindow")
            # Không nên tiếp tục nếu thiếu thư viện cơ bản
            # self.close() # Đóng nếu được tạo
            raise ImportError("PyQt6 is required for RecognitionWindow but not found.")


        self.current_image_path: Optional[str] = None
        self.current_user = current_user if current_user else {}
        self.setWindowTitle("Chức Năng Nhận Diện Biển Báo")
        self.setGeometry(250, 250, 650, 480) # Điều chỉnh kích thước nếu cần
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Layout hàng trên cùng (ảnh và nút)
        top_layout = QHBoxLayout()
        main_layout.addLayout(top_layout)

        # --- Cột trái: Hiển thị ảnh ---
        image_layout = QVBoxLayout(); image_layout.setSpacing(5)
        self.image_label = QLabel("Kéo/Thả ảnh hoặc nhấn 'Tải Ảnh Lên'")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.image_label.setMinimumSize(400, 350)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding); self.image_label.setStyleSheet("QLabel { border: 2px dashed #aaa; background-color: #f8f8f8; color: #555; font-size: 11pt; }")
        self.setAcceptDrops(True); self.image_label.setAcceptDrops(True)
        self.image_label.dragEnterEvent = self.dragEnterEvent; self.image_label.dragMoveEvent = self.dragMoveEvent; self.image_label.dropEvent = self.dropEvent
        image_layout.addWidget(self.image_label)

        # Nút xóa ảnh dưới ảnh
        self.clear_image_button = QPushButton("Xóa Ảnh Hiện Tại"); self.clear_image_button.setToolTip("Gỡ bỏ ảnh đang hiển thị"); self.clear_image_button.setEnabled(False); self.clear_image_button.clicked.connect(self.clear_image); image_layout.addWidget(self.clear_image_button)
        top_layout.addLayout(image_layout, 3) # Ảnh chiếm nhiều không gian hơn

        # --- Cột phải: Các nút điều khiển ---
        action_layout = QVBoxLayout(); action_layout.setAlignment(Qt.AlignmentFlag.AlignTop); action_layout.setSpacing(15); top_layout.addLayout(action_layout, 1)
        button_font = QFont(); button_font.setPointSize(11) # Font to hơn chút

        self.load_button = QPushButton(' Tải Ảnh Lên'); self.load_button.setFont(button_font); self.load_button.setToolTip("Chọn ảnh từ máy tính"); self.load_button.clicked.connect(self.load_image); action_layout.addWidget(self.load_button)
        self.predict_button = QPushButton(' Bắt đầu Nhận Diện'); self.predict_button.setFont(button_font); self.predict_button.setEnabled(False); self.predict_button.setToolTip("Gửi ảnh để nhận diện biển báo"); self.predict_button.clicked.connect(self.predict_image); action_layout.addWidget(self.predict_button)

        action_layout.addStretch(1) # Đẩy nút đóng xuống dưới

        self.close_button = QPushButton("Đóng Chức Năng Này")
        self.close_button.setFont(button_font)
        self.close_button.clicked.connect(self.close) # Đóng chỉ cửa sổ này
        action_layout.addWidget(self.close_button)

    # --- Copy các hàm xử lý từ main_window.py cũ ---
    # dragEnterEvent, dragMoveEvent, dropEvent
    # set_image_path, clear_image, load_image, _fallback_load_image
    # predict_image
    # set_buttons_enabled (chỉ điều khiển load/predict/clear)
    # --- Lưu ý: Cần sửa đổi các hàm này để dùng logger_rec, scale_pixmap_func_rec, API_URL_REC, etc.

    # Ví dụ sửa đổi set_buttons_enabled:
    def set_buttons_enabled(self, enabled: bool):
        """Kích hoạt hoặc vô hiệu hóa các nút chức năng nhận diện."""
        self.load_button.setEnabled(enabled)
        has_image = bool(self.current_image_path)
        self.predict_button.setEnabled(enabled and has_image)
        self.clear_image_button.setEnabled(enabled and has_image)
        # Không còn các nút khác ở đây


    # --- Drag & Drop Events ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
        else: event.ignore()
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
        else: event.ignore()
    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                valid_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.ppm']
                file_path_obj = Path(file_path)
                if file_path_obj.is_file() and file_path_obj.suffix.lower() in valid_extensions:
                    self.set_image_path(file_path)
                    event.acceptProposedAction()
                else:
                    show_warning_message(self, "Loại File Không Hợp Lệ", f"Chỉ chấp nhận file ảnh ({', '.join(valid_extensions)}).\nFile của bạn: {file_path_obj.suffix}")
                    event.ignore()
            else: event.ignore()
        else: event.ignore()

    # --- Image Handling ---
    def set_image_path(self, file_path: Optional[str]):
        if file_path and Path(file_path).is_file():
            self.current_image_path = file_path
            logger_rec.info(f"Ảnh được chọn: {self.current_image_path}")
            if CONFIG_LOADER_AVAILABLE_REC:
                try:
                    settings_data = load_settings(); settings_data['last_image_dir'] = str(Path(file_path).parent); save_settings(settings_data)
                except Exception as e: logger_rec.warning(f"Không thể lưu thư mục ảnh cuối: {e}")

            pixmap_orig = QPixmap(self.current_image_path)
            if not pixmap_orig.isNull():
                # Sử dụng hàm scale đã được gán (hoặc fallback)
                scaled_pixmap = scale_pixmap_func_rec(pixmap_orig, self.image_label.size())
                self.image_label.setPixmap(scaled_pixmap)
                self.image_label.setText("")
                self.image_label.setStyleSheet("border: 1px solid green;")
                self.set_buttons_enabled(True) # Bật lại các nút liên quan đến ảnh
            else:
                show_error_message(self, "Lỗi Ảnh", f"Không thể đọc hoặc hiển thị file ảnh:\n{file_path}")
                self.clear_image()
        elif file_path:
            show_error_message(self, "Lỗi Đường Dẫn", f"Đường dẫn file không hợp lệ hoặc không tồn tại:\n{file_path}")
            self.clear_image()

    def clear_image(self):
        self.current_image_path = None
        self.image_label.clear(); self.image_label.setText("Kéo/Thả ảnh hoặc nhấn 'Tải Ảnh Lên'")
        self.image_label.setStyleSheet("QLabel { border: 2px dashed #aaa; background-color: #f8f8f8; color: #555; font-size: 11pt; }")
        self.set_buttons_enabled(True) # Cho phép tải ảnh mới
        self.predict_button.setEnabled(False) # Tắt nhận diện
        self.clear_image_button.setEnabled(False) # Tắt xóa
        logger_rec.info("Image cleared from display.")

    def load_image(self):
        last_dir = str(Path.home())
        if CONFIG_LOADER_AVAILABLE_REC:
            try: settings_data = load_settings(); last_dir = settings_data.get("last_image_dir", last_dir)
            except Exception as e: logger_rec.warning(f"Could not load last_image_dir setting: {e}")

        if UPLOAD_WINDOW_AVAILABLE_REC:
            try:
                upload_dialog = UploadWindow(parent=self, start_dir=last_dir)
                if upload_dialog.exec() == QDialog.DialogCode.Accepted: self.set_image_path(upload_dialog.getSelectedFilePath())
                else: logger_rec.info("Việc chọn ảnh đã bị hủy (UploadWindow).")
            except Exception as e: logger_rec.error(f"Error opening UploadWindow: {e}", exc_info=True); self._fallback_load_image(last_dir)
        else: self._fallback_load_image(last_dir)

    def _fallback_load_image(self, start_dir):
         logger_rec.info("Using QFileDialog fallback for image selection.")
         file_path_fb, _ = QFileDialog.getOpenFileName(self, "Chọn Ảnh Biển Báo", start_dir, "Image Files (*.png *.jpg *.jpeg *.bmp *.ppm)")
         if file_path_fb: self.set_image_path(file_path_fb)
         else: logger_rec.info("Việc chọn ảnh đã bị hủy (QFileDialog).")

    # --- Prediction ---
    def predict_image(self):
        if not self.current_image_path:
            show_warning_message(self, "Chưa chọn ảnh", "Vui lòng tải hoặc kéo thả ảnh vào trước khi nhận diện.")
            return

        # Lấy lại settings mới nhất phòng trường hợp đã thay đổi
        current_settings = load_settings() if CONFIG_LOADER_AVAILABLE_REC else DEFAULT_SETTINGS
        api_url = current_settings.get("api_url", API_URL_REC) # Dùng biến toàn cục của module làm fallback
        class_images_dir = Path(current_settings.get("class_images_dir", CLASS_IMAGES_DIR_REC))
        top_n_results = 3

        self.set_buttons_enabled(False); QApplication.processEvents()

        top_predictions_list = []; error_detail = None; image_bytes_content = None
        try:
            logger_rec.info(f"Reading image file: {self.current_image_path}")
            with open(self.current_image_path, 'rb') as f_read: image_bytes_content = f_read.read()
            if not image_bytes_content: raise ValueError("Image file empty.")

            files = {'file': (Path(self.current_image_path).name, image_bytes_content, 'image/jpeg')} # Giả định mime type
            params = {'top_n': top_n_results}
            logger_rec.info(f"Sending prediction request to API: {api_url} with top_n={top_n_results}")
            response = requests.post(api_url, files=files, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()
            logger_rec.debug(f"API Response JSON: {result}")

            if "top_predictions" in result and isinstance(result["top_predictions"], list) and result["top_predictions"]:
                top_predictions_list = result["top_predictions"]
                first_pred = top_predictions_list[0]
                # Kiểm tra key cần thiết
                if not all(key in first_pred for key in ["class_id", "class_name", "confidence"]):
                    error_detail = f"API response format error (missing keys): {top_predictions_list}"; logger_rec.error(error_detail); top_predictions_list = []
                else: logger_rec.info(f"Prediction successful: Received {len(top_predictions_list)} Top-N results.")
            else: error_detail = f"API did not return valid 'top_predictions' list. Response: {result}"; logger_rec.error(error_detail)

        except FileNotFoundError: error_detail = f"Error: Image file not found at:\n{self.current_image_path}"; logger_rec.error(error_detail)
        except ValueError as ve: error_detail = f"Error reading image file: {ve}"; logger_rec.error(error_detail)
        except requests.exceptions.ConnectionError: error_detail = f"API Connection Error:\nCould not connect to {api_url}\nPlease check if the API server is running and the URL in Settings is correct."; logger_rec.error(error_detail)
        except requests.exceptions.Timeout: error_detail = f"API Timeout Error:\nRequest to {api_url} timed out."; logger_rec.error(error_detail)
        except requests.exceptions.RequestException as e: # Lỗi request chung
            error_detail = f"API Request Error: {e}"
            status_code = 'N/A'
            api_error = str(e)
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                try: api_error = e.response.json().get('detail', e.response.text)
                except ValueError: api_error = e.response.text
            error_detail += f"\n\nAPI Error Details (Status: {status_code}):\n{api_error}"
            logger_rec.error(error_detail, exc_info=True) # Log traceback
        except Exception as e: # Lỗi không mong muốn khác
            error_detail = f"An unexpected error occurred during prediction:\n{e}"; logger_rec.error(error_detail, exc_info=True)

        finally:
            self.set_buttons_enabled(True); QApplication.processEvents() # Kích hoạt lại nút
            # Xử lý hiển thị kết quả hoặc lỗi
            if top_predictions_list:
                top1_pred = top_predictions_list[0]
                # Ưu tiên hiển thị ResultWindow nếu có
                if RESULT_WINDOW_AVAILABLE_REC:
                    try:
                        result_dialog = ResultWindow(
                            top_predictions=top_predictions_list,
                            input_image_path=self.current_image_path,
                            class_images_dir=str(class_images_dir), # Cần chuyển Path thành str
                            parent=self )
                        result_dialog.exec() # Hiển thị dialog modal
                    except Exception as e_res: # Nếu lỗi mở cửa sổ chi tiết
                        show_error_message(self,"Lỗi Hiển Thị Kết Quả", f"Lỗi mở cửa sổ kết quả chi tiết:\n{e_res}")
                        logger_rec.error("Error opening ResultWindow", exc_info=True)
                        # Hiển thị fallback đơn giản
                        show_info_message(self, "Kết Quả (Top 1)", f"Dự đoán: {top1_pred['class_name']}\nĐộ tin cậy: {top1_pred['confidence']:.2%}")
                else: # Nếu ResultWindow không có
                    show_info_message(self, "Kết Quả (Top 1)", f"Dự đoán: {top1_pred['class_name']}\nĐộ tin cậy: {top1_pred['confidence']:.2%}")

                # Lưu vào lịch sử database
                if DATABASE_AVAILABLE_REC:
                    try:
                        success_db = add_prediction_to_history(
                            image_path=self.current_image_path,
                            predicted_class_id=top1_pred['class_id'],
                            predicted_class_name=top1_pred['class_name'],
                            confidence=top1_pred['confidence'] )
                        if not success_db: logger_rec.warning("Failed to add prediction to history database (returned False).")
                    except Exception as db_err:
                        show_error_message(self, "Lỗi Cơ Sở Dữ Liệu", f"Không thể lưu kết quả vào lịch sử:\n{db_err}")
                        logger_rec.error("Error saving prediction to DB", exc_info=True)

            elif error_detail: # Nếu có lỗi xảy ra trong quá trình gọi API
                show_error_message(self, "Lỗi Nhận Diện", error_detail)
            # Không làm gì nếu không có lỗi và cũng không có kết quả (trường hợp hiếm)


# --- Test Block ---
if __name__ == '__main__':
    # Cần QApplication để chạy widget
    app_test = QApplication(sys.argv)
    # Tạo user giả để test nếu cần
    fake_user = {'id': 1, 'username': 'test_rec', 'role': 'user'}
    try:
         rec_window = RecognitionWindow(current_user=fake_user)
         rec_window.show()
         sys.exit(app_test.exec())
    except ImportError as e:
         print(f"Could not run RecognitionWindow test due to missing dependency: {e}")
         sys.exit(1)