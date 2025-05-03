# database/data_exporter.py

import csv
import os
import sys
from datetime import datetime

# --- Thêm thư mục gốc vào sys.path ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Import Trình quản lý Database ---
try:
    from database.database_manager import get_all_history, DATABASE_PATH
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"DataExporter Error: Could not import database_manager. Error: {e}")
    DATABASE_AVAILABLE = False

# --- Hàm chính để xuất CSV ---
def export_history_to_csv(output_dir='.', filename=None):
    """
    Xuất toàn bộ lịch sử nhận diện từ database ra file CSV.

    Args:
        output_dir (str): Thư mục để lưu file CSV.
        filename (str, optional): Tên file CSV. Nếu None, sẽ tạo tên mặc định
                                  kèm timestamp.
    """
    if not DATABASE_AVAILABLE:
        print("ERROR: Cannot export data, database manager not available.")
        return False

    print("Fetching history data from database...")
    history_data = get_all_history() # Lấy dữ liệu dạng list of dict

    if not history_data:
        print("No history data found to export.")
        return False

    if filename is None:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gtsrb_history_export_{timestamp_str}.csv"

    output_filepath = os.path.join(output_dir, filename)

    # Đảm bảo thư mục output tồn tại
    os.makedirs(output_dir, exist_ok=True)

    print(f"Exporting {len(history_data)} records to: {output_filepath}")

    try:
        # Lấy header từ keys của dictionary đầu tiên
        headers = history_data[0].keys()

        with open(output_filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader() # Ghi dòng header
            writer.writerows(history_data) # Ghi tất cả các dòng dữ liệu

        print("Export successful!")
        return True

    except Exception as e:
        print(f"ERROR: Failed to export data to CSV. Reason: {e}")
        return False

# --- Chạy trực tiếp ---
if __name__ == "__main__":
    print("--- Running Database History Exporter ---")
    # Xuất ra thư mục gốc của dự án làm ví dụ
    export_history_to_csv(output_dir=project_root)
    print("--- Exporter Finished ---")