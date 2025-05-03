# data/augmented/augment_data.py
import os
import cv2
import numpy as np
import random
from tqdm import tqdm
import sys
import time # Thêm để đo thời gian

# --- Thêm thư mục gốc ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Import Config và Utils ---
try:
    import config
    from utils.data_loader import load_data_npy
    from utils.data_augmentation import augment_image
    from tensorflow.keras.utils import to_categorical # type: ignore
    UTILS_AVAILABLE = True
except ImportError as e:
    print(f"ERROR: Cannot import required modules.")
    print(f"Error: {e}")
    UTILS_AVAILABLE = False
    # Định nghĩa hàm giả
    def augment_image(img, **kwargs): return img
    def load_data_npy(path): return None
    def to_categorical(y, num_classes): return None # Hoặc raise lỗi
except Exception as e:
    print(f"ERROR: An unexpected error occurred during imports: {e}")
    UTILS_AVAILABLE = False
    def augment_image(img, **kwargs): return img
    def load_data_npy(path): return None
    def to_categorical(y, num_classes): return None

# --- Cấu hình Augmentation & Oversampling ---
SOURCE_TRAIN_NPY = config.TRAIN_NPY_PATH
AUGMENTED_DATA_DIR = os.path.join(config.DATA_DIR, 'augmented')
TARGET_AUGMENTED_TRAIN_NPY = os.path.join(AUGMENTED_DATA_DIR, 'train_augmented.npz')

MINORITY_CLASS_THRESHOLD = 800
AUGMENTATIONS_PER_MINORITY_SAMPLE = 3

AUGMENT_PARAMS = {
    'rotation': 5,
    'width_shift': 0.05,
    'height_shift': 0.05,
    'zoom': 0.05,
    'brightness': [0.95, 1.05]
}

# Tạo thư mục đích nếu chưa có
os.makedirs(AUGMENTED_DATA_DIR, exist_ok=True)

def main():
    if not UTILS_AVAILABLE:
        print("Exiting due to import errors.")
        return
    if to_categorical is None:
         print("ERROR: tensorflow.keras.utils.to_categorical not available. Cannot proceed.")
         return

    print("--- Starting Offline Data Augmentation & Oversampling (Memory Optimized) ---")
    print(f"Using source: {SOURCE_TRAIN_NPY}")
    print(f"Saving augmented data to: {TARGET_AUGMENTED_TRAIN_NPY}")
    print(f"Augmentation parameters: {AUGMENT_PARAMS}")
    start_time = time.time()

    # 1. Load Original Training Data
    # ================================
    print("\n[Step 1/5] Loading original training data...")
    original_data = load_data_npy(SOURCE_TRAIN_NPY)
    if original_data is None:
        print("ERROR: Could not load original training data. Exiting.")
        return
    train_images_float, train_labels_one_hot = original_data
    num_original_samples = len(train_images_float)
    print(f"Original training samples: {num_original_samples}, dtype: {train_images_float.dtype}")
    train_labels_int = np.argmax(train_labels_one_hot, axis=1)

    # 2. Count Samples per Class & Identify Indices for Augmentation
    # ================================================================
    print("\n[Step 2/5] Analyzing class distribution...")
    unique_classes, counts = np.unique(train_labels_int, return_counts=True)
    class_counts = dict(zip(unique_classes, counts))
    print(f"Class distribution (first 10 classes): {list(class_counts.items())[:10]}...")
    print(f"Minority class threshold: {MINORITY_CLASS_THRESHOLD}")
    print(f"Augmentations per minority sample: {AUGMENTATIONS_PER_MINORITY_SAMPLE}")

    # --- Tối ưu hóa: Tạo danh sách các chỉ số cần xử lý và shuffle nó ---
    print("\n[Step 3/5] Creating and shuffling index mapping...")
    index_mapping = [] # List of tuples: (original_index, is_augmented_copy_flag)
    for i in range(num_original_samples):
        index_mapping.append((i, False)) # Add index for the original image
        # Check if the class is a minority
        if class_counts.get(train_labels_int[i], 0) < MINORITY_CLASS_THRESHOLD:
            # Add indices for augmented copies
            for _ in range(AUGMENTATIONS_PER_MINORITY_SAMPLE):
                index_mapping.append((i, True)) # Mark as an augmented copy

    final_num_samples = len(index_mapping)
    print(f"Total samples after mapping (including augmentations): {final_num_samples}")
    # Shuffle the mapping list IN-PLACE (memory efficient)
    random.shuffle(index_mapping)
    print("Index mapping shuffled.")

    # 3. Process Images based on Shuffled Indices (Augment on the fly)
    # ================================================================
    print("\n[Step 4/5] Processing images and augmenting on-the-fly...")
    # Tạo list mới để chứa kết quả cuối cùng
    final_augmented_images = []
    final_augmented_labels_int = []

    # Giải phóng bộ nhớ của list cũ nếu có thể (dù không cần thiết ở đây nữa)
    # del augmented_images_list
    # del augmented_labels_list

    for orig_idx, is_augmented_copy in tqdm(index_mapping, desc="Processing mapped indices"):
        img = train_images_float[orig_idx] # Get original image
        label = train_labels_int[orig_idx] # Get original label

        if is_augmented_copy:
            # Augment the image
            augmented_img = augment_image(img, **AUGMENT_PARAMS)
            final_augmented_images.append(augmented_img)
        else:
            # Use the original image
            final_augmented_images.append(img)

        final_augmented_labels_int.append(label)

    # === Quan trọng: Giải phóng bộ nhớ không cần thiết trước khi tạo mảng lớn ===
    print("Releasing original data from memory...")
    del train_images_float
    del train_labels_one_hot
    del train_labels_int
    del index_mapping # Không cần list index nữa
    import gc # Gọi Garbage Collector (tùy chọn, Python thường tự làm)
    gc.collect()

    # 4. Convert Final Lists to NumPy Arrays and One-Hot Encode Labels
    # ===================================================================
    print("\n[Step 5/5] Converting final lists to NumPy arrays and saving...")
    try:
        print(f"Attempting to create final image array with shape ({len(final_augmented_images)}, {config.IMG_HEIGHT}, {config.IMG_WIDTH}, 3)")
        augmented_images_np = np.array(final_augmented_images, dtype=np.float32)
        print("Image array created.")

        print(f"Attempting to create final label array with shape ({len(final_augmented_labels_int)},)")
        augmented_labels_int_np = np.array(final_augmented_labels_int, dtype=np.int32)
        print("Integer label array created.")

        # === Giải phóng list Python ngay sau khi chuyển đổi ===
        print("Releasing final lists from memory...")
        del final_augmented_images
        del final_augmented_labels_int
        gc.collect()

        # One-hot encode labels
        print("Converting labels to one-hot encoding...")
        augmented_labels_one_hot_np = to_categorical(augmented_labels_int_np, num_classes=config.NUM_CLASSES)
        print(f"Final augmented data shapes: Images {augmented_images_np.shape}, Labels {augmented_labels_one_hot_np.shape}")

        # === Giải phóng mảng nhãn số nguyên ===
        del augmented_labels_int_np
        gc.collect()

        # 5. Save Augmented Data as .npz
        # ================================
        print(f"Saving augmented data to: {TARGET_AUGMENTED_TRAIN_NPY}")
        np.savez(TARGET_AUGMENTED_TRAIN_NPY, images=augmented_images_np, labels=augmented_labels_one_hot_np)
        end_time = time.time()
        print(f"✅ Augmentation complete. Augmented data saved as .npz. Time taken: {end_time - start_time:.2f} seconds.")

    except MemoryError as e:
         print("\nERROR: Still encountered MemoryError during final array creation or saving.")
         print(f"Error details: {e}")
         print("Consider reducing augmentation amount, processing in smaller batches (more complex), or using a machine with more RAM.")
    except Exception as e:
         print(f"\nERROR: An unexpected error occurred during final conversion or saving: {e}")
         import traceback
         traceback.print_exc()


if __name__ == "__main__":
    main()
