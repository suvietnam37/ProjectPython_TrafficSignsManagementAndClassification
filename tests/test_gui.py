# tests/test_gui.py

import unittest
import sys
import os

# --- Thêm thư mục gốc ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Import thư viện GUI và các cửa sổ ---
try:
    from PyQt6.QtWidgets import QApplication
    # Import các cửa sổ cần test (nếu có thể test đơn lẻ)
    # from gui.main_window import MainWindow
    # from gui.history_window import HistoryWindow
    # from gui.settings_window import SettingsWindow
    GUI_AVAILABLE = True
    # Tạo một QApplication instance nếu chưa có (cần cho test widget)
    app = QApplication.instance() or QApplication(sys.argv)
except ImportError:
    GUI_AVAILABLE = False
    print("WARNING: PyQt6 not found or GUI modules failed to import. Skipping GUI tests.")


@unittest.skipUnless(GUI_AVAILABLE, "PyQt6 not available or GUI modules failed import.")
class TestGUI(unittest.TestCase):

    def test_main_window_creation(self):
        """Kiểm tra xem MainWindow có thể được tạo không (test rất cơ bản)."""
        print("\nTesting MainWindow creation...")
        try:
            from gui.main_hub_window import MainWindow # Import tại đây để tránh lỗi nếu thiếu
            window = MainWindow()
            self.assertIsNotNone(window)
            # Có thể thêm các assert khác để kiểm tra widget tồn tại
            self.assertTrue(hasattr(window, 'load_button'))
            self.assertTrue(hasattr(window, 'predict_button'))
            window.close() # Đóng cửa sổ sau khi test
            print("MainWindow creation test passed (basic).")
        except Exception as e:
            self.fail(f"Failed to create MainWindow: {e}")

    def test_history_window_creation(self):
        """Kiểm tra xem HistoryWindow có thể được tạo không."""
        print("\nTesting HistoryWindow creation...")
        try:
             from gui.history_window import HistoryWindow, DATABASE_AVAILABLE # Import tại đây
             if not DATABASE_AVAILABLE:
                  self.skipTest("Skipping HistoryWindow test: Database manager not available.")
             window = HistoryWindow()
             self.assertIsNotNone(window)
             self.assertTrue(hasattr(window, 'history_table'))
             window.close()
             print("HistoryWindow creation test passed (basic).")
        except Exception as e:
             self.fail(f"Failed to create HistoryWindow: {e}")

    # Thêm các test khác cho SettingsWindow, các nút bấm, v.v.
    # Lưu ý: Test tương tác GUI (ví dụ: click nút) thường cần các công cụ
    # chuyên dụng hơn như pytest-qt hoặc mô phỏng sự kiện phức tạp hơn.


if __name__ == '__main__':
    print("Running GUI Unit Tests (Basic)...")
    # Lưu ý: Chạy test GUI có thể mở và đóng nhanh các cửa sổ
    if GUI_AVAILABLE:
        unittest.main()
    else:
        print("\nSKIPPING TESTS: PyQt6 or GUI modules unavailable.")