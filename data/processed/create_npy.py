# data/processed/create_npy.py

import os
import numpy as np
import config
from utils.data_loader import (
    load_train_data,
    load_test_data,
    preprocess_data,
    split_data
)

def main():
    """
    Quy trình xử lý dữ liệu:
    1. Tải dữ liệu thô (train và test).
    2. Chia tập train thành train/validation.
    3. Tiền xử lý (chuẩn hóa, one-hot encoding, lọc nhãn lỗi).
    4. Lưu các tập dữ liệu đã xử lý thành file .npz.
    """
    print("--- Starting Data Processing ---")

    # Step 1: Load raw training data
    print("\n[Step 1/4] Loading raw training data...")
    train_images_raw, train_labels_raw = load_train_data(
        config.TRAIN_DATA_SOURCE_DIR,
        config.IMG_HEIGHT, config.IMG_WIDTH, config.NUM_CLASSES
    )
    if train_images_raw is None or train_labels_raw is None:
        print("ERROR: Failed to load training data. Exiting.")
        return

    # Step 2: Load raw test data
    print("\n[Step 2/4] Loading raw test data...")
    test_images_raw, test_labels_raw = load_test_data(
        config.TEST_DATA_DIR, config.TEST_CSV_PATH,
        config.IMG_HEIGHT, config.IMG_WIDTH
    )
    if test_images_raw is None or test_labels_raw is None:
        print("ERROR: Failed to load test data. Exiting.")
        return

    print("\nRaw data shapes:")
    print(f"  Train images: {train_images_raw.shape}, Train labels: {train_labels_raw.shape}")
    print(f"  Test images: {test_images_raw.shape}, Test labels: {test_labels_raw.shape}")

    # Step 3: Split training data
    print(f"\n[Step 3/4] Splitting training data (Validation ratio: {config.VAL_SPLIT_RATIO})...")
    train_img_split, val_img_split, train_lbl_split_int, val_lbl_split_int = split_data(
        train_images_raw,
        train_labels_raw,
        test_size=config.VAL_SPLIT_RATIO,
        random_state=42
    )

    print("\nData shapes after splitting:")
    print(f"  Train: {train_img_split.shape}, {train_lbl_split_int.shape}")
    print(f"  Val: {val_img_split.shape}, {val_lbl_split_int.shape}")

    # Step 4: Preprocess all datasets (including label validation inside)
    print("\n[Step 4/4] Preprocessing data (Normalization and One-Hot Encoding)...")

    print("  Preprocessing training set...")
    train_images, train_labels = preprocess_data(train_img_split, train_lbl_split_int, config.NUM_CLASSES)

    print("  Preprocessing validation set...")
    val_images, val_labels = preprocess_data(val_img_split, val_lbl_split_int, config.NUM_CLASSES)

    print("  Preprocessing test set...")
    test_images, test_labels = preprocess_data(test_images_raw, test_labels_raw, config.NUM_CLASSES)

    # Save processed data using .npz
    print("\n[Final Step] Saving processed data to .npz files...")
    try:
        os.makedirs(config.PROCESSED_DATA_DIR, exist_ok=True)
        print(f"  Directory ensured: {config.PROCESSED_DATA_DIR}")
    except OSError as e:
        print(f"ERROR: Could not create directory {config.PROCESSED_DATA_DIR}. Reason: {e}")
        return

    try:
        np.savez(config.TRAIN_NPY_PATH, images=train_images, labels=train_labels)
        print(f"  Saved train data to {config.TRAIN_NPY_PATH}")

        np.savez(config.VAL_NPY_PATH, images=val_images, labels=val_labels)
        print(f"  Saved val data to {config.VAL_NPY_PATH}")

        np.savez(config.TEST_NPY_PATH, images=test_images, labels=test_labels)
        print(f"  Saved test data to {config.TEST_NPY_PATH}")
    except Exception as e:
        print(f"ERROR: Failed to save .npz files. Reason: {e}")

    print("\n--- Data Processing Finished ---")

if __name__ == "__main__":
    main()
