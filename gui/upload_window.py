# gui/upload_window.py

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt
# --- THÊM DÒNG NÀY ---
from typing import Union, Optional # Có thể dùng Optional[str] thay cho Union[str, None] cũng được

# --- Thêm thư mục gốc vào sys.path ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import helpers nếu cần (ví dụ: lưu đường dẫn cuối cùng)
# from .ui_helpers import ...
# from utils.config_loader import load_settings, save_settings # Ví dụ

class UploadWindow(QDialog):
    """
    Dialog đơn giản để người dùng chọn một file ảnh.
    Trả về đường dẫn file đã chọn khi người dùng nhấn OK.
    """
    def __init__(self, parent=None, start_dir=""):
        super().__init__(parent)
        self.setWindowTitle("Chọn Ảnh Để Nhận Diện")
        self.setMinimumWidth(400)
        self.selected_file_path: Optional[str] = None # Lưu đường dẫn đã chọn, dùng Optional cũng được
        self.start_directory: str = start_dir # Thư mục bắt đầu cho dialog

        # --- Layout chính ---
        layout = QVBoxLayout()
        self.setLayout(layout)

        # --- Phần chọn file ---
        file_layout = QHBoxLayout()
        layout.addLayout(file_layout)

        self.file_path_label = QLabel("Đường dẫn ảnh:")
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True) # Chỉ hiển thị
        self.browse_button = QPushButton("Duyệt...")
        self.browse_button.clicked.connect(self.browseFile)

        file_layout.addWidget(self.file_path_label)
        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(self.browse_button)

        # --- Nút OK / Cancel ---
        # Sử dụng QDialogButtonBox cho các nút chuẩn
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept) # Kết nối tín hiệu accepted với self.accept
        button_box.rejected.connect(self.reject) # Kết nối tín hiệu rejected với self.reject
        layout.addWidget(button_box)

        # Vô hiệu hóa nút OK ban đầu cho đến khi có file được chọn
        self.updateOkButtonState()

    def browseFile(self):
        """Mở QFileDialog để chọn ảnh."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Chọn Ảnh Biển Báo",
            self.start_directory, # Bắt đầu từ thư mục cuối cùng (nếu có)
            "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.file_path_edit.setText(file_path)
            self.selected_file_path = file_path
            # Cập nhật thư mục bắt đầu cho lần sau
            self.start_directory = os.path.dirname(file_path)
        # Cập nhật trạng thái nút OK sau khi chọn (hoặc không chọn)
        self.updateOkButtonState()

    def updateOkButtonState(self):
        """Kích hoạt hoặc vô hiệu hóa nút OK dựa trên việc đã chọn file chưa."""
        button_box = self.findChild(QDialogButtonBox)
        if button_box:
            ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
            if ok_button:
                ok_button.setEnabled(bool(self.selected_file_path))

    # --- ĐÃ SỬA LỖI CÚ PHÁP TYPE HINT Ở ĐÂY ---
    # Sử dụng Union[str, None] hoặc Optional[str] đều được
    def getSelectedFilePath(self) -> Union[str, None]:
    # Hoặc: def getSelectedFilePath(self) -> Optional[str]:
        """Trả về đường dẫn file đã được chọn."""
        # Phương thức này được gọi sau khi dialog được chấp nhận (accept)
        return self.selected_file_path

    # Có thể ghi đè accept để kiểm tra lần cuối, nhưng không bắt buộc vì nút OK đã bị vô hiệu hóa
    # def accept(self):
    #     if self.selected_file_path:
    #         super().accept()


# --- Chạy thử dialog ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Lấy thư mục cuối cùng từ settings nếu có
    last_dir = ""
    # Ví dụ lấy thư mục hiện tại nếu không có gì khác
    # last_dir = os.getcwd()
    # try:
    #     from utils.config_loader import load_settings
    #     settings = load_settings()
    #     last_dir = settings.get("last_image_dir", os.getcwd()) # Lấy thư mục làm việc nếu không có
    # except ImportError:
    #     pass

    dialog = UploadWindow(start_dir=last_dir)
    # Hiển thị dialog và chờ người dùng tương tác
    if dialog.exec() == QDialog.DialogCode.Accepted:
        selected_path = dialog.getSelectedFilePath()
        print(f"File đã chọn: {selected_path}")
        # Lưu lại thư mục cuối cùng nếu muốn
        # try:
        #     from utils.config_loader import load_settings, save_settings
        #     if selected_path: # Chỉ lưu nếu có đường dẫn hợp lệ
        #         settings = load_settings()
        #         settings['last_image_dir'] = os.path.dirname(selected_path)
        #         save_settings(settings)
        # except ImportError:
        #     pass
        # except Exception as e:
        #      print(f"Warning: Could not save last directory. Error: {e}")
    else:
        print("Hủy chọn file.")

    # Kết thúc ứng dụng nếu login bị hủy
    sys.exit(0) # Thoát sau khi dialog đóng