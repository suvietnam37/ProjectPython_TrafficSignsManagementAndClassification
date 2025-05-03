# gui/login_window.py
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QDialogButtonBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from typing import Optional, Dict

# --- Thêm thư mục gốc ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Import auth_manager từ utils ---
try:
    from utils import auth_manager # <<< Đã sửa đường dẫn import
    AUTH_MANAGER_AVAILABLE = True
except ImportError:
    print("LoginWindow FATAL ERROR: utils.auth_manager not found or error importing.")
    AUTH_MANAGER_AVAILABLE = False

# --- Import ui_helpers ---
try:
    from .ui_helpers import show_error_message
except ImportError:
    # Fallback nếu không import được ui_helpers
    def show_error_message(parent, title, message):
        QMessageBox.critical(parent, title, message)

class LoginWindow(QDialog):
    """Dialog đăng nhập."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Đăng Nhập Hệ Thống")
        self.setModal(True)
        self.setMinimumWidth(350)
        self.logged_in_user_info: Optional[Dict] = None
        self.initUI()

        if not AUTH_MANAGER_AVAILABLE:
             show_error_message(self, "Lỗi Hệ Thống", "Không thể tải module xác thực người dùng.\nChức năng đăng nhập không khả dụng.")
             try: # Vô hiệu hóa input nếu lỗi
                 self.username_input.setEnabled(False)
                 self.password_input.setEnabled(False)
                 ok_button = self.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Ok)
                 if ok_button: ok_button.setEnabled(False)
             except Exception as e: print(f"Error disabling widgets: {e}")

    def initUI(self):
        """Khởi tạo giao diện người dùng cho cửa sổ đăng nhập."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # --- Form đăng nhập ---
        form_layout = QVBoxLayout(); form_layout.setSpacing(10)
        # Username
        user_layout = QHBoxLayout(); user_label = QLabel("Tên đăng nhập:")
        self.username_input = QLineEdit(); self.username_input.setPlaceholderText("Nhập tên đăng nhập")
        user_layout.addWidget(user_label); user_layout.addWidget(self.username_input); form_layout.addLayout(user_layout)
        # Password
        pass_layout = QHBoxLayout(); pass_label = QLabel("Mật khẩu:")
        self.password_input = QLineEdit(); self.password_input.setPlaceholderText("Nhập mật khẩu")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        pass_layout.addWidget(pass_label); pass_layout.addWidget(self.password_input); form_layout.addLayout(pass_layout)

        layout.addLayout(form_layout) # Thêm form vào layout chính
        # Thêm khoảng trống phía trên nút bấm nếu muốn
        layout.addSpacerItem(QSpacerItem(20, 15, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # --- Nút Đăng nhập / Thoát ---
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        login_button = button_box.button(QDialogButtonBox.StandardButton.Ok); login_button.setText("Đăng Nhập")
        cancel_button = button_box.button(QDialogButtonBox.StandardButton.Cancel); cancel_button.setText("Thoát")
        # Kết nối tín hiệu
        login_button.clicked.connect(self.attempt_login)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        # Cho phép nhấn Enter
        self.username_input.returnPressed.connect(login_button.click)
        self.password_input.returnPressed.connect(login_button.click)
        # Đặt focus vào ô username khi mở dialog
        self.username_input.setFocus()

    def attempt_login(self):
        """Kiểm tra thông tin đăng nhập bằng auth_manager."""
        if not AUTH_MANAGER_AVAILABLE:
            show_error_message(self, "Lỗi", "Module xác thực không khả dụng.")
            return

        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            show_error_message(self, "Thiếu Thông Tin", "Vui lòng nhập tên đăng nhập và mật khẩu.")
            return

        print(f"Attempting login for user: {username}")
        # Gọi hàm từ auth_manager đã import
        user_data = auth_manager.get_user_by_username(username)

        if user_data:
            print(f"User '{username}' found. Verifying password...")
            hashed_password = user_data.get('password_hash')
            if hashed_password and auth_manager.verify_password(password, hashed_password):
                print("Login successful!")
                # Lưu thông tin cần thiết (không lưu hash)
                self.logged_in_user_info = {
                    'id': user_data.get('id'),
                    'username': user_data.get('username'),
                    'role': user_data.get('role', 'user') # Mặc định là user nếu role bị thiếu
                }
                self.accept() # Đóng dialog và trả về Accepted
            else:
                print("Login failed: Incorrect password.")
                show_error_message(self, "Đăng Nhập Thất Bại", "Tên đăng nhập hoặc mật khẩu không đúng.")
                self.password_input.clear() # Xóa ô mật khẩu
                self.password_input.setFocus() # Focus vào ô mật khẩu sau lỗi
        else:
            print(f"Login failed: User '{username}' not found.")
            show_error_message(self, "Đăng Nhập Thất Bại", "Tên đăng nhập hoặc mật khẩu không đúng.")
            self.password_input.clear()
            # Có thể xóa cả username nếu muốn: self.username_input.clear()
            self.username_input.setFocus() # Đặt focus lại vào ô username

    def getLoggedInUserInfo(self) -> Optional[Dict]:
        """Trả về thông tin người dùng đã đăng nhập thành công."""
        return self.logged_in_user_info

# --- Chạy thử dialog ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Kiểm tra auth_manager trước khi chạy
    if not AUTH_MANAGER_AVAILABLE:
        QMessageBox.critical(None,"Lỗi Hệ Thống","Không thể import utils.auth_manager. Không thể chạy LoginWindow.")
        sys.exit(1)

    login_dialog = LoginWindow()
    # Hiển thị dialog và chờ kết quả
    if login_dialog.exec() == QDialog.DialogCode.Accepted:
        user_info = login_dialog.getLoggedInUserInfo()
        print("Đăng nhập thành công! Thông tin người dùng:")
        print(user_info)
    else:
        print("Người dùng đã thoát hoặc hủy đăng nhập.")

    # Thoát ứng dụng sau khi dialog đóng
    sys.exit(0)