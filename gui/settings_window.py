# gui/settings_window.py

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFileDialog, QGroupBox # Thêm QGroupBox
)
from PyQt6.QtCore import Qt

# --- Thêm thư mục gốc vào sys.path ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Import trình quản lý cấu hình ---
try:
    from utils.config_loader import load_settings, save_settings, DEFAULT_SETTINGS
    CONFIG_LOADER_AVAILABLE = True
except ImportError as e:
    print(f"SettingsWindow Error: Could not import config_loader. Settings cannot be managed. Error: {e}")
    CONFIG_LOADER_AVAILABLE = False
except Exception as e:
    print(f"SettingsWindow Error: Unexpected error importing config_loader. Error: {e}")
    CONFIG_LOADER_AVAILABLE = False


class SettingsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Đặt thuộc tính để cửa sổ này là modal (khóa cửa sổ cha khi mở)
        # self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle('Cài Đặt Ứng Dụng')
        self.setMinimumWidth(450) # Đặt chiều rộng tối thiểu
        self.initUI()
        # Tải cài đặt hiện tại khi mở cửa sổ
        self.loadCurrentSettings()

    def initUI(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # --- Nhóm Cài đặt API ---
        api_groupbox = QGroupBox("Cài đặt API")
        api_layout = QVBoxLayout()
        api_groupbox.setLayout(api_layout)
        main_layout.addWidget(api_groupbox)

        api_url_layout = QHBoxLayout()
        api_url_label = QLabel("URL Endpoint Dự Đoán:")
        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("Ví dụ: http://127.0.0.1:8000/predict")
        api_url_layout.addWidget(api_url_label)
        api_url_layout.addWidget(self.api_url_input)
        api_layout.addLayout(api_url_layout)

        # --- Nhóm Cài đặt Giao diện ---
        ui_groupbox = QGroupBox("Cài đặt Giao diện")
        ui_layout = QVBoxLayout()
        ui_groupbox.setLayout(ui_layout)
        main_layout.addWidget(ui_groupbox)

        img_dir_layout = QHBoxLayout()
        img_dir_label = QLabel("Thư mục Ảnh Mẫu:")
        self.img_dir_input = QLineEdit()
        self.img_dir_input.setReadOnly(True) # Chỉ hiển thị, chọn bằng nút
        img_dir_browse_button = QPushButton("Chọn...")
        img_dir_browse_button.clicked.connect(self.browseImageDirectory)
        img_dir_layout.addWidget(img_dir_label)
        img_dir_layout.addWidget(self.img_dir_input)
        img_dir_layout.addWidget(img_dir_browse_button)
        ui_layout.addLayout(img_dir_layout)

        # --- Nhóm Cài đặt Database (Ví dụ) ---
        # db_groupbox = QGroupBox("Cài đặt Database")
        # ... (Tương tự, thêm QLineEdit và nút Browse cho database_path) ...
        # main_layout.addWidget(db_groupbox)


        # --- Các Nút Điều Khiển ---
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        save_button = QPushButton("Lưu Cài Đặt")
        save_button.clicked.connect(self.saveCurrentSettings)
        button_layout.addWidget(save_button)

        reset_button = QPushButton("Đặt lại Mặc Định")
        reset_button.clicked.connect(self.resetToDefaults)
        button_layout.addWidget(reset_button)

        close_button = QPushButton("Đóng")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        # Vô hiệu hóa nếu không load được config_loader
        if not CONFIG_LOADER_AVAILABLE:
            api_groupbox.setEnabled(False)
            ui_groupbox.setEnabled(False)
            save_button.setEnabled(False)
            reset_button.setEnabled(False)
            QMessageBox.critical(self, "Lỗi", "Không thể tải trình quản lý cấu hình.\nCửa sổ cài đặt sẽ bị vô hiệu hóa.")


    def loadCurrentSettings(self):
        """Tải cài đặt từ file và hiển thị lên giao diện."""
        if not CONFIG_LOADER_AVAILABLE: return

        settings = load_settings()
        self.api_url_input.setText(settings.get('api_url', ''))
        self.img_dir_input.setText(settings.get('class_images_dir', ''))
        # self.db_path_input.setText(settings.get('database_path', '')) # Nếu có ô nhập DB path

    def browseImageDirectory(self):
        """Mở hộp thoại chọn thư mục cho ảnh mẫu."""
        current_dir = self.img_dir_input.text() # Lấy đường dẫn hiện tại làm điểm bắt đầu
        directory = QFileDialog.getExistingDirectory(self, "Chọn Thư Mục Chứa Ảnh Mẫu", current_dir)
        if directory: # Nếu người dùng chọn một thư mục
            self.img_dir_input.setText(directory)

    # def browseDatabaseFile(self):
    #     """Mở hộp thoại chọn file database."""
    #     # ... (Tương tự dùng QFileDialog.getSaveFileName hoặc getOpenFileName) ...

    def saveCurrentSettings(self):
        """Lấy giá trị từ input và lưu vào file settings.json."""
        if not CONFIG_LOADER_AVAILABLE: return

        new_settings = {
            "api_url": self.api_url_input.text().strip(), # Lấy text và xóa khoảng trắng thừa
            "class_images_dir": self.img_dir_input.text().strip(),
            # "database_path": self.db_path_input.text().strip(), # Nếu có
        }

        # (Tùy chọn) Validate dữ liệu nhập vào (ví dụ: URL có hợp lệ không?)

        if save_settings(new_settings):
            QMessageBox.information(self, "Thành công", "Cài đặt đã được lưu thành công.\nMột số thay đổi có thể cần khởi động lại ứng dụng.")
            # Tùy chọn: Phát tín hiệu để MainWindow biết cần tải lại cài đặt
            self.close() # Đóng cửa sổ sau khi lưu
        else:
            QMessageBox.critical(self, "Lỗi", "Không thể lưu cài đặt.")

    def resetToDefaults(self):
        """Đặt lại các ô nhập liệu về giá trị mặc định."""
        if not CONFIG_LOADER_AVAILABLE: return

        reply = QMessageBox.question(self, 'Xác nhận',
                                     "Bạn có chắc muốn đặt lại tất cả cài đặt về mặc định không?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.api_url_input.setText(DEFAULT_SETTINGS.get('api_url', ''))
            self.img_dir_input.setText(DEFAULT_SETTINGS.get('class_images_dir', ''))
            # self.db_path_input.setText(DEFAULT_SETTINGS.get('database_path', ''))
            # Có thể lưu luôn cài đặt mặc định vào file ở đây nếu muốn
            # save_settings(DEFAULT_SETTINGS)


# --- Chạy cửa sổ độc lập để test ---
if __name__ == '__main__':
    if not CONFIG_LOADER_AVAILABLE:
        print("Cannot run SettingsWindow standalone: config_loader not available.")
        app_test = QApplication(sys.argv)
        QMessageBox.critical(None, "Lỗi", "Không thể import config_loader.\nKhông thể chạy cửa sổ cài đặt.")
        sys.exit(1)

    app = QApplication(sys.argv)
    settings_win = SettingsWindow()
    settings_win.show()
    sys.exit(app.exec())