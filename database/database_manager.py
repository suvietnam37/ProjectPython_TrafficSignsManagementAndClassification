# database/database_manager.py

import sqlite3
import os
from datetime import datetime
# <<< Đã import List, Tuple, Dict, Optional từ typing >>>
from typing import List, Tuple, Dict, Optional

# --- Lấy đường dẫn database ---
try:
    import config
    if hasattr(config, 'DATABASE_PATH'):
        DATABASE_PATH = config.DATABASE_PATH
    else:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'history.db')
        print("DBManager WARNING: config.DATABASE_PATH not found, using default.")
except (ImportError, AttributeError):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'history.db')
    print("DBManager WARNING: config module not found or lacks DATABASE_PATH, using default.")

print(f"DBManager using Database: {DATABASE_PATH}")


def create_connection():
    """ Tạo kết nối đến database """
    conn = None
    if not os.path.exists(DATABASE_PATH):
        print(f"DBManager Error: Database file not found at {DATABASE_PATH}")
        return None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row # Trả về kết quả dạng dictionary-like
        return conn
    except sqlite3.Error as e:
        print(f"DBManager Error connecting to database: {e}")
    return conn

def add_prediction_to_history(image_path: str, predicted_class_id: int, predicted_class_name: str, confidence: float) -> bool:
    """ Thêm một bản ghi dự đoán mới vào bảng history """
    conn = create_connection()
    if conn is None:
        print("DBManager: Cannot connect to database to add history.")
        return False
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = ''' INSERT INTO history(timestamp, image_path, predicted_class_id, predicted_class_name, confidence)
              VALUES(?,?,?,?,?) '''
    cur = conn.cursor()
    try:
        cur.execute(sql, (now, image_path, predicted_class_id, predicted_class_name, confidence))
        conn.commit()
        # print(f"DBManager: Prediction added to history: {os.path.basename(image_path)} -> {predicted_class_name}")
        return True
    except sqlite3.Error as e:
        print(f"DBManager Error adding prediction to history: {e}")
        return False
    finally:
        if conn:
            conn.close()

# <<< Đã sửa Type Hint -> List[Dict] >>>
def get_all_history() -> List[Dict]:
    """ Lấy tất cả các bản ghi từ bảng history, sắp xếp theo thời gian mới nhất trước """
    conn = create_connection()
    if conn is None:
        print("DBManager: Cannot connect to database to get history.")
        return []
    cur = conn.cursor()
    try:
        # Chọn cả ID để dùng cho việc xóa
        cur.execute("SELECT id, timestamp, image_path, predicted_class_name, confidence FROM history ORDER BY timestamp DESC")
        rows = cur.fetchall()
        # Chuyển đổi rows (list of sqlite3.Row) thành list of dictionaries
        history_list = []
        for row in rows:
            # Truy cập bằng tên cột nhờ conn.row_factory
            history_list.append({
                "id": row["id"],
                "timestamp": row["timestamp"],
                "image_path": row["image_path"],
                "predicted_class_name": row["predicted_class_name"],
                # Chuyển đổi confidence thành chuỗi %
                "confidence": f"{row['confidence']:.2%}" if isinstance(row['confidence'], (float, int)) else "N/A"
            })
        return history_list
    except sqlite3.Error as e:
        print(f"DBManager Error fetching history: {e}")
        return []
    finally:
        if conn:
            conn.close()

# <<< Đã sửa Type Hints -> List[int] và Tuple[bool, str] >>>
def delete_history_records(record_ids: List[int]) -> Tuple[bool, str]:
    """Xóa các bản ghi lịch sử dựa trên danh sách ID."""
    if not record_ids:
        return False, "Không có ID nào được cung cấp để xóa."

    conn = create_connection()
    if conn is None:
        return False, "Không thể kết nối database để xóa lịch sử."

    try:
        cur = conn.cursor()
        # Tạo chuỗi placeholders (?, ?, ...) tương ứng với số lượng ID
        placeholders = ', '.join('?' * len(record_ids))
        sql = f"DELETE FROM history WHERE id IN ({placeholders})"

        print(f"DBManager Executing SQL: {sql} with IDs: {record_ids}")
        cur.execute(sql, record_ids)
        conn.commit()

        deleted_count = cur.rowcount
        print(f"DBManager: Successfully deleted {deleted_count} record(s).")
        if deleted_count == len(record_ids):
             return True, f"Đã xóa thành công {deleted_count} mục."
        elif deleted_count > 0:
             return True, f"Đã xóa {deleted_count} mục (một số ID có thể không tồn tại hoặc đã bị xóa)."
        else:
             return False, "Không có mục nào được xóa (ID không tồn tại hoặc lỗi)."


    except sqlite3.Error as e:
        print(f"DBManager Error deleting history records: {e}")
        return False, f"Lỗi database khi xóa lịch sử: {e}"
    finally:
        if conn:
            conn.close()

# --- Ví dụ sử dụng (chỉ chạy khi thực thi file này trực tiếp) ---
if __name__ == '__main__':
    print("--- Testing Database Manager (database/database_manager.py) ---")

    # Thử thêm một bản ghi giả
    print("\nAdding dummy record...")
    add_prediction_to_history("/path/to/dummy/test.png", 14, "Dừng lại", 0.999)

    print("\nFetching history...")
    history_data = get_all_history()
    if history_data:
        print(f"Found {len(history_data)} records.")
        print("First few records:")
        for record in history_data[:3]: print(record)

        # Test xóa
        if len(history_data) >= 1:
             # Lấy ID của bản ghi mới nhất (đầu tiên trong list)
             id_to_delete = history_data[0]['id']
             # Lấy ID của bản ghi thứ 3 nếu có
             ids_to_delete_list = [id_to_delete]
             if len(history_data) >= 3:
                 ids_to_delete_list.append(history_data[2]['id'])
             # Thêm ID không tồn tại để test
             ids_to_delete_list.append(99999)

             print(f"\nAttempting to delete records with IDs: {ids_to_delete_list}")
             success, msg = delete_history_records(ids_to_delete_list)
             print(f"Deletion result: {success}, Message: {msg}")

             print("\nFetching history again...")
             history_data_after = get_all_history()
             print(f"Found {len(history_data_after)} records after deletion.")
        else:
             print("Not enough records to test deletion.")
    else:
        print("No history found or error fetching.")
    print("--- Test Finished ---")