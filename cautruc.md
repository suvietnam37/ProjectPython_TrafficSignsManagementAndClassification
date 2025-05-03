GTSRB_Project/
│
├── api/                     # API Backend (FastAPI)
│   ├── routes/              # Định nghĩa các API endpoints
│   │   ├── __init__.py
│   │   └── predict.py       # Endpoint nhận ảnh và dự đoán Top-N (đã cập nhật)
│   ├── __init__.py
│   └── app.py               # File khởi tạo ứng dụng FastAPI (đã cập nhật import)
│
├── data/                    # Xử lý và lưu trữ dữ liệu
│   ├── raw/                 # Dữ liệu gốc (cần tải GTSRB vào đây)
│   │   └── GTSRB/
│   │       ├── Train/
│   │       ├── Test/
│   │       │   └── GT-final_test.csv
│   │       └── ...
│   │
│   ├── cleaned/             # Dữ liệu sau khi làm sạch
│   │   ├── __init__.py
│   │   ├── clean_data.py    # Script làm sạch dữ liệu
│   │   └── GTSRB/
│   │       └── Train/
│   │
│   ├── augmented/           # Dữ liệu sau khi tăng cường
│   │   ├── __init__.py
│   │   ├── augment_data.py  # Script tăng cường (đã cập nhật dùng utils)
│   │   └── train_augmented.npz # File dữ liệu tăng cường (đã lưu dạng .npz)
│   │
│   └── processed/           # Dữ liệu đã xử lý cuối cùng
│       ├── __init__.py
│       ├── create_npy.py    # Script tạo file .npz (đã cập nhật)
│       ├── train.npz        # Dữ liệu train đã xử lý (.npz)
│       ├── test.npz         # Dữ liệu test đã xử lý (.npz)
│       └── val.npz          # Dữ liệu validation đã xử lý (.npz)
│
├── database/                # Quản lý cơ sở dữ liệu
│   ├── __init__.py
│   ├── database_setup.py    # Script tạo DB và bảng (history, users) (đã cập nhật)
│   ├── database_manager.py  # Hàm thêm/lấy/XÓA lịch sử (đã cập nhật)
│   ├── data_exporter.py     # Script xuất lịch sử ra CSV
│   └── history.db           # File database SQLite (được tạo tự động)
│
├── gui/                     # Giao diện Người dùng (PyQt6)
│   ├── assets/              # Tài nguyên cho GUI
│   │   └── class_images/    # Chứa ảnh mẫu cho từng lớp (0.png, 1.png, ...)
│   ├── __init__.py
│   ├── main_window.py       # Cửa sổ chính (đã cập nhật nhận user, gọi các cửa sổ khác)
│   ├── login_window.py      # Cửa sổ đăng nhập (đã cập nhật dùng auth_manager)
│   ├── history_window.py    # Cửa sổ xem lịch sử (đã cập nhật thêm nút Xóa, xử lý multi-select)
│   ├── user_management_window.py # <<< CỬA SỔ MỚI: Quản lý người dùng (Thêm/Sửa/Xóa) >>>
│   ├── settings_window.py   # Cửa sổ cài đặt
│   ├── upload_window.py     # Dialog chọn file ảnh
│   ├── result_window.py     # Dialog hiển thị kết quả Top-N (đã cập nhật layout)
│   └── ui_helpers.py        # Hàm tiện ích cho GUI (message box, scale ảnh)
│
├── logs/                    # Thư mục chứa file log (được tạo khi chạy)
│   └── (app.log, ...)
│
├── models/                  # Định nghĩa kiến trúc và lưu model huấn luyện
│   ├── __init__.py
│   ├── model_cnn.py         # File chứa hàm xây dựng mô hình CNN (basic, improved)
│   └── gtsrb_cnn_improved_best.keras # File model đã huấn luyện (được tạo sau khi train)
│
├── tests/                   # Các bài kiểm thử
│   ├── test_data/           # Dữ liệu giả dùng cho testing
│   ├── __init__.py
│   ├── test_data_loader.py
│   ├── test_model.py
│   ├── test_api.py
│   ├── test_gui.py          # (Có thể cần cập nhật/thêm test cho cửa sổ mới)
│   └── test_end_to_end.py   # (Có thể cần cập nhật)
│
├── training/                # Scripts cho việc huấn luyện và đánh giá
│   ├── __init__.py
│   ├── train_model.py       # Script chính để huấn luyện (đã cập nhật)
│   ├── test_model.py        # Script đánh giá trên tập test (đã cập nhật)
│   └── validate_model.py    # Script đánh giá trên tập validation (đã cập nhật)
│
├── utils/                   # Các hàm tiện ích tái sử dụng
│   ├── __init__.py          # <<< ĐẢM BẢO FILE NÀY TỒN TẠI >>> (Đánh dấu là package)
│   ├── auth_manager.py      # <<< FILE MỚI: Xử lý logic xác thực và quản lý người dùng >>>
│   ├── data_loader.py       # Hàm tải và tiền xử lý dữ liệu
│   ├── config_loader.py     # Hàm tải/lưu cấu hình từ settings.json
│   ├── model_utils.py       # Hàm lưu/tải model, history
│   ├── metrics.py           # Hàm tính toán các chỉ số đánh giá
│   ├── visualization.py     # Hàm vẽ đồ thị (history, confusion matrix)
│   └── data_augmentation.py # Hàm thực hiện các phép tăng cường ảnh
│
├── venv/                    # Thư mục môi trường ảo (thường trong .gitignore)
│
├── .gitignore               # Các file/thư mục được Git bỏ qua
├── config.py                # File cấu hình trung tâm (đã cập nhật DATABASE_PATH)
├── main.py                  # Điểm khởi chạy chính cho ứng dụng GUI (đã cập nhật để bắt đầu bằng Login)
├── requirements.txt         # Danh sách thư viện (đã thêm passlib[bcrypt])
├── README.md                # File hướng dẫn dự án (nên cập nhật)
└── check_npy.py             # Script kiểm tra file npy (tùy chọn)