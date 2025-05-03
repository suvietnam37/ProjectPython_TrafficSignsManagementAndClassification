# gui/main_hub_window.py

import sys
import os
import logging
from pathlib import Path
from typing import Optional, Dict

try:
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
        QSpacerItem, QSizePolicy, QGridLayout, QFrame, QMessageBox # Thêm QMessageBox
    )
    from PyQt6.QtGui import QFont, QIcon # Thêm QIcon nếu muốn dùng icon
    from PyQt6.QtCore import Qt, QSize, pyqtSignal # Thêm pyqtSignal nếu cần signal từ Settings
    PYQT6_AVAILABLE_HUB = True
except ImportError:
    print("MainHubWindow FATAL ERROR: PyQt6 not found.")
    PYQT6_AVAILABLE_HUB = False
    # Nên dừng ứng dụng nếu cửa sổ chính không thể tạo

logger_hub = logging.getLogger(__name__)

# --- Add project root ---
current_dir_hub = Path(__file__).resolve().parent
project_root_hub = current_dir_hub.parent
if str(project_root_hub) not in sys.path:
    sys.path.insert(0, str(project_root_hub))
    logger_hub.info(f"MainHubWindow added project root: {project_root_hub}")

# --- Import các cửa sổ chức năng và kiểm tra ---
# Đặt biến cờ mặc định là False
RECOG_WIN_OK = False
USER_MGMT_WIN_OK = False
HIST_MGMT_WIN_OK = False
SETTINGS_WIN_OK = False
UI_HELPERS_OK = False

try: from .recognition_window import RecognitionWindow; RECOG_WIN_OK = True
except ImportError as e: logger_hub.error(f"Failed to import RecognitionWindow: {e}")

try: from .user_management_window import UserManagementWindow, AUTH_MANAGER_AVAILABLE_UM; USER_MGMT_WIN_OK = AUTH_MANAGER_AVAILABLE_UM
except ImportError as e: logger_hub.error(f"Failed to import UserManagementWindow or its auth_manager: {e}")

try: from .history_management_window import HistoryManagementWindow, DATABASE_AVAILABLE_HIST; HIST_MGMT_WIN_OK = DATABASE_AVAILABLE_HIST
except ImportError as e: logger_hub.error(f"Failed to import HistoryManagementWindow or its DB access: {e}")

try: from .settings_window import SettingsWindow, CONFIG_LOADER_AVAILABLE; SETTINGS_WIN_OK = CONFIG_LOADER_AVAILABLE
except ImportError as e: logger_hub.error(f"Failed to import SettingsWindow or its config_loader: {e}")

try: from .ui_helpers import show_info_message, show_error_message; UI_HELPERS_OK = True
except ImportError: logger_hub.warning("MainHubWindow: ui_helpers not found."); # Thêm fallback nếu muốn

# --- Fallback helpers ---
if not UI_HELPERS_OK:
    # Đảm bảo QMessageBox được import nếu cần fallback
    try: from PyQt6.QtWidgets import QMessageBox
    except ImportError: pass

    def show_error_message(p, t, m):
        try: QMessageBox.critical(p, t, m)
        except NameError: print(f"Fallback Error Msg: {t} - {m}")
    def show_info_message(p, t, m):
        try: QMessageBox.information(p, t, m)
        except NameError: print(f"Fallback Info Msg: {t} - {m}")


class MainHubWindow(QWidget):
    def __init__(self, current_user: Optional[Dict] = None):
        super().__init__()
        if not PYQT6_AVAILABLE_HUB:
            # Hiển thị lỗi và thoát nếu thiếu thư viện cơ bản
            try:
                app_err = QApplication.instance() or QApplication(sys.argv)
                QMessageBox.critical(None, "Lỗi nghiêm trọng", "PyQt6 không khả dụng. Không thể khởi chạy giao diện chính.")
            except Exception: print("Cannot show critical error for missing PyQt6 in MainHubWindow")
            sys.exit("PyQt6 not found, cannot start Main Hub.")

        self.current_user = current_user if current_user else {}
        self.recognition_window_instance: Optional[RecognitionWindow] = None
        self.user_mgmt_window_instance: Optional[UserManagementWindow] = None
        self.history_mgmt_window_instance: Optional[HistoryManagementWindow] = None
        self.settings_window_instance: Optional[SettingsWindow] = None

        self.initUI()
        self.update_window_title() # Đặt tiêu đề sau khi initUI

    def update_window_title(self):
        window_title = "Hệ Thống Quản Lý & Nhận Diện Biển Báo GTSRB"
        username = self.current_user.get('username')
        role = self.current_user.get('role', 'user') # Mặc định là user
        if username:
            window_title += f" - (Người dùng: {username} - Vai trò: {role.capitalize()})"
        self.setWindowTitle(window_title)

    def initUI(self):
        self.resize(600, 400) # Kích thước ban đầu cho hub
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # --- Tiêu đề ---
        title_label = QLabel("Chọn Chức Năng")
        title_font = QFont(); title_font.setPointSize(18); title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        main_layout.addSpacerItem(QSpacerItem(20, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # --- Grid Layout cho các nút chức năng ---
        grid_layout = QGridLayout()
        grid_layout.setSpacing(25) # Khoảng cách giữa các nút
        main_layout.addLayout(grid_layout)

        button_font = QFont(); button_font.setPointSize(12)
        button_size = QSize(180, 60) # Kích thước nút

        # 1. Nút Nhận Diện
        self.recog_button = QPushButton(" Nhận Diện\n Biển Báo") # Thêm icon nếu muốn
        # self.recog_button.setIcon(QIcon("path/to/recog_icon.png")) # Ví dụ thêm icon
        # self.recog_button.setIconSize(QSize(32, 32))
        self.recog_button.setFont(button_font); self.recog_button.setFixedSize(button_size)
        self.recog_button.setEnabled(RECOG_WIN_OK) # Bật nếu cửa sổ import OK
        if RECOG_WIN_OK: self.recog_button.clicked.connect(self.open_recognition_window)
        grid_layout.addWidget(self.recog_button, 0, 0, Qt.AlignmentFlag.AlignCenter)

        # 2. Nút Quản Lý Người Dùng
        self.user_mgmt_button = QPushButton(" Quản Lý\n Người Dùng")
        self.user_mgmt_button.setFont(button_font); self.user_mgmt_button.setFixedSize(button_size)
        # Điều kiện: Role admin VÀ cửa sổ + auth manager OK
        can_manage_users = self.current_user.get('role') == 'admin' and USER_MGMT_WIN_OK
        self.user_mgmt_button.setEnabled(can_manage_users)
        if can_manage_users: self.user_mgmt_button.clicked.connect(self.open_user_management_window)
        # Log lý do bị tắt (chỉ khi debug)
        elif self.current_user.get('role') != 'admin': logger_hub.debug("User Mgt button disabled: Not admin role.")
        elif not USER_MGMT_WIN_OK: logger_hub.warning("User Mgt button disabled: Window or Auth Manager unavailable.")
        grid_layout.addWidget(self.user_mgmt_button, 0, 1, Qt.AlignmentFlag.AlignCenter)

        # 3. Nút Quản Lý Lịch Sử
        self.hist_mgmt_button = QPushButton(" Quản Lý\n Lịch Sử")
        self.hist_mgmt_button.setFont(button_font); self.hist_mgmt_button.setFixedSize(button_size)
        self.hist_mgmt_button.setEnabled(HIST_MGMT_WIN_OK) # Bật nếu cửa sổ và DB OK
        if HIST_MGMT_WIN_OK: self.hist_mgmt_button.clicked.connect(self.open_history_management_window)
        else: logger_hub.warning("History Mgt button disabled: Window or DB unavailable.")
        grid_layout.addWidget(self.hist_mgmt_button, 1, 0, Qt.AlignmentFlag.AlignCenter)

        # 4. Nút Cài Đặt
        self.settings_button = QPushButton(" Cài Đặt\n Hệ Thống")
        self.settings_button.setFont(button_font); self.settings_button.setFixedSize(button_size)
        self.settings_button.setEnabled(SETTINGS_WIN_OK) # Bật nếu cửa sổ và config loader OK
        if SETTINGS_WIN_OK: self.settings_button.clicked.connect(self.open_settings_window)
        else: logger_hub.warning("Settings button disabled: Window or Config Loader unavailable.")
        grid_layout.addWidget(self.settings_button, 1, 1, Qt.AlignmentFlag.AlignCenter)

        main_layout.addStretch(1) # Đẩy nút Thoát xuống dưới

        # --- Nút Thoát ---
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch(1)
        self.exit_button = QPushButton("Thoát Ứng Dụng")
        self.exit_button.setFont(button_font)
        # Kết nối với slot để đóng ứng dụng một cách an toàn
        self.exit_button.clicked.connect(self.close_application)
        bottom_layout.addWidget(self.exit_button)
        bottom_layout.addStretch(1)
        main_layout.addLayout(bottom_layout)
        main_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))


    # --- Hàm mở các cửa sổ chức năng ---
    # Sử dụng mẫu: Kiểm tra instance, nếu chưa có thì tạo mới, nếu có thì đưa lên trước
    def open_window(self, window_attribute_name, window_class, *args, **kwargs):
        """Hàm chung để mở hoặc kích hoạt cửa sổ con."""
        window_instance = getattr(self, window_attribute_name, None)
        # Kiểm tra xem instance có tồn tại và có phải là instance của class mong muốn không
        if window_instance is None or not isinstance(window_instance, window_class) or not window_instance.isVisible():
            try:
                # Tạo cửa sổ mới, truyền parent=self để quản lý vòng đời (giúp đóng cùng Hub nếu Hub đóng)
                # Lưu ý: parent=self có thể không cần nếu muốn cửa sổ con tồn tại độc lập
                new_instance = window_class(*args, **kwargs) # Bỏ parent=self nếu muốn độc lập
                setattr(self, window_attribute_name, new_instance)
                new_instance.show()
                new_instance.activateWindow() # Mang lên trên cùng
                new_instance.raise_()      # Đảm bảo focus
                logger_hub.info(f"Opened new {window_class.__name__}.")
            except Exception as e:
                show_error_message(self, "Lỗi Mở Cửa Sổ", f"Không thể mở {window_class.__name__}:\n{e}")
                logger_hub.error(f"Error opening {window_class.__name__}", exc_info=True)
                setattr(self, window_attribute_name, None) # Reset instance nếu tạo lỗi
        else:
            # Nếu cửa sổ đã tồn tại và đang hiển thị, đưa nó lên trước
            window_instance.activateWindow()
            window_instance.raise_()
            # Tùy chọn: Gọi hàm tải lại dữ liệu nếu cần (ví dụ: history)
            if hasattr(window_instance, 'loadHistoryData'): window_instance.loadHistoryData()
            if hasattr(window_instance, 'loadUsers'): window_instance.loadUsers()
            if hasattr(window_instance, 'loadCurrentSettings'): window_instance.loadCurrentSettings()
            logger_hub.info(f"Activated existing {window_class.__name__}.")


    def open_recognition_window(self):
        if not RECOG_WIN_OK:
            show_error_message(self,"Lỗi", "Không thể mở chức năng Nhận diện do lỗi import.")
            return
        # Truyền user vào nếu RecognitionWindow cần
        self.open_window('recognition_window_instance', RecognitionWindow, current_user=self.current_user)

    def open_user_management_window(self):
        if not self.user_mgmt_button.isEnabled(): # Kiểm tra lại quyền và khả năng import
            show_error_message(self,"Lỗi", "Không thể mở chức năng Quản lý Người dùng (thiếu quyền hoặc lỗi import).")
            return
        self.open_window('user_mgmt_window_instance', UserManagementWindow)

    def open_history_management_window(self):
        if not HIST_MGMT_WIN_OK:
            show_error_message(self,"Lỗi", "Không thể mở chức năng Quản lý Lịch sử do lỗi import hoặc DB.")
            return
        self.open_window('history_mgmt_window_instance', HistoryManagementWindow)

    def open_settings_window(self):
        if not SETTINGS_WIN_OK:
            show_error_message(self,"Lỗi", "Không thể mở chức năng Cài đặt do lỗi import hoặc config.")
            return
        self.open_window('settings_window_instance', SettingsWindow)
        # Kết nối signal settings_changed nếu SettingsWindow phát ra nó
        settings_win = getattr(self, 'settings_window_instance', None)
        # Kiểm tra xem signal có tồn tại và có thể gọi được không
        if settings_win and hasattr(settings_win, 'settings_changed') and isinstance(getattr(settings_win, 'settings_changed', None), pyqtSignal):
             logger_hub.debug("Attempting to connect settings_changed signal...")
             try:
                 # Ngắt kết nối cũ trước để tránh kết nối nhiều lần
                 settings_win.settings_changed.disconnect(self._handle_settings_change_in_hub)
                 logger_hub.debug("Disconnected previous settings_changed connection (if any).")
             except TypeError:
                 logger_hub.debug("No previous settings_changed connection found to disconnect.")
             except Exception as e_disc:
                 logger_hub.warning(f"Error disconnecting settings_changed signal: {e_disc}")

             try:
                 settings_win.settings_changed.connect(self._handle_settings_change_in_hub)
                 logger_hub.info("Connected settings_changed signal from SettingsWindow.")
             except TypeError as e_connect_type:
                  logger_hub.warning(f"TypeError connecting settings_changed signal: {e_connect_type}. Is the signal defined correctly?")
             except Exception as e_connect:
                 logger_hub.error(f"Failed to connect settings_changed signal: {e_connect}", exc_info=True)
        elif settings_win:
             logger_hub.debug("SettingsWindow instance exists but does not have a connectable 'settings_changed' signal.")


    def _handle_settings_change_in_hub(self):
        """Xử lý khi Hub nhận được tín hiệu cài đặt đã thay đổi."""
        logger_hub.info("MainHub received 'settings_changed' signal. (Further actions can be implemented here)")
        # Ví dụ: Cập nhật tiêu đề cửa sổ nếu tên người dùng/role thay đổi trong cài đặt (ít khả năng)
        # Hoặc: Buộc các cửa sổ con tải lại cấu hình nếu cần thiết
        # self.update_window_title() # Cập nhật nếu cần
        pass # Hiện tại chưa cần làm gì thêm ở Hub

    def close_application(self):
        """Đóng ứng dụng một cách an toàn."""
        logger_hub.info("Close application requested.")
        # Đóng tất cả các cửa sổ con đang mở trước khi thoát
        logger_hub.debug("Closing child windows...")
        for attr_name in ['recognition_window_instance', 'user_mgmt_window_instance', 'history_mgmt_window_instance', 'settings_window_instance']:
            instance = getattr(self, attr_name, None)
            if instance and hasattr(instance, 'isVisible') and instance.isVisible():
                logger_hub.debug(f"Closing {attr_name}...")
                try:
                    instance.close()
                except Exception as e_close:
                    logger_hub.warning(f"Error closing {attr_name}: {e_close}")
        logger_hub.info("Exiting application...")
        QApplication.instance().quit()


    # --- Ghi đè closeEvent để xử lý khi người dùng đóng cửa sổ Hub bằng nút X ---
    def closeEvent(self, event):
        logger_hub.debug("MainHub closeEvent triggered.")
        self.close_application() # Gọi hàm đóng an toàn
        event.accept() # Chấp nhận sự kiện đóng

# --- Test Block ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Tạo user giả để test
    fake_user_admin = {'id': 1, 'username': 'test_admin', 'role': 'admin'}
    fake_user_normal = {'id': 2, 'username': 'test_user', 'role': 'user'}

    # Chọn user để test
    # current_test_user = fake_user_normal
    current_test_user = fake_user_admin

    logger_hub.info(f"--- Running MainHubWindow Standalone Test (User: {current_test_user.get('username')}) ---")

    try:
        hub_window = MainHubWindow(current_user=current_test_user)
        hub_window.show()
        sys.exit(app.exec())
    except Exception as e:
         logger_hub.critical(f"Failed to run MainHubWindow test: {e}", exc_info=True)
         # Hiển thị lỗi nếu có thể
         try: QMessageBox.critical(None, "Lỗi Test", f"Không thể chạy MainHubWindow.\n\nLỗi: {e}")
         except Exception as e_msg: print(f"Could not show test error message box: {e_msg}")
         sys.exit(1)