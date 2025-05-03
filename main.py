# main.py
import sys
import os
import logging # Thêm logging
from pathlib import Path # Dùng pathlib cho đường dẫn
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox # Thêm QMessageBox

# --- Setup Logging cơ bản ---
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True) # Tạo thư mục logs nếu chưa có
log_file = log_dir / 'gtsrb_app.log' # Đổi tên file log cho rõ ràng
# Cấu hình logging
logging.basicConfig(
    level=logging.INFO, # Mức log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s', # Định dạng log
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8', mode='a'), # Ghi vào file, mode 'a' để nối tiếp
        logging.StreamHandler() # Vẫn in ra console
    ]
)
logger_main = logging.getLogger("MainApp") # Đặt tên logger chính

# --- Add project root ---
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    logger_main.info(f"Added project root to sys.path: {project_root}")

# --- Import UI Windows ---
try:
    # <<< THAY ĐỔI: Import MainHubWindow thay vì MainWindow >>>
    from gui.main_hub_window import MainHubWindow
    from gui.login_window import LoginWindow, AUTH_MANAGER_AVAILABLE as LOGIN_AUTH_OK
    logger_main.info("UI Windows imported successfully.")
    if not LOGIN_AUTH_OK:
         logger_main.warning("Auth Manager not available for LoginWindow. Login might fail.")
except ImportError as e:
    logger_main.critical(f"FATAL ERROR: Could not import UI windows.", exc_info=True)
    # Hiển thị lỗi cho người dùng cuối nếu có thể
    try:
        app_err = QApplication(sys.argv) # Cần app để hiện QMessageBox
        QMessageBox.critical(None, "Lỗi Khởi Động", f"Không thể tải các thành phần giao diện cần thiết.\n\nChi tiết lỗi:\n{e}\n\nVui lòng kiểm tra cài đặt và file log trong thư mục 'logs'.")
    except Exception as e_msg:
        print(f"Could not show error message box: {e_msg}") # In ra console nếu QMessageBox lỗi
    sys.exit(1)
except Exception as e:
    logger_main.critical(f"FATAL ERROR: An unexpected error occurred during UI import.", exc_info=True)
    try:
        app_err = QApplication(sys.argv)
        QMessageBox.critical(None, "Lỗi Khởi Động", f"Lỗi không mong muốn khi khởi tạo giao diện.\n\nChi tiết lỗi:\n{e}\n\nVui lòng kiểm tra file log trong thư mục 'logs'.")
    except Exception as e_msg:
         print(f"Could not show error message box: {e_msg}")
    sys.exit(1)

def main():
    logger_main.info("=======================================")
    logger_main.info("=== Starting GTSRB Application ===")
    logger_main.info("=======================================")
    app = QApplication(sys.argv)

    logger_main.info("Showing LoginWindow...")
    try:
        login_dialog = LoginWindow()
    except Exception as e:
        logger_main.critical("Failed to create LoginWindow.", exc_info=True)
        QMessageBox.critical(None, "Lỗi Khởi Động", f"Không thể tạo cửa sổ đăng nhập.\n\nLỗi: {e}")
        sys.exit(1)

    # Hiển thị dialog đăng nhập và chờ kết quả
    if login_dialog.exec() == QDialog.DialogCode.Accepted:
        logged_in_user = login_dialog.getLoggedInUserInfo() # Lấy thông tin user đã đăng nhập
        if logged_in_user:
            username = logged_in_user.get('username', 'N/A')
            role = logged_in_user.get('role', 'N/A')
            logger_main.info(f"Login successful for user '{username}' (Role: {role}). Creating MainHubWindow...")
            try:
                # <<< THAY ĐỔI: Tạo MainHubWindow và truyền user vào >>>
                main_hub = MainHubWindow(current_user=logged_in_user)
                main_hub.show() # Hiển thị cửa sổ Hub
                logger_main.info("Starting application event loop...")
                exit_code = app.exec() # Chạy vòng lặp sự kiện
                logger_main.info(f"Application event loop finished with exit code: {exit_code}")
                sys.exit(exit_code)
            except Exception as e:
                 logger_main.critical("Failed to create or show MainHubWindow.", exc_info=True)
                 QMessageBox.critical(None, "Lỗi Giao Diện Chính", f"Không thể khởi tạo giao diện chính.\n\nLỗi: {e}")
                 sys.exit(1)
        else:
             logger_main.error("Login accepted but no user info returned. Exiting.")
             QMessageBox.critical(None, "Lỗi Đăng Nhập", "Đăng nhập được chấp nhận nhưng không có thông tin người dùng. Liên hệ quản trị viên.")
             sys.exit(1)
    else:
        logger_main.info("Login cancelled or failed by user. Exiting application.")
        sys.exit(0) # Thoát bình thường nếu hủy đăng nhập

if __name__ == "__main__":
    # Cấu hình Qt nếu cần (ví dụ: scale DPI) - Nên đặt trước khi tạo QApplication
    # os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    # QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling) # Cú pháp mới hơn
    main()