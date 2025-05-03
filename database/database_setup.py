# database/database_setup.py
import sqlite3
import os
from datetime import datetime
# <<< KHÔNG import auth_manager >>>

# --- Xác định đường dẫn đến file database ---
# Lấy thư mục gốc của dự án (đi lên 2 cấp từ database/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_DIR = os.path.join(BASE_DIR, 'database')
DATABASE_PATH = os.path.join(DATABASE_DIR, 'history.db') # Tên file database

# Đảm bảo thư mục database tồn tại
os.makedirs(DATABASE_DIR, exist_ok=True)

def create_connection(db_file):
    """ Tạo kết nối đến file SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"SQLite connection established to {db_file} (Version: {sqlite3.sqlite_version})")
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
    return conn

def create_table(conn, create_table_sql):
    """ Tạo bảng từ câu lệnh create_table_sql """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        # Log một phần của câu lệnh SQL để xác nhận bảng nào đang được tạo
        print(f"Table creation attempted using SQL: {create_table_sql.split('(')[0].strip()}...")
    except sqlite3.Error as e:
        print(f"Error creating table: {e}")

def setup_database():
    """ Thiết lập database: tạo kết nối và các bảng cần thiết """
    print("--- Setting up Database ---")
    print(f"Database file will be at: {DATABASE_PATH}")

    # Câu lệnh SQL để tạo bảng history
    sql_create_history_table = """ CREATE TABLE IF NOT EXISTS history (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        timestamp TEXT NOT NULL,
                                        image_path TEXT NOT NULL,
                                        predicted_class_id INTEGER NOT NULL,
                                        predicted_class_name TEXT NOT NULL,
                                        confidence REAL NOT NULL
                                        -- Tùy chọn: Thêm user_id nếu muốn liên kết với người dùng
                                        -- user_id INTEGER,
                                        -- FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
                                    ); """

    # Câu lệnh SQL để tạo bảng users
    sql_create_users_table = """ CREATE TABLE IF NOT EXISTS users (
                                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                                        username TEXT UNIQUE NOT NULL,
                                        password_hash TEXT NOT NULL,
                                        role TEXT NOT NULL DEFAULT 'user', -- 'user' hoặc 'admin'
                                        created_at TEXT NOT NULL
                                    ); """

    # Tạo kết nối database
    conn = create_connection(DATABASE_PATH)

    # Tạo các bảng nếu kết nối thành công
    if conn is not None:
        print("\nCreating 'history' table (if not exists)...")
        create_table(conn, sql_create_history_table)

        print("\nCreating 'users' table (if not exists)...")
        create_table(conn, sql_create_users_table)

        # --- Tạo admin user mặc định nếu bảng users mới được tạo hoặc trống ---
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]

            if user_count == 0:
                print("\nUsers table is empty. Creating default admin user...")
                try:
                    # <<< Import passlib trực tiếp tại đây >>>
                    from passlib.context import CryptContext
                    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

                    default_admin_username = "admin"
                    # !!! CỰC KỲ QUAN TRỌNG: Đổi mật khẩu này ngay sau lần chạy đầu tiên !!!
                    default_admin_password = "adminpassword"
                    hashed_password = pwd_context.hash(default_admin_password) # <<< Hash trực tiếp
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Thêm admin mặc định vào bảng
                    cursor.execute("""
                        INSERT INTO users (username, password_hash, role, created_at)
                        VALUES (?, ?, ?, ?)
                    """, (default_admin_username, hashed_password, 'admin', now))
                    conn.commit() # Lưu thay đổi
                    print(f"Default admin user '{default_admin_username}' created successfully.")
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    print("!!! PLEASE CHANGE THE DEFAULT ADMIN PASSWORD IMMEDIATELY !!!")
                    print("!!! Use the 'Manage Users' feature after logging in.    !!!")
                    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                except ImportError:
                     print("\nERROR: 'passlib' library not found. Cannot create default admin user.")
                     print("Please install it: pip install passlib[bcrypt]")
                except sqlite3.Error as e:
                     print(f"\nERROR creating default admin user in database: {e}")
            else:
                print(f"\nUsers table already contains {user_count} user(s). Skipping default admin creation.")

        except sqlite3.Error as e:
            print(f"\nERROR checking users table count: {e}")

        # Đóng kết nối
        conn.close()
        print("\nDatabase connection closed.")
    else:
        print("\nError! Cannot create the database connection. Setup failed.")

    print("--- Database Setup Finished ---")

# Chạy hàm setup khi thực thi file này trực tiếp
if __name__ == '__main__':
    setup_database()