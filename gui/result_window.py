# gui/result_window.py

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QDialogButtonBox, QGroupBox, QScrollArea, QWidget as QBaseWidget # Đổi tên QWidget
)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt, QSize

# --- Thêm thư mục gốc ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path: sys.path.insert(0, project_root)

# Import helper để scale ảnh
try: from .ui_helpers import scale_pixmap; UI_HELPERS_AVAILABLE_RESULT = True
except ImportError: UI_HELPERS_AVAILABLE_RESULT = False; print("Warning: ui_helpers not found.")
def scale_pixmap_fallback(pixmap, target_size): return pixmap.scaled(target_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation) if not pixmap.isNull() else pixmap
scale_pixmap_func = scale_pixmap if UI_HELPERS_AVAILABLE_RESULT else scale_pixmap_fallback


class ResultWindow(QDialog):
    """Dialog hiển thị kết quả nhận diện (bao gồm Top-N)."""
    def __init__(self, top_predictions: list, input_image_path: str, class_images_dir: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kết Quả Nhận Diện Chi Tiết")
        self.setMinimumSize(550, 450)

        if not top_predictions:
             print("Error: Received empty top_predictions list.")
             self.top_prediction = None; self.other_predictions = []
        else:
            self.top_prediction = top_predictions[0]; self.other_predictions = top_predictions[1:]

        self.input_image_path = input_image_path
        self.class_images_dir = class_images_dir

        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(); self.setLayout(main_layout)

        if self.top_prediction:
            top_class_name = self.top_prediction['class_name']; top_confidence = self.top_prediction['confidence']
            top_class_id = self.top_prediction['class_id']

            self.result_text_label = QLabel(f"Kết quả chính: <b>{top_class_name}</b>"); self.result_text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            font = self.result_text_label.font(); font.setPointSize(14); font.setBold(True); self.result_text_label.setFont(font)
            main_layout.addWidget(self.result_text_label)

            self.confidence_label = QLabel(f"Độ tin cậy: {top_confidence:.2%}"); self.confidence_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            font_conf = self.confidence_label.font(); font_conf.setPointSize(11); self.confidence_label.setFont(font_conf)
            main_layout.addWidget(self.confidence_label)

            image_layout = QHBoxLayout(); image_layout.setContentsMargins(10, 5, 10, 5); main_layout.addLayout(image_layout)
            fixed_image_size = QSize(180, 180)

            input_group_layout = QVBoxLayout(); input_title = QLabel("Ảnh Đầu Vào:"); input_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.input_image_display = QLabel("..."); self.input_image_display.setAlignment(Qt.AlignmentFlag.AlignCenter); self.input_image_display.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
            self.input_image_display.setFixedSize(fixed_image_size); self.input_image_display.setStyleSheet("border: 1px solid #ccc; background-color: #eee;")
            pixmap_input = QPixmap(self.input_image_path);
            if not pixmap_input.isNull(): self.input_image_display.setPixmap(scale_pixmap_func(pixmap_input, fixed_image_size)); self.input_image_display.setText("")
            else: self.input_image_display.setText("Lỗi tải ảnh\nđầu vào"); print(f"ResultWindow - Failed load input: {self.input_image_path}")
            input_group_layout.addWidget(input_title); input_group_layout.addWidget(self.input_image_display); input_group_layout.addStretch(); image_layout.addLayout(input_group_layout)

            sample_group_layout = QVBoxLayout(); sample_title = QLabel("Ảnh Mẫu (Dự đoán Top 1):"); sample_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.sample_image_display = QLabel("..."); self.sample_image_display.setAlignment(Qt.AlignmentFlag.AlignCenter); self.sample_image_display.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
            self.sample_image_display.setFixedSize(fixed_image_size); self.sample_image_display.setStyleSheet("border: 1px solid green; background-color: #eee;")
            sample_image_path = os.path.join(self.class_images_dir, f"{top_class_id}.png")
            pixmap_sample = QPixmap(sample_image_path)
            if not pixmap_sample.isNull(): self.sample_image_display.setPixmap(scale_pixmap_func(pixmap_sample, fixed_image_size)); self.sample_image_display.setText("")
            else: self.sample_image_display.setText("Không tìm thấy\nảnh mẫu"); self.sample_image_display.setStyleSheet("border: 1px dashed red;"); print(f"ResultWindow - Failed load sample: {sample_image_path}")
            sample_group_layout.addWidget(sample_title); sample_group_layout.addWidget(self.sample_image_display); sample_group_layout.addStretch(); image_layout.addLayout(sample_group_layout)
        else:
            error_label = QLabel("Không nhận được kết quả dự đoán hợp lệ."); error_label.setAlignment(Qt.AlignmentFlag.AlignCenter); main_layout.addWidget(error_label)

        if self.other_predictions:
            others_group = QGroupBox("Các dự đoán có khả năng khác:"); others_layout = QVBoxLayout(); others_group.setLayout(others_layout)
            scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True); scroll_content = QBaseWidget(); scroll_layout = QVBoxLayout(scroll_content)
            for i, pred in enumerate(self.other_predictions):
                other_label = QLabel(f"{i+2}. {pred['class_name']} ({pred['confidence']:.2%})")
                scroll_layout.addWidget(other_label)
            scroll_layout.addStretch(); scroll_area.setWidget(scroll_content); scroll_area.setFixedHeight(80) # Giới hạn chiều cao
            others_layout.addWidget(scroll_area); main_layout.addWidget(others_group)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok); button_box.accepted.connect(self.accept); main_layout.addWidget(button_box)

# --- Chạy thử dialog ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    try: import config as cfg_test; CLASS_IMAGES_DIR_TEST = cfg_test.CLASS_IMAGES_DIR
    except: CLASS_IMAGES_DIR_TEST = "../gui/assets/class_images"
    dummy_top_predictions = [
        {"class_id": 14, "class_name": "Dừng lại", "confidence": 0.7234}, {"class_id": 17, "class_name": "Cấm đi ngược chiều", "confidence": 0.2100},
        {"class_id": 1, "class_name": "Giới hạn tốc độ (30km/h)", "confidence": 0.05} ]
    dummy_input_path = "../tests/test_data/sample_sign.png"
    if not os.path.exists(dummy_input_path): print(f"Warning: Dummy input image not found: {dummy_input_path}")
    dialog = ResultWindow(top_predictions=dummy_top_predictions, input_image_path=dummy_input_path, class_images_dir=CLASS_IMAGES_DIR_TEST)
    dialog.exec()