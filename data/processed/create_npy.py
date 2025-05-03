# data/processed/create_npy.py
import os
import numpy as np
import sys
import logging
import gc

# --- Calculate Project Root ---
# Goes up 3 levels from data/processed/create_npy.py to reach project root
try:
    current_script_path = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
except NameError:
    project_root = os.path.abspath(os.path.join(os.getcwd(), '../..')) # Fallback

# --- Add project root to sys.path ---
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger_create = logging.getLogger("CreateNPY")
logger_create.info(f"Project root added to sys.path: {project_root}") # Log path addition

# --- Import Config and Utils ---
UTILS_AVAILABLE_CREATE = False
try:
    import config # Now this should work
    from utils.data_loader import (
        load_train_data,
        load_test_data,
        preprocess_data,
        split_data
    )
    UTILS_AVAILABLE_CREATE = True
    logger_create.info("Config and data_loader imported successfully.")
except ImportError as e:
    logger_create.error(f"ERROR: Cannot import required modules (config, utils.data_loader). {e}", exc_info=True)
    # Exit if essential imports fail
    sys.exit(f"Exiting: Failed to import {e}")
except Exception as e:
     logger_create.error(f"ERROR: Unexpected error during imports: {e}", exc_info=True)
     sys.exit("Exiting: Unexpected import error.")


# --- Phần còn lại của file (hàm main, etc.) giữ nguyên ---
# ... (Paste the rest of the create_npy.py code here starting from the 'main' function definition)
def main():
    """
    Processes raw or cleaned data:
    1. Loads raw/cleaned training data.
    2. Loads raw test data.
    3. Splits training data into training and validation sets.
    4. Preprocesses all sets (normalization, one-hot encoding).
    5. Saves the final train, validation, and test sets as compressed .npz files.
    """
    if not UTILS_AVAILABLE_CREATE:
        logger_create.error("Exiting: Essential utils were not loaded.") # Should have exited above, but double-check
        return

    logger_create.info("--- Starting Data Processing (Train/Val/Test Set Creation) ---")
    # Determine source directory for training data based on config
    train_source_dir = config.TRAIN_DATA_SOURCE_DIR
    logger_create.info(f"Using training data source: {train_source_dir}")

    # Check if source directory exists
    if not os.path.isdir(train_source_dir):
         logger_create.error(f"Training data source directory not found: {train_source_dir}")
         logger_create.error("Please ensure the directory exists and contains the GTSRB Train subfolders, or run the cleaning script if using cleaned data.")
         return

    # Step 1: Load Training Data (from specified source)
    # ==================================================
    logger_create.info("[Step 1/4] Loading training data...")
    train_images_raw, train_labels_raw = load_train_data(
        train_source_dir,
        config.IMG_HEIGHT, config.IMG_WIDTH, config.NUM_CLASSES
    )
    if train_images_raw is None or train_labels_raw is None:
        logger_create.error(f"Failed to load training data from {train_source_dir}. Exiting.")
        return
    logger_create.info(f"Loaded {len(train_images_raw)} training images.")

    # Step 2: Load Test Data (always from raw Test dir)
    # ==============================================
    logger_create.info("[Step 2/4] Loading raw test data...")
    if not os.path.isdir(config.TEST_DATA_DIR) or not os.path.isfile(config.TEST_CSV_PATH):
         logger_create.error(f"Test data directory ({config.TEST_DATA_DIR}) or CSV ({config.TEST_CSV_PATH}) not found.")
         logger_create.error("Please ensure the raw GTSRB Test data and its CSV file are correctly placed.")
         del train_images_raw, train_labels_raw; gc.collect()
         return

    test_images_raw, test_labels_raw = load_test_data(
        config.TEST_DATA_DIR, config.TEST_CSV_PATH,
        config.IMG_HEIGHT, config.IMG_WIDTH
    )
    if test_images_raw is None or test_labels_raw is None:
        logger_create.error("Failed to load test data. Exiting.")
        # Clean up loaded train data if test loading fails
        del train_images_raw, train_labels_raw
        gc.collect()
        return
    logger_create.info(f"Loaded {len(test_images_raw)} test images.")

    logger_create.info("Raw data shapes:")
    logger_create.info(f"  Train images: {train_images_raw.shape}, Train labels: {train_labels_raw.shape}")
    logger_create.info(f"  Test images: {test_images_raw.shape}, Test labels: {test_labels_raw.shape}")

    # Step 3: Split Training Data into Train/Validation
    # =================================================
    logger_create.info(f"[Step 3/4] Splitting training data (Validation ratio: {config.VAL_SPLIT_RATIO})...")
    split_result = split_data(
        train_images_raw,
        train_labels_raw,
        test_size=config.VAL_SPLIT_RATIO,
        random_state=42 # for reproducibility
    )
    if split_result[0] is None: # Check if split_data returned None tuple
         logger_create.error("Failed to split training data. Check previous logs for errors (e.g., insufficient samples for stratification). Exiting.")
         del train_images_raw, train_labels_raw, test_images_raw, test_labels_raw; gc.collect()
         return
    train_img_split, val_img_split, train_lbl_split, val_lbl_split = split_result

    logger_create.info("Data shapes after splitting:")
    logger_create.info(f"  New Train: Images={train_img_split.shape}, Labels={train_lbl_split.shape}")
    logger_create.info(f"  Validation: Images={val_img_split.shape}, Labels={val_lbl_split.shape}")

    # --- Release original full training set from memory ---
    del train_images_raw, train_labels_raw
    gc.collect()
    logger_create.info("Released original raw training data from memory.")


    # Step 4: Preprocess all Datasets
    # =================================
    logger_create.info("[Step 4/4] Preprocessing datasets (Normalization & One-Hot Encoding)...")
    try:
        logger_create.info("  Preprocessing training set...")
        train_images, train_labels = preprocess_data(train_img_split, train_lbl_split, config.NUM_CLASSES)
        if train_images is None: raise ValueError("Preprocessing failed for training set.")
        del train_img_split, train_lbl_split; gc.collect() # Free memory

        logger_create.info("  Preprocessing validation set...")
        val_images, val_labels = preprocess_data(val_img_split, val_lbl_split, config.NUM_CLASSES)
        if val_images is None: raise ValueError("Preprocessing failed for validation set.")
        del val_img_split, val_lbl_split; gc.collect() # Free memory

        logger_create.info("  Preprocessing test set...")
        test_images, test_labels = preprocess_data(test_images_raw, test_labels_raw, config.NUM_CLASSES)
        if test_images is None: raise ValueError("Preprocessing failed for test set.")
        del test_images_raw, test_labels_raw; gc.collect() # Free memory

        logger_create.info("Final processed data shapes:")
        logger_create.info(f"  Train: Images={train_images.shape}, Labels={train_labels.shape}, DType={train_images.dtype}")
        logger_create.info(f"  Val:   Images={val_images.shape}, Labels={val_labels.shape}, DType={val_images.dtype}")
        logger_create.info(f"  Test:  Images={test_images.shape}, Labels={test_labels.shape}, DType={test_images.dtype}")

    except Exception as e:
        logger_create.error(f"Error during preprocessing: {e}", exc_info=True)
        return

    # Step 5: Save Processed Data
    # ============================
    logger_create.info("[Final Step] Saving processed data to compressed .npz files...")
    target_dir = config.PROCESSED_DATA_DIR
    train_path = config.TRAIN_NPY_PATH # Path for the *final* training set (post-split)
    val_path = config.VAL_NPY_PATH
    test_path = config.TEST_NPY_PATH

    try:
        os.makedirs(target_dir, exist_ok=True)
        logger_create.info(f"Ensured output directory exists: {target_dir}")
    except OSError as e:
        logger_create.error(f"Could not create directory {target_dir}. Reason: {e}")
        return

    try:
        logger_create.info(f"Saving training data to {train_path}...")
        np.savez_compressed(train_path, images=train_images, labels=train_labels)
        del train_images, train_labels; gc.collect() # Free memory after saving

        logger_create.info(f"Saving validation data to {val_path}...")
        np.savez_compressed(val_path, images=val_images, labels=val_labels)
        del val_images, val_labels; gc.collect()

        logger_create.info(f"Saving test data to {test_path}...")
        np.savez_compressed(test_path, images=test_images, labels=test_labels)
        del test_images, test_labels; gc.collect()

        logger_create.info("✅ Successfully saved train, validation, and test sets.")

    except Exception as e:
        logger_create.error(f"Failed to save .npz files. Reason: {e}", exc_info=True)

    logger_create.info("--- Data Processing Finished ---")

if __name__ == "__main__":
    main()