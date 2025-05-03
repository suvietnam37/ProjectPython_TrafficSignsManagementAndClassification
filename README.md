# Dự án Nhận Dạng Biển Báo Giao Thông GTSRB

## Tổng Quan

Dự án này thực hiện một hệ thống nhận dạng Biển Báo Giao Thông Đức (từ bộ dữ liệu GTSRB) sử dụng Mạng Nơ-ron Tích chập (CNN) được xây dựng bằng TensorFlow/Keras. Hệ thống bao gồm:

*   **Xử lý Dữ liệu:** Các script để làm sạch, tăng cường và xử lý bộ dữ liệu GTSRB.
*   **Huấn luyện Mô hình:** Các script để huấn luyện và đánh giá mô hình CNN.
*   **API Backend:** Một backend FastAPI để cung cấp mô hình đã huấn luyện, cho phép tải ảnh lên để dự đoán.
*   **GUI Desktop:** Giao diện người dùng đồ họa dựa trên PyQt6 để tương tác với hệ thống, bao gồm dự đoán ảnh, quản lý người dùng, xem lịch sử và cấu hình cài đặt.
*   **Cơ sở dữ liệu:** Database SQLite để lưu trữ lịch sử dự đoán và thông tin đăng nhập người dùng.
*   **Module Quản lý:** Bao gồm quản lý người dùng, quản lý nhân viên (ví dụ) và quản lý thông tin biển báo.

## Cấu Trúc Dự Án

GTSRB_Project/
│
├── api/                     # API Backend (FastAPI)
│   ├── routes/              # Định nghĩa các API endpoints
│   │   ├── __init__.py
│   │   └── predict.py       # Endpoint nhận ảnh và dự đoán Top-N (đã cập nhật ngưỡng)
│   ├── __init__.py
│   └── app.py               # File khởi tạo ứng dụng FastAPI (đã cập nhật health check)
│
├── data/                    # Xử lý và lưu trữ dữ liệu
│   ├── raw/                 # Dữ liệu gốc GTSRB
│   │   └── GTSRB/ (...)
│   ├── cleaned/             # Dữ liệu sau khi làm sạch
│   │   ├── __init__.py
│   │   ├── clean_data.py    # Script làm sạch dữ liệu (mờ, nhỏ)
│   │   └── GTSRB/ (...)     # Dữ liệu train đã làm sạch
│   ├── augmented/           # Dữ liệu sau khi tăng cường
│   │   ├── __init__.py
│   │   ├── augment_data.py  # Script tăng cường và cân bằng lớp (oversampling)
│   │   └── train_augmented.npz # File dữ liệu tăng cường (được tạo bởi augment_data.py)
│   └── processed/           # Dữ liệu đã xử lý cuối cùng (dạng .npz)
│       ├── __init__.py
│       ├── create_npy.py    # Script tạo file .npz từ cleaned hoặc raw data
│       ├── train.npz        # Dữ liệu train đã xử lý (từ create_npy.py, chưa tăng cường)
│       ├── test.npz         # Dữ liệu test đã xử lý (từ create_npy.py)
│       └── val.npz          # Dữ liệu validation đã xử lý (từ create_npy.py)
│
├── database/                # Quản lý cơ sở dữ liệu SQLite
│   ├── __init__.py
│   ├── database_setup.py    # (U) Script tạo DB và các bảng (history, users, employees, traffic_signs)
│   ├── database_manager.py  # (U) Hàm quản lý bảng history (get, delete)
│   ├── data_exporter.py     # Script xuất lịch sử ra CSV
│   └── history.db           # File database SQLite (được tạo/cập nhật tự động)
│
├── gui/                     # Giao diện Người dùng (PyQt6)
│   ├── assets/              # Tài nguyên cho GUI (ảnh mẫu, icon...)
│   │   └── class_images/    # Chứa ảnh mẫu cho từng lớp (0.png, 1.png, ...)
│   ├── dialogs/             # (+) Thư mục chứa các cửa sổ Dialog con
│   │   ├── __init__.py
│   │   ├── add_edit_user_dialog.py      # (+) Dialog thêm/sửa User
│   │   └── add_edit_employee_dialog.py  # (+) Dialog thêm/sửa Employee
│   ├── __init__.py
│   ├── main_hub_window.py   # (U) Cửa sổ Hub chính (layout mới, QStackedWidget)
│   ├── login_window.py      # (U) Cửa sổ đăng nhập (xử lý logout)
│   ├── recognition_window.py # (U) Widget Nhận diện (trước là cửa sổ riêng)
│   ├── history_management_window.py # (U) Widget Quản lý Lịch sử (trước là history_window)
│   ├── user_management_window.py  # (U) Widget Quản lý Người dùng (trước là cửa sổ riêng)
│   ├── employee_management_window.py # (+) Widget Quản lý Nhân viên (MỚI)
│   ├── sign_management_window.py   # (+) Widget Quản lý Biển báo (MỚI)
│   ├── settings_window.py   # (U) Widget Cài đặt (trước là cửa sổ riêng)
│   ├── upload_window.py     # Dialog chọn file ảnh (ít thay đổi)
│   ├── result_window.py     # Dialog hiển thị kết quả Top-N (ít thay đổi)
│   └── ui_helpers.py        # Hàm tiện ích cho GUI (message box, scale ảnh)
│
├── logs/                    # Thư mục chứa file log (được tạo khi chạy)
│   ├── gtsrb_app.log        # Log từ ứng dụng GUI
│   └── fit/                 # Log từ TensorBoard trong quá trình training
│       └── (Thư mục theo timestamp)
│
├── models/                  # Định nghĩa kiến trúc và lưu model huấn luyện
│   ├── __init__.py
│   ├── model_cnn.py         # File chứa hàm xây dựng mô hình CNN (basic, improved)
│   └── gtsrb_cnn_improved_best.keras # File model đã huấn luyện (được tạo sau khi train)
│   └── training_history...json # File lưu lịch sử huấn luyện (được tạo sau train)
│   └── confusion_matrix...png  # Ảnh ma trận nhầm lẫn (tạo sau test)
│   └── test_classification_report...txt # Report đánh giá (tạo sau test)
│
├── tests/                   # Các bài kiểm thử (CẦN CẬP NHẬT LỚN)
│   ├── test_data/           # Dữ liệu giả dùng cho testing
│   │   └── sample_sign_e2e.png # Ảnh ví dụ cho E2E test
│   ├── __init__.py
│   ├── test_data_loader.py  # <<< Cần review/cập nhật
│   ├── test_model.py        # <<< Ít ảnh hưởng, test việc build model
│   ├── test_api.py          # <<< Cần review/cập nhật health check, response format
│   ├── test_gui.py          # <<< CẦN VIẾT LẠI HOÀN TOÀN cho cấu trúc widget mới
│   ├── test_auth_manager.py # (+) NÊN THÊM test cho auth_manager
│   ├── test_employee_manager.py # (+) NÊN THÊM test cho module mới
│   ├── test_sign_info_manager.py # (+) NÊN THÊM test cho module mới
│   └── test_end_to_end.py   # <<< Cần review/cập nhật (hiện chỉ test API)
│
├── training/                # Scripts cho việc huấn luyện và đánh giá
│   ├── __init__.py
│   ├── train_model.py       # Script chính để huấn luyện (đã cập nhật dùng augmented data, callbacks)
│   ├── test_model.py        # Script đánh giá trên tập test (đã cập nhật dùng metrics, plot)
│   └── validate_model.py    # Script đánh giá trên tập validation (đã cập nhật)
│
├── utils/                   # Các hàm tiện ích tái sử dụng
│   ├── __init__.py
│   ├── auth_manager.py      # (U) Xử lý logic xác thực và CRUD người dùng
│   ├── employee_manager.py  # (+) Logic CRUD nhân viên (MỚI)
│   ├── sign_info_manager.py # (+) Logic quản lý thông tin biển báo (MỚI)
│   ├── data_loader.py       # Hàm tải và tiền xử lý dữ liệu
│   ├── config_loader.py     # Hàm tải/lưu cấu hình từ settings.json
│   ├── model_utils.py       # Hàm lưu/tải model, history
│   ├── metrics.py           # Hàm tính toán các chỉ số đánh giá
│   ├── visualization.py     # Hàm vẽ đồ thị (history, confusion matrix, samples)
│   └── data_augmentation.py # Hàm thực hiện các phép tăng cường ảnh
│
├── venv/                    # Thư mục môi trường ảo (thường trong .gitignore)
│
├── .gitignore               # (U) Các file/thư mục được Git bỏ qua (cập nhật DB, logs, models)
├── config.py                # (U) File cấu hình trung tâm (thêm hằng số, đường dẫn)
├── main.py                  # (U) Điểm khởi chạy chính cho ứng dụng GUI (xử lý login/logout hub)
├── requirements.txt         # (U) Danh sách thư viện (thêm passlib)
├── README.md                # (U) File hướng dẫn dự án (đã cập nhật/dịch)
└── check_npy.py             # Script kiểm tra file npy (tùy chọn, đã cập nhật)

## Tính Năng

*   **Nhận dạng Biển báo:** Dự đoán loại biển báo giao thông từ ảnh được tải lên bằng mô hình CNN đã huấn luyện.
*   **Dự đoán Top-N:** API và GUI hiển thị N dự đoán có khả năng nhất cùng với điểm tin cậy.
*   **Ngưỡng Tin cậy:** API lọc các dự đoán có độ tin cậy thấp hơn ngưỡng có thể cấu hình.
*   **Tăng cường Dữ liệu:** Tăng cường dữ liệu ngoại tuyến (offline augmentation) để cải thiện độ bền của mô hình.
*   **Xác thực Người dùng:** Hệ thống đăng nhập an toàn sử dụng mã hóa mật khẩu (bcrypt).
*   **Kiểm soát Truy cập Dựa trên Vai trò:** Phân biệt vai trò 'admin' và 'user', cấp quyền khác nhau (ví dụ: chỉ admin mới quản lý được người dùng).
*   **Lịch sử Dự đoán:** Lưu trữ và hiển thị các dự đoán trước đây trong GUI.
*   **Quản lý Người dùng:** (Admin) Thêm, sửa vai trò/mật khẩu và xóa người dùng.
*   **Quản lý Nhân viên:** (Admin - Module Ví dụ) Các thao tác CRUD cơ bản cho hồ sơ nhân viên.
*   **Quản lý Thông tin Biển báo:** (Admin) Xem thông tin biển báo và cập nhật mô tả.
*   **Cài đặt Linh hoạt:** URL API và đường dẫn tài nguyên có thể được cấu hình qua GUI hoặc file `settings.json`.
*   **Thiết kế Module hóa:** Mã nguồn được tổ chức thành các module logic (API, GUI, Utils, Training, etc.).

## Thiết lập và Cài đặt

1.  **Clone Repository:**
    ```bash
    git clone <your-repository-url>
    cd GTSRB_Project
    ```

2.  **Tạo Môi trường ảo:** (Khuyến nghị)
    ```bash
    python -m venv venv
    # Kích hoạt môi trường
    # Windows:
    .\venv\Scripts\activate
    # macOS/Linux:
    source venv/bin/activate
    ```

3.  **Cài đặt Thư viện:**
    ```bash
    pip install -r requirements.txt
    ```
    *Lưu ý: Đảm bảo bạn có phiên bản Python phù hợp (ví dụ: 3.8+) và pip.*
    *Lưu ý: `tensorflow` có thể yêu cầu cài đặt CUDA/cuDNN cụ thể để hỗ trợ GPU.*

4.  **Tải Bộ dữ liệu GTSRB:**
    *   Tải bộ dữ liệu từ nguồn chính thức (ví dụ: [benchmark.ini.rub.de](http://benchmark.ini.rub.de/?section=gtsrb&subsection=dataset)).
    *   Giải nén nội dung vào thư mục `GTSRB_Project/data/raw/`. Cấu trúc nên giống như sau:
        ```
        data/raw/GTSRB/
        ├── Train/
        │   ├── 0/
        │   ├── 1/
        │   └── ... (đến 42)
        ├── Test/
        │   └── GT-final_test.csv
        │   └── 00000.png
        │   └── ...
        └── (Các file khác như Readme.txt)
        ```

5.  **Thiết lập Cơ sở dữ liệu:**
    *   Chạy script thiết lập database một lần để tạo file database (`history.db`) và các bảng cần thiết (history, users, employees, traffic_signs). Script này cũng tạo người dùng admin mặc định.
    ```bash
    python database/database_setup.py
    ```
    *   **LƯU Ý BẢO MẬT QUAN TRỌNG:** Thông tin đăng nhập admin mặc định là `admin`/`admin`. Hãy đăng nhập ngay sau khi thiết lập và đổi mật khẩu thông qua chức năng "Quản Lý Người Dùng".

## Chạy Ứng Dụng

1.  **Xử lý Dữ liệu (Chạy một lần):**
    *   **(Tùy chọn nhưng Khuyến nghị) Làm sạch Dữ liệu:** Tạo bản sao sạch hơn của ảnh.
        ```bash
        python data/cleaned/clean_data.py
        ```
    *   **Tạo file NPY đã xử lý:** Phân chia dữ liệu, tiền xử lý và lưu dưới dạng `.npz`. Script này đọc từ `config.TRAIN_DATA_SOURCE_DIR` (mặc định là dữ liệu đã làm sạch nếu `clean_data.py` đã chạy).
        ```bash
        python data/processed/create_npy.py
        ```
    *   **(Tùy chọn) Tăng cường Dữ liệu:** Tạo dữ liệu huấn luyện đã tăng cường (đọc từ file NPY đã xử lý).
        ```bash
        python data/augmented/augment_data.py
        ```

2.  **Huấn luyện Mô hình (Chạy một lần, hoặc khi cần):**
    *   Huấn luyện mô hình CNN. Script này sẽ sử dụng dữ liệu tăng cường (`train_augmented.npz`) nếu tồn tại, nếu không sẽ dùng dữ liệu huấn luyện đã xử lý (`train.npz`). Mô hình tốt nhất được lưu vào thư mục `models/`.
    ```bash
    python training/train_model.py
    ```
    *   **(Tùy chọn) Đánh giá:** Kiểm tra mô hình đã huấn luyện trên tập validation và tập test.
        ```bash
        python training/validate_model.py
        python training/test_model.py
        ```

3.  **Khởi động API Backend:**
    *   Mở một terminal, kích hoạt môi trường ảo.
    *   Chạy server FastAPI bằng Uvicorn:
    ```bash
    uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload
    ```
    *   `--reload` cho phép tự động tải lại khi code thay đổi (hữu ích khi phát triển).
    *   Truy cập tài liệu API tại `http://127.0.0.1:8000/docs`.

4.  **Chạy Ứng dụng GUI Desktop:**
    *   Mở một terminal *khác*, kích hoạt môi trường ảo.
    *   Chạy script GUI chính:
    ```bash
    python main.py
    ```
    *   Đăng nhập bằng tài khoản (mặc định ban đầu: `admin`/`admin`).

## Cách Sử Dụng

*   **Đăng nhập:** Nhập tên đăng nhập và mật khẩu. Admin mặc định là `admin`/`admin` (hãy đổi ngay!).
*   **Giao diện chính (Hub):** Chọn chức năng từ thanh điều hướng bên trái.
    *   **Nhận Diện:** Tải ảnh lên (kéo thả hoặc duyệt file), nhấp "Bắt đầu Nhận Diện". Kết quả (Top-N) sẽ hiển thị trong một cửa sổ dialog.
    *   **Lịch Sử:** Xem các dự đoán trước đây. Chọn các dòng và nhấp "Xóa" để loại bỏ.
    *   **Quản Lý Người Dùng:** (Chỉ Admin) Thêm người dùng mới, sửa vai trò/mật khẩu, xóa người dùng. *Không thể xóa admin cuối cùng hoặc người dùng đang đăng nhập.*
    *   **Quản Lý Nhân Viên:** (Chỉ Admin) Thao tác CRUD cơ bản cho hồ sơ nhân viên.
    *   **Quản Lý Biển Báo:** (Chỉ Admin) Xem thông tin biển báo và cập nhật mô tả.
    *   **Cài Đặt:** Cấu hình URL API và đường dẫn đến thư mục ảnh mẫu của các loại biển báo.
*   **Đăng xuất:** Nhấp nút "Đăng Xuất" để quay lại màn hình đăng nhập.
*   **Thoát:** Đóng cửa sổ chính.

## TODO / Cải tiến Tiềm năng

*   **Cập nhật Tests:** Viết lại các test trong `tests/` để phù hợp với GUI và module mới. Sử dụng `pytest-qt` để test GUI tốt hơn.
*   **Quản lý Biển báo:** Cho phép admin tải lên/thay thế ảnh mẫu cho biển báo.
*   **Quản lý Nhân viên:** Liên kết nhân viên với tài khoản người dùng một cách chặt chẽ hơn (ví dụ: dùng dropdown trong dialog).
*   **Xử lý Lỗi:** Xử lý lỗi cụ thể hơn và cung cấp phản hồi rõ ràng hơn cho người dùng.
*   **Cấu hình:** Tải `CLASS_NAMES` và các thông tin mô hình khác từ file cấu hình hoặc database thay vì hardcode.
*   **Bảo mật API:** Triển khai xác thực/phân quyền phù hợp cho các endpoint API nếu cần sử dụng ngoài môi trường local.
*   **Hiệu năng:** Tối ưu hóa việc tải dữ liệu và dự đoán mô hình nếu gặp vấn đề về hiệu năng.
*   **Đóng gói:** Tạo file thực thi bằng PyInstaller hoặc các công cụ tương tự.
*   **Đa ngôn ngữ (i18n):** Hỗ trợ nhiều ngôn ngữ cho GUI.

## Giấy phép

(Ghi rõ giấy phép của bạn ở đây, ví dụ: MIT, Apache 2.0, hoặc để trống nếu là dự án riêng)