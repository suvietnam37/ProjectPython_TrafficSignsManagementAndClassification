# gui/ui_helpers.py

from PyQt6.QtWidgets import QMessageBox, QWidget
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QSize

# --- Hàm hiển thị hộp thoại thông báo ---

def show_message_box(parent: QWidget, title: str, message: str, icon: QMessageBox.Icon = QMessageBox.Icon.Information):
    """
    Hiển thị một hộp thoại thông báo chuẩn.

    Args:
        parent (QWidget): Cửa sổ cha (hoặc None).
        title (str): Tiêu đề của hộp thoại.
        message (str): Nội dung thông báo.
        icon (QMessageBox.Icon): Loại icon (Information, Warning, Critical, Question).
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setIcon(icon)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok) # Chỉ có nút OK
    msg_box.exec()

def show_info_message(parent: QWidget, title: str, message: str):
    """Hiển thị hộp thoại thông tin."""
    show_message_box(parent, title, message, QMessageBox.Icon.Information)

def show_warning_message(parent: QWidget, title: str, message: str):
    """Hiển thị hộp thoại cảnh báo."""
    show_message_box(parent, title, message, QMessageBox.Icon.Warning)

def show_error_message(parent: QWidget, title: str, message: str):
    """Hiển thị hộp thoại lỗi."""
    show_message_box(parent, title, message, QMessageBox.Icon.Critical)

def ask_confirmation(parent: QWidget, title: str, question: str) -> bool:
    """
    Hiển thị hộp thoại xác nhận (Yes/No).

    Args:
        parent (QWidget): Cửa sổ cha (hoặc None).
        title (str): Tiêu đề hộp thoại.
        question (str): Câu hỏi xác nhận.

    Returns:
        bool: True nếu người dùng nhấn Yes, False nếu nhấn No.
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(question)
    msg_box.setIcon(QMessageBox.Icon.Question)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    msg_box.setDefaultButton(QMessageBox.StandardButton.No) # Mặc định chọn No
    reply = msg_box.exec()
    return reply == QMessageBox.StandardButton.Yes

# --- Hàm xử lý hình ảnh (Ví dụ) ---

def scale_pixmap(pixmap: QPixmap, target_size: QSize) -> QPixmap:
    """
    Thay đổi kích thước QPixmap để vừa với target_size mà vẫn giữ tỷ lệ khung hình.

    Args:
        pixmap (QPixmap): Đối tượng QPixmap gốc.
        target_size (QSize): Kích thước tối đa mong muốn (thường là size của QLabel).

    Returns:
        QPixmap: Đối tượng QPixmap đã được thay đổi kích thước.
    """
    if pixmap.isNull() or not target_size.isValid():
        return pixmap # Trả về gốc nếu không hợp lệ

    return pixmap.scaled(
        target_size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )


# --- (Không cần test block phức tạp cho file helper này) ---
if __name__ == '__main__':
    # Chỉ chạy test đơn giản nếu cần, ví dụ test hiển thị message box
    # Cần QApplication để chạy test widget
    import sys
    from PyQt6.QtWidgets import QApplication, QPushButton

    app = QApplication(sys.argv)
    main_widget = QWidget() # Widget giả làm parent

    print("Testing UI Helpers...")

    # Test info message
    # btn1 = QPushButton("Test Info")
    # btn1.clicked.connect(lambda: show_info_message(main_widget, "Thông tin", "Đây là thông báo thông tin."))
    # btn1.show()

    # Test confirmation
    print("Asking confirmation...")
    confirmed = ask_confirmation(main_widget, "Xác nhận", "Bạn có chắc muốn tiếp tục không?")
    print(f"User confirmed: {confirmed}")

    # Test error message
    # show_error_message(main_widget, "Lỗi", "Đã có lỗi xảy ra!")

    # Không cần chạy app.exec() nếu chỉ test logic không cần tương tác

    print("UI Helpers testing finished (basic).")
    # sys.exit(app.exec()) # Bỏ comment nếu muốn giữ cửa sổ test mở