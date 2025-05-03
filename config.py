# config.py
import os

# Đường dẫn gốc của dự án
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Đường dẫn Dữ liệu ---
DATA_DIR = os.path.join(BASE_DIR, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw', 'GTSRB')
TRAIN_DATA_DIR = os.path.join(RAW_DATA_DIR, 'Train')
TEST_DATA_DIR = os.path.join(RAW_DATA_DIR, 'Test')
TEST_CSV_PATH = os.path.join(RAW_DATA_DIR, TEST_DATA_DIR, 'GT-final_test.csv') # File CSV nằm trong thư mục Test
CLEANED_DATA_DIR = os.path.join(DATA_DIR, 'cleaned', 'GTSRB')
CLEANED_TRAIN_DATA_DIR = os.path.join(CLEANED_DATA_DIR, 'Train')
AUGMENTED_DATA_DIR = os.path.join(DATA_DIR, 'augmented')
AUGMENTED_TRAIN_NPY_PATH = os.path.join(AUGMENTED_DATA_DIR, 'train_augmented.npz')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')
TRAIN_NPY_PATH = os.path.join(PROCESSED_DATA_DIR, "train.npz")
VAL_NPY_PATH = os.path.join(PROCESSED_DATA_DIR, "val.npz")
TEST_NPY_PATH = os.path.join(PROCESSED_DATA_DIR, "test.npz")

# --- Đường dẫn Database ---
# <<< ĐẢM BẢO DÒNG NÀY TỒN TẠI >>>
DATABASE_DIR = os.path.join(BASE_DIR, 'database')
DATABASE_PATH = os.path.join(DATABASE_DIR, 'history.db')

# --- Chọn nguồn dữ liệu cho create_npy.py ---
TRAIN_DATA_SOURCE_DIR = CLEANED_TRAIN_DATA_DIR # Mặc định dùng dữ liệu đã làm sạch

# --- Cấu hình Tiền xử lý & Chia dữ liệu ---
IMG_HEIGHT = 32
IMG_WIDTH = 32
NUM_CLASSES = 43
VAL_SPLIT_RATIO = 0.2

# --- Cấu hình Huấn luyện Mô hình ---
MODELS_DIR = os.path.join(BASE_DIR, 'models')
# Đường dẫn lưu file model tốt nhất
MODEL_SAVE_PATH = os.path.join(MODELS_DIR, 'gtsrb_cnn_improved_best.keras')

EPOCHS = 60
BATCH_SIZE = 64
LEARNING_RATE = 0.001

# --- Tham số cho Callbacks ---
EARLY_STOPPING_PATIENCE = 15
LR_PATIENCE = 7
LR_REDUCTION_FACTOR = 0.2
MIN_LR = 1e-6

# --- Đảm bảo thư mục Models và Database tồn tại ---
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(DATABASE_DIR, exist_ok=True) # <<< Thêm dòng này cho chắc chắn >>>

print(f"Config loaded. Project Base Dir: {BASE_DIR}")
print(f"Model save path set to: {MODEL_SAVE_PATH}")
print(f"Database path set to: {DATABASE_PATH}") # <<< Thêm log này để kiểm tra >>>