# gui/history_management_window.py

import sys
import os
from pathlib import Path # Thêm Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QMessageBox, QAbstractItemView, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QItemSelectionModel

# --- Add project root ---
current_dir_hist = Path(__file__).resolve().parent
project_root_hist = current_dir_hist.parent
if str(project_root_hist) not in sys.path:
    sys.path.insert(0, str(project_root_hist))

# --- Import Dependencies ---
try:
    from database.database_manager import get_all_history, delete_history_records
    DATABASE_AVAILABLE_HIST = True
except ImportError: DATABASE_AVAILABLE_HIST = False; print("HistoryMgtWindow: DB manager not found.")

try: from .ui_helpers import show_error_message, show_info_message, ask_confirmation
except ImportError: print("HistoryMgtWindow: ui_helpers not found."); # Thêm fallback nếu muốn

# --- Fallback helpers ---
if 'show_error_message' not in globals():
    # Đảm bảo QMessageBox được import nếu cần fallback
    try: from PyQt6.QtWidgets import QMessageBox
    except ImportError: pass

    def show_error_message(p, t, m):
        try: QMessageBox.critical(p, t, m)
        except NameError: print(f"Fallback Error Msg: {t} - {m}")
    def show_info_message(p, t, m):
        try: QMessageBox.information(p, t, m)
        except NameError: print(f"Fallback Info Msg: {t} - {m}")
    def ask_confirmation(p, t, q):
        try: return QMessageBox.question(p, t, q, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes
        except NameError: return False # Mặc định là No nếu lỗi

# --- Đổi tên class ---
class HistoryManagementWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Quản Lý Lịch Sử Nhận Diện') # <<< Đổi tiêu đề
        self.resize(800, 600)
        self.initUI()
        if DATABASE_AVAILABLE_HIST:
            self.loadHistoryData()
        # self.show() # Không cần show ở đây, cửa sổ cha sẽ gọi

    def initUI(self):
        """Khởi tạo giao diện người dùng cho cửa sổ lịch sử."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # --- Layout nút trên cùng ---
        top_button_layout = QHBoxLayout()
        layout.addLayout(top_button_layout)

        self.refresh_button = QPushButton('Làm Mới')
        self.refresh_button.setToolTip("Tải lại danh sách lịch sử")
        self.refresh_button.clicked.connect(self.loadHistoryData)
        top_button_layout.addWidget(self.refresh_button)

        self.delete_button = QPushButton('Xóa Mục Chọn')
        self.delete_button.setToolTip("Xóa các dòng đang được chọn")
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self.deleteSelectedHistory)
        top_button_layout.addWidget(self.delete_button)

        top_button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # --- Bỏ nút Close ở đây, vì cửa sổ này là chức năng riêng ---
        # self.close_button = QPushButton('Đóng') # Bỏ đi
        # ... (code liên quan close_button bị bỏ) ...

        # --- Bảng lịch sử ---
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(['ID', 'Thời gian', 'Ảnh', 'Kết quả', 'Tin cậy'])
        header = self.history_table.horizontalHeader(); header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents); header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents); header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch); header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents); header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.history_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection); self.history_table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel); self.history_table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.history_table.itemSelectionChanged.connect(self.updateDeleteButtonState)
        layout.addWidget(self.history_table)

        if not DATABASE_AVAILABLE_HIST:
            self.refresh_button.setEnabled(False); self.delete_button.setEnabled(False)
            show_error_message(self, "Lỗi Database", "Chức năng lịch sử không khả dụng.")
            self.history_table.setRowCount(1); item = QTableWidgetItem("Không thể tải lịch sử."); item.setTextAlignment(Qt.AlignmentFlag.AlignCenter); self.history_table.setItem(0, 0, item); self.history_table.setSpan(0, 0, 1, self.history_table.columnCount())
        else: self.updateDeleteButtonState()

    def updateDeleteButtonState(self):
        """Kích hoạt/Vô hiệu hóa nút xóa dựa trên lựa chọn."""
        enable_delete = DATABASE_AVAILABLE_HIST and bool(self.history_table.selectionModel().selectedRows())
        self.delete_button.setEnabled(enable_delete)

    def loadHistoryData(self):
        """Lấy dữ liệu từ database và cập nhật bảng."""
        if not DATABASE_AVAILABLE_HIST: return
        # Ngắt kết nối signal tạm thời
        try: self.history_table.itemSelectionChanged.disconnect(self.updateDeleteButtonState)
        except TypeError: pass # Bỏ qua nếu chưa kết nối

        print("HistoryMgtWindow: Loading history data...")
        try: history_records = get_all_history()
        except Exception as e: print(f"HistoryMgtWindow: Error get_all_history: {e}"); show_error_message(self, "Lỗi DB", f"Lỗi lấy lịch sử:\n{e}"); history_records = []

        self.history_table.setRowCount(0) # Xóa bảng cũ
        if not history_records:
            print("HistoryMgtWindow: No history records found."); self.history_table.setRowCount(1); item = QTableWidgetItem("Không có dữ liệu lịch sử."); item.setTextAlignment(Qt.AlignmentFlag.AlignCenter); self.history_table.setItem(0, 0, item); self.history_table.setSpan(0, 0, 1, self.history_table.columnCount())
        else:
            self.history_table.setRowCount(len(history_records))
            for row_index, record in enumerate(history_records):
                # Lấy dữ liệu an toàn với .get()
                rec_id = record.get('id', '')
                rec_time = record.get('timestamp', 'N/A')
                rec_path = record.get('image_path', 'N/A')
                rec_class = record.get('predicted_class_name', 'N/A')
                rec_conf = record.get('confidence', 'N/A')

                item_id = QTableWidgetItem(str(rec_id))
                item_timestamp = QTableWidgetItem(rec_time)
                item_path = QTableWidgetItem(rec_path)
                item_class = QTableWidgetItem(rec_class)
                item_confidence = QTableWidgetItem(rec_conf)

                # Căn chỉnh
                item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item_confidence.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item_timestamp.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Lưu ID vào dữ liệu của item để dễ lấy khi xóa
                item_id.setData(Qt.ItemDataRole.UserRole, rec_id)

                # Đặt item vào bảng
                self.history_table.setItem(row_index, 0, item_id)
                self.history_table.setItem(row_index, 1, item_timestamp)
                self.history_table.setItem(row_index, 2, item_path)
                self.history_table.setItem(row_index, 3, item_class)
                self.history_table.setItem(row_index, 4, item_confidence)

            print(f"HistoryMgtWindow: Loaded {len(history_records)} records.")
            self.history_table.scrollToTop() # Cuộn lên đầu bảng

        # Kết nối lại signal và cập nhật nút
        self.updateDeleteButtonState(); self.history_table.itemSelectionChanged.connect(self.updateDeleteButtonState)

    def deleteSelectedHistory(self):
        """Xóa các dòng được chọn trong bảng khỏi database."""
        if not DATABASE_AVAILABLE_HIST: show_error_message(self, "Lỗi", "Database không khả dụng."); return

        selected_rows_indices = self.history_table.selectionModel().selectedRows()
        if not selected_rows_indices: show_info_message(self, "Thông báo", "Vui lòng chọn ít nhất một dòng để xóa."); return

        ids_to_delete = []
        for model_index in selected_rows_indices:
            row = model_index.row(); id_item = self.history_table.item(row, 0) # Lấy item ở cột ID (cột 0)
            if id_item:
                # Lấy ID đã lưu trong data của item
                record_id = id_item.data(Qt.ItemDataRole.UserRole)
                if record_id is not None:
                    try: ids_to_delete.append(int(record_id)) # Chuyển sang int
                    except ValueError: print(f"Warning: Invalid non-integer ID found in row {row}: {record_id}")
                else: print(f"Warning: Could not retrieve record ID from item data in row {row}")
            else: print(f"Warning: Could not get item for ID column in selected row {row}")

        if not ids_to_delete: show_error_message(self, "Lỗi", "Không thể lấy được ID của các mục đã chọn."); return

        num_selected = len(ids_to_delete)
        if ask_confirmation(self, "Xác nhận Xóa", f"Bạn có chắc chắn muốn xóa {num_selected} mục đã chọn khỏi lịch sử không?\nHành động này không thể hoàn tác."):
            print(f"Attempting to delete history records with IDs: {ids_to_delete}")
            success, message = delete_history_records(ids_to_delete) # Gọi hàm từ DB manager
            if success: show_info_message(self, "Thành công", message); self.loadHistoryData() # Tải lại bảng
            else: show_error_message(self, "Xóa Thất Bại", message)
        else:
            print("Deletion cancelled by user.")


# --- Test Block ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    if not DATABASE_AVAILABLE_HIST:
         # Import QMessageBox nếu chưa có ở global scope
         try: from PyQt6.QtWidgets import QMessageBox
         except ImportError: pass
         try: QMessageBox.critical(None, "Lỗi DB", "Không thể chạy HistoryManagementWindow do thiếu kết nối DB.")
         except NameError: print("Cannot show critical error for missing DB in HistoryManagementWindow")
         sys.exit(1)

    history_win = HistoryManagementWindow()
    history_win.show() # Gọi show ở đây để test độc lập
    sys.exit(app.exec())