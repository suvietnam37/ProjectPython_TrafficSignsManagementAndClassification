# utils/auth_manager.py
import sqlite3
import os
from datetime import datetime
from passlib.context import CryptContext
from typing import Tuple, List, Dict, Optional # <<< Đã import các kiểu cần thiết

# --- Cấu hình ---
# Lấy đường dẫn DB từ config nếu được import bởi module khác
try:
    import config
    # Đảm bảo config.py có định nghĩa DATABASE_PATH
    if hasattr(config, 'DATABASE_PATH'):
        AUTH_DB_PATH = config.DATABASE_PATH
    else:
        # Fallback nếu config không có
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        AUTH_DB_PATH = os.path.join(BASE_DIR, 'database', 'history.db')
        print("AuthManager WARNING: config.DATABASE_PATH not found, using default path.")
except (ImportError, AttributeError):
    # Fallback nếu config không import được
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    AUTH_DB_PATH = os.path.join(BASE_DIR, 'database', 'history.db')
    print("AuthManager WARNING: config module not found or lacks DATABASE_PATH, using default path.")


print(f"AuthManager using Database: {AUTH_DB_PATH}")

# Khởi tạo context cho việc hash (chọn thuật toán bcrypt)
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except ImportError:
    print("AuthManager FATAL ERROR: passlib library not found. Please install: pip install passlib[bcrypt]")
    # Có thể raise lỗi ở đây để dừng chương trình nếu passlib là bắt buộc
    raise

VALID_ROLES = ['user', 'admin'] # Các vai trò hợp lệ

def _create_connection():
    """ Tạo kết nối đến database """
    conn = None
    if not os.path.exists(AUTH_DB_PATH):
        print(f"AuthManager DB Error: Database file not found at {AUTH_DB_PATH}")
        return None
    try:
        # isolation_level=None để tự động commit (hoặc nhớ commit thủ công)
        conn = sqlite3.connect(AUTH_DB_PATH)
        conn.row_factory = sqlite3.Row # Trả về kết quả dạng dictionary-like
        return conn
    except sqlite3.Error as e:
        print(f"AuthManager DB Error: {e}")
    return conn

# --- Hashing ---
def hash_password(password: str) -> str:
    """Băm mật khẩu."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Xác minh mật khẩu thô với mật khẩu đã băm."""
    # Thêm kiểm tra đầu vào cơ bản
    if not plain_password or not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        # Log lỗi cẩn thận hơn, có thể là do hash không hợp lệ
        print(f"Error verifying password (potentially invalid hash?): {e}")
        return False

# --- CRUD Operations ---
# <<< Đã sửa kiểu trả về -> Tuple[bool, str] >>>
def add_user(username: str, password: str, role: str = 'user') -> Tuple[bool, str]:
    """Thêm người dùng mới."""
    if role not in VALID_ROLES:
        return False, f"Vai trò không hợp lệ: {role}. Chỉ chấp nhận: {VALID_ROLES}"
    if not username or not password:
        return False, "Tên đăng nhập và mật khẩu không được để trống."

    conn = _create_connection()
    if not conn: return False, "Không thể kết nối database."

    hashed_pw = hash_password(password)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = "INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)"
    try:
        cur = conn.cursor()
        cur.execute(sql, (username, hashed_pw, role, now))
        conn.commit()
        print(f"User '{username}' added successfully with role '{role}'.")
        return True, f"Người dùng '{username}' đã được thêm."
    except sqlite3.IntegrityError: # Lỗi UNIQUE constraint nếu username tồn tại
        print(f"Error adding user: Username '{username}' already exists.")
        return False, f"Tên đăng nhập '{username}' đã tồn tại."
    except sqlite3.Error as e:
        print(f"Database error adding user '{username}': {e}")
        return False, f"Lỗi database khi thêm người dùng: {e}"
    finally:
        if conn: conn.close()

# <<< Đã sửa kiểu trả về -> Optional[Dict] >>>
def get_user_by_username(username: str) -> Optional[Dict]:
    """Lấy thông tin người dùng bằng username."""
    conn = _create_connection()
    if not conn: return None
    sql = "SELECT * FROM users WHERE username = ?"
    try:
        cur = conn.cursor()
        cur.execute(sql, (username,))
        user_row = cur.fetchone()
        # Chuyển sqlite3.Row thành dict tường minh
        return dict(user_row) if user_row else None
    except sqlite3.Error as e:
        print(f"Database error getting user '{username}': {e}")
        return None
    finally:
        if conn: conn.close()

# <<< Đã sửa kiểu trả về -> Optional[Dict] >>>
def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Lấy thông tin người dùng bằng ID."""
    conn = _create_connection()
    if not conn: return None
    sql = "SELECT * FROM users WHERE id = ?"
    try:
        cur = conn.cursor()
        cur.execute(sql, (user_id,))
        user_row = cur.fetchone()
        return dict(user_row) if user_row else None
    except sqlite3.Error as e:
        print(f"Database error getting user ID {user_id}: {e}")
        return None
    finally:
        if conn: conn.close()

# <<< Đã sửa kiểu trả về -> List[Dict] >>>
def list_users() -> List[Dict]:
    """Lấy danh sách tất cả người dùng (không kèm password hash)."""
    conn = _create_connection()
    if not conn: return []
    sql = "SELECT id, username, role, created_at FROM users ORDER BY username"
    try:
        cur = conn.cursor()
        cur.execute(sql)
        # Chuyển đổi từng sqlite3.Row thành dict
        users = [dict(row) for row in cur.fetchall()]
        return users
    except sqlite3.Error as e:
        print(f"Database error listing users: {e}")
        return []
    finally:
        if conn: conn.close()

# <<< Đã sửa kiểu trả về -> Tuple[bool, str] >>>
def update_user_role(user_id: int, new_role: str) -> Tuple[bool, str]:
    """Cập nhật vai trò của người dùng."""
    if new_role not in VALID_ROLES:
        return False, f"Vai trò không hợp lệ: {new_role}"

    conn = _create_connection()
    if not conn: return False, "Không thể kết nối database."
    sql = "UPDATE users SET role = ? WHERE id = ?"
    try:
        cur = conn.cursor()
        cur.execute(sql, (new_role, user_id))
        conn.commit()
        if cur.rowcount == 0:
             return False, f"Không tìm thấy người dùng với ID: {user_id}"
        print(f"Role updated for user ID {user_id} to '{new_role}'.")
        return True, f"Vai trò của người dùng ID {user_id} đã được cập nhật."
    except sqlite3.Error as e:
        print(f"Database error updating role for user ID {user_id}: {e}")
        return False, f"Lỗi database khi cập nhật vai trò: {e}"
    finally:
        if conn: conn.close()

# <<< Đã sửa kiểu trả về -> Tuple[bool, str] >>>
def update_user_password(user_id: int, new_password: str) -> Tuple[bool, str]:
    """Cập nhật mật khẩu của người dùng."""
    if not new_password:
         return False, "Mật khẩu mới không được để trống."
    conn = _create_connection()
    if not conn: return False, "Không thể kết nối database."

    new_hashed_pw = hash_password(new_password)
    sql = "UPDATE users SET password_hash = ? WHERE id = ?"
    try:
        cur = conn.cursor()
        cur.execute(sql, (new_hashed_pw, user_id))
        conn.commit()
        if cur.rowcount == 0:
             return False, f"Không tìm thấy người dùng với ID: {user_id}"
        print(f"Password updated for user ID {user_id}.")
        return True, f"Mật khẩu của người dùng ID {user_id} đã được cập nhật."
    except sqlite3.Error as e:
        print(f"Database error updating password for user ID {user_id}: {e}")
        return False, f"Lỗi database khi cập nhật mật khẩu: {e}"
    finally:
        if conn: conn.close()

# <<< Đã sửa kiểu trả về -> Tuple[bool, str] >>>
def delete_user(user_id: int) -> Tuple[bool, str]:
    """Xóa người dùng."""
    user_to_delete = get_user_by_id(user_id)
    if user_to_delete and user_to_delete['username'] == 'admin':
         all_users = list_users()
         admin_count = sum(1 for u in all_users if u['role'] == 'admin')
         if admin_count <= 1:
              return False, "Không thể xóa người dùng 'admin' cuối cùng."

    conn = _create_connection()
    if not conn: return False, "Không thể kết nối database."
    sql = "DELETE FROM users WHERE id = ?"
    try:
        cur = conn.cursor()
        cur.execute(sql, (user_id,))
        conn.commit()
        if cur.rowcount == 0:
             return False, f"Không tìm thấy người dùng với ID: {user_id}"
        print(f"User ID {user_id} deleted.")
        return True, f"Người dùng ID {user_id} đã được xóa."
    except sqlite3.Error as e:
        print(f"Database error deleting user ID {user_id}: {e}")
        return False, f"Lỗi database khi xóa người dùng: {e}"
    finally:
        if conn: conn.close()

# --- Test block (chỉ chạy khi thực thi trực tiếp) ---
if __name__ == '__main__':
    print("--- Testing Auth Manager (utils/auth_manager.py) ---")
    # Chạy setup để đảm bảo bảng và admin mặc định tồn tại
    # from database.database_setup import setup_database # Import nếu cần chạy setup từ đây
    # setup_database()

    print("\nListing initial users:")
    users = list_users()
    print(users if users else "No users found or DB connection error.")

    print("\nAttempting to add a new user 'testuser':")
    success, msg = add_user("testuser", "testpass123", "user")
    print(f"Result: {success}, Message: {msg}")

    print("\nAttempting to add 'testuser' again (should fail):")
    success, msg = add_user("testuser", "anotherpass")
    print(f"Result: {success}, Message: {msg}")

    print("\nGetting user 'testuser':")
    user = get_user_by_username("testuser")
    if user:
        print(user)
        user_id = user['id']
        print(f"\nVerifying password for 'testuser' (correct: 'testpass123'):")
        is_valid = verify_password("testpass123", user['password_hash'])
        print(f"Verification result (correct): {is_valid}")
        is_valid = verify_password("wrongpass", user['password_hash'])
        print(f"Verification result (incorrect): {is_valid}")

        print(f"\nUpdating role for user ID {user_id} to 'admin':")
        success, msg = update_user_role(user_id, 'admin')
        print(f"Result: {success}, Message: {msg}")
        user_updated = get_user_by_id(user_id)
        print(f"Updated user info: {user_updated}")

        print(f"\nUpdating password for user ID {user_id}:")
        success, msg = update_user_password(user_id, "newpassword456")
        print(f"Result: {success}, Message: {msg}")
        user_updated_pw = get_user_by_id(user_id)
        if user_updated_pw: # Kiểm tra xem có lấy được user sau update không
             print(f"Verifying new password:")
             is_valid = verify_password("newpassword456", user_updated_pw['password_hash'])
             print(f"Verification result (new): {is_valid}")
        else:
             print("Could not retrieve user after password update to verify.")


        print(f"\nDeleting user ID {user_id}:")
        success, msg = delete_user(user_id)
        print(f"Result: {success}, Message: {msg}")
        user_deleted = get_user_by_id(user_id)
        print(f"User after deletion: {user_deleted}")

    else:
        print("User 'testuser' not found, cannot proceed with further tests.")

    print("\n--- Auth Manager Test Finished ---")