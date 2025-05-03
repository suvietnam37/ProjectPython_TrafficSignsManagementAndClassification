# gui/user_management_window.py

import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QMessageBox, QDialog, QLabel, QLineEdit, QComboBox,
    QDialogButtonBox, QAbstractItemView, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt

# --- Thêm thư mục gốc ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path: sys.path.insert(0, project_root)

# --- Import auth_manager và helpers ---
try:
    from utils import auth_manager
    AUTH_MANAGER_AVAILABLE_UM = True
except ImportError:
    print("UserManagementWindow FATAL ERROR: from utils import auth_manager not found.")
    AUTH_MANAGER_AVAILABLE_UM = False

try:
    from .ui_helpers import show_error_message, show_info_message, ask_confirmation
except ImportError:
    def show_error_message(parent, title, message): QMessageBox.critical(parent, title, message)
    def show_info_message(parent, title, message): QMessageBox.information(parent, title, message)
    def ask_confirmation(parent, title, question): return QMessageBox.question(parent, title, question, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes

# ==============================================================
# == Dialog Thêm/Sửa Người Dùng (Inner Class hoặc file riêng) ==
# ==============================================================
class AddEditUserDialog(QDialog):
    def __init__(self, parent=None, user_data=None):
        super().__init__(parent)
        self.is_edit_mode = user_data is not None
        self.user_id = user_data.get('id') if self.is_edit_mode else None

        self.setWindowTitle("Sửa Người Dùng" if self.is_edit_mode else "Thêm Người Dùng Mới")
        self.setMinimumWidth(350)
        self.setModal(True)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Username
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("Tên đăng nhập:"))
        self.username_input = QLineEdit()
        if self.is_edit_mode:
            self.username_input.setText(user_data.get('username', ''))
            self.username_input.setReadOnly(True) # Không cho sửa username
        else:
             self.username_input.setPlaceholderText("Nhập tên đăng nhập")
        user_layout.addWidget(self.username_input)
        layout.addLayout(user_layout)

        # Password
        pass_layout = QHBoxLayout()
        pass_label_text = "Mật khẩu mới:" if self.is_edit_mode else "Mật khẩu:"
        pass_layout.addWidget(QLabel(pass_label_text))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        if self.is_edit_mode:
            self.password_input.setPlaceholderText("(Để trống nếu không đổi)")
        else:
            self.password_input.setPlaceholderText("Nhập mật khẩu")
        pass_layout.addWidget(self.password_input)
        layout.addLayout(pass_layout)

        # Role
        role_layout = QHBoxLayout()
        role_layout.addWidget(QLabel("Vai trò:"))
        self.role_combo = QComboBox()
        self.role_combo.addItems(auth_manager.VALID_ROLES) # Lấy từ auth_manager
        if self.is_edit_mode:
            current_role = user_data.get('role', 'user')
            if current_role in auth_manager.VALID_ROLES:
                 self.role_combo.setCurrentText(current_role)
        role_layout.addWidget(self.role_combo)
        layout.addLayout(role_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def getUserData(self) -> dict:
        """Lấy dữ liệu từ các input."""
        data = {
            'username': self.username_input.text().strip(),
            'password': self.password_input.text(), # Trả về PW thô, không hash ở đây
            'role': self.role_combo.currentText()
        }
        if self.is_edit_mode:
            data['id'] = self.user_id
        return data

# ======================================
# == Cửa sổ Quản lý Người Dùng Chính ==
# ======================================
class UserManagementWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Quản Lý Người Dùng')
        self.setGeometry(250, 250, 650, 400)
        self.initUI()
        self.loadUsers()

    def initUI(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # --- Layout cho các nút điều khiển ở trên ---
        top_button_layout = QHBoxLayout()
        main_layout.addLayout(top_button_layout)

        self.add_button = QPushButton("Thêm Người Dùng Mới")
        self.add_button.clicked.connect(self.addUser)
        top_button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Sửa Người Dùng")
        self.edit_button.clicked.connect(self.editUser)
        self.edit_button.setEnabled(False) # Kích hoạt khi chọn dòng
        top_button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Xóa Người Dùng")
        self.delete_button.clicked.connect(self.deleteUser)
        self.delete_button.setEnabled(False) # Kích hoạt khi chọn dòng
        top_button_layout.addWidget(self.delete_button)

        top_button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.refresh_button = QPushButton("Làm Mới Danh Sách")
        self.refresh_button.clicked.connect(self.loadUsers)
        top_button_layout.addWidget(self.refresh_button)

        self.close_button = QPushButton("Đóng")
        self.close_button.clicked.connect(self.close)
        top_button_layout.addWidget(self.close_button)

        # --- Bảng Hiển Thị Người Dùng ---
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(4) # ID, Username, Role, Created At
        self.user_table.setHorizontalHeaderLabels(['ID', 'Tên đăng nhập', 'Vai trò', 'Ngày tạo'])
        self.user_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.user_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.user_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection) # Chỉ chọn 1 dòng để sửa/xóa
        self.user_table.verticalHeader().setVisible(False) # Ẩn header dọc (số dòng)

        header = self.user_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Username
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Role
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Created At

        # Kích hoạt nút Sửa/Xóa khi chọn dòng
        self.user_table.itemSelectionChanged.connect(self.updateButtonStates)

        main_layout.addWidget(self.user_table)

        # --- Vô hiệu hóa nếu auth_manager không có ---
        if not AUTH_MANAGER_AVAILABLE_UM:
            self.add_button.setEnabled(False)
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.refresh_button.setEnabled(False)
            self.user_table.setEnabled(False)
            show_error_message(self, "Lỗi Hệ Thống", "Không thể tải auth_manager.\nChức năng quản lý người dùng không khả dụng.")

    def updateButtonStates(self):
        """Kích hoạt/Vô hiệu hóa nút Sửa/Xóa dựa trên lựa chọn."""
        selected_rows = self.user_table.selectionModel().selectedRows()
        enable = len(selected_rows) == 1 # Chỉ kích hoạt nếu chọn đúng 1 dòng
        self.edit_button.setEnabled(enable)
        self.delete_button.setEnabled(enable)

    def loadUsers(self):
        """Tải danh sách người dùng từ auth_manager và hiển thị."""
        if not AUTH_MANAGER_AVAILABLE_UM: return

        print("Loading users...")
        self.user_table.setRowCount(0) # Xóa bảng cũ
        users = auth_manager.list_users()

        if not users:
            print("No users found or error listing users.")
            # Có thể hiển thị thông báo trong bảng
            return

        self.user_table.setRowCount(len(users))
        for row_idx, user_dict in enumerate(users):
            item_id = QTableWidgetItem(str(user_dict.get('id', '')))
            item_username = QTableWidgetItem(user_dict.get('username', 'N/A'))
            item_role = QTableWidgetItem(user_dict.get('role', 'N/A'))
            item_created = QTableWidgetItem(user_dict.get('created_at', 'N/A'))

            # Căn giữa ID và Role
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_role.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_created.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.user_table.setItem(row_idx, 0, item_id)
            self.user_table.setItem(row_idx, 1, item_username)
            self.user_table.setItem(row_idx, 2, item_role)
            self.user_table.setItem(row_idx, 3, item_created)
        print(f"Loaded {len(users)} users into table.")
        self.updateButtonStates() # Cập nhật trạng thái nút sau khi load

    def addUser(self):
        """Mở dialog để thêm người dùng mới."""
        dialog = AddEditUserDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            user_data = dialog.getUserData()
            username = user_data['username']
            password = user_data['password']
            role = user_data['role']

            if not password: # Mật khẩu là bắt buộc khi thêm mới
                show_error_message(self, "Lỗi", "Mật khẩu không được để trống khi thêm người dùng mới.")
                return

            success, message = auth_manager.add_user(username, password, role)
            if success:
                show_info_message(self, "Thành công", message)
                self.loadUsers() # Tải lại danh sách
            else:
                show_error_message(self, "Thêm Thất Bại", message)

    def editUser(self):
        """Mở dialog để sửa người dùng đã chọn."""
        selected_rows = self.user_table.selectionModel().selectedRows()
        if not selected_rows:
            show_warning_message(self, "Chưa chọn", "Vui lòng chọn một người dùng để sửa.")
            return

        selected_row_index = selected_rows[0].row()
        user_id_item = self.user_table.item(selected_row_index, 0) # Cột ID
        username_item = self.user_table.item(selected_row_index, 1) # Cột Username
        role_item = self.user_table.item(selected_row_index, 2) # Cột Role

        if not user_id_item: return # Lỗi không lấy được ID
        try:
            user_id = int(user_id_item.text())
            current_data = {
                'id': user_id,
                'username': username_item.text() if username_item else '',
                'role': role_item.text() if role_item else 'user'
            }
        except ValueError:
             show_error_message(self,"Lỗi","Không thể lấy ID người dùng hợp lệ.")
             return

        dialog = AddEditUserDialog(self, user_data=current_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.getUserData()
            new_password = updated_data['password']
            new_role = updated_data['role']
            success_overall = True
            messages = []

            # Cập nhật mật khẩu nếu có nhập
            if new_password:
                print(f"Attempting to update password for user ID {user_id}")
                pw_success, pw_msg = auth_manager.update_user_password(user_id, new_password)
                success_overall &= pw_success
                messages.append(f"Mật khẩu: {pw_msg}")

            # Cập nhật vai trò nếu thay đổi
            if new_role != current_data['role']:
                print(f"Attempting to update role for user ID {user_id} from '{current_data['role']}' to '{new_role}'")
                role_success, role_msg = auth_manager.update_user_role(user_id, new_role)
                success_overall &= role_success
                messages.append(f"Vai trò: {role_msg}")

            if not messages: # Không có gì thay đổi
                 show_info_message(self,"Thông báo","Không có thay đổi nào được thực hiện.")
            elif success_overall:
                show_info_message(self, "Thành công", "\n".join(messages))
                self.loadUsers() # Tải lại
            else:
                show_error_message(self, "Sửa Thất Bại", "\n".join(messages))

    def deleteUser(self):
        """Xóa người dùng đã chọn."""
        selected_rows = self.user_table.selectionModel().selectedRows()
        if not selected_rows:
            show_warning_message(self, "Chưa chọn", "Vui lòng chọn một người dùng để xóa.")
            return

        selected_row_index = selected_rows[0].row()
        user_id_item = self.user_table.item(selected_row_index, 0)
        username_item = self.user_table.item(selected_row_index, 1)

        if not user_id_item: return
        try:
            user_id = int(user_id_item.text())
            username = username_item.text() if username_item else f"ID {user_id}"
        except ValueError:
             show_error_message(self,"Lỗi","Không thể lấy ID người dùng hợp lệ.")
             return

        if ask_confirmation(self, "Xác nhận Xóa", f"Bạn có chắc chắn muốn xóa người dùng '{username}' (ID: {user_id}) không?\nHành động này không thể hoàn tác."):
            print(f"Attempting to delete user ID {user_id} ('{username}')")
            success, message = auth_manager.delete_user(user_id)
            if success:
                show_info_message(self, "Thành công", message)
                self.loadUsers() # Tải lại
            else:
                show_error_message(self, "Xóa Thất Bại", message)

# --- Chạy cửa sổ độc lập để test ---
if __name__ == '__main__':
    if not AUTH_MANAGER_AVAILABLE_UM:
         print("Cannot run UserManagementWindow standalone: auth_manager not available.")
         app_test = QApplication(sys.argv)
         QMessageBox.critical(None, "Lỗi Hệ Thống", "Không thể import auth_manager.\nKhông thể chạy cửa sổ quản lý người dùng.")
         sys.exit(1)

    app = QApplication(sys.argv)
    user_mgmt_win = UserManagementWindow()
    user_mgmt_win.show()
    sys.exit(app.exec())