# data/augmented/augment_data.py
import os
import cv2
import numpy as np
import random
from tqdm import tqdm
import sys
import time
import logging
import gc # Garbage collector

# --- Calculate Project Root ---
# Goes up 3 levels from data/augmented/augment_data.py to reach project root
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
logger_aug = logging.getLogger("AugmentData")
logger_aug.info(f"Project root added to sys.path: {project_root}")

# --- Import Config and Utils ---
UTILS_AVAILABLE = False
CONFIG_LOADED_AUG = False
try:
    import config # NOW this should work
    CONFIG_LOADED_AUG = True
    from utils.data_loader import load_data_npy # Only need npy loader here
    from utils.data_augmentation import augment_image
    # Use TensorFlow's to_categorical directly if installed
    from tensorflow.keras.utils import to_categorical
    UTILS_AVAILABLE = True
    logger_aug.info("Config and utils loaded successfully.")
except ImportError as e:
    logger_aug.error(f"ERROR: Cannot import required modules (config, utils.*, tensorflow). {e}", exc_info=True)
    # Define dummy functions if needed (not recommended for actual run)
    def augment_image(img, **kwargs): return img
    def load_data_npy(path): return None, None
    def to_categorical(y, num_classes): raise ImportError("TensorFlow not available for to_categorical")
except Exception as e:
    logger_aug.error(f"ERROR: An unexpected error occurred during imports: {e}", exc_info=True)

# --- Configuration ---
# Exit early if config failed to load
if not CONFIG_LOADED_AUG:
     logger_aug.critical("Exiting: config.py could not be loaded.")
     sys.exit(1)

# Determine source: Use cleaned data NPY if it exists, otherwise use processed NPY from raw
CLEANED_NPY_PATH = os.path.join(config.PROCESSED_DATA_DIR, "train_cleaned_source.npz") # You might need a script to generate this specifically
PROCESSED_RAW_NPY_PATH = config.TRAIN_NPY_PATH # The one created directly from raw/split by create_npy.py

# Choose the best available source NPY for augmentation
if os.path.exists(config.AUGMENTED_TRAIN_NPY_PATH):
     logger_aug.warning(f"Target augmented file already exists: {config.AUGMENTED_TRAIN_NPY_PATH}. It might be overwritten.")
     # Decide if you want to exit or overwrite. Overwriting is the default here.

# For source, prioritize the standard processed train set unless you have a specific cleaned NPY
SOURCE_TRAIN_NPY_AUG = PROCESSED_RAW_NPY_PATH
# You could add logic here to check for CLEANED_NPY_PATH if you create it
# if os.path.exists(CLEANED_NPY_PATH):
#      SOURCE_TRAIN_NPY_AUG = CLEANED_NPY_PATH
#      logger_aug.info(f"Using cleaned data NPY as source: {SOURCE_TRAIN_NPY_AUG}")
# else:
logger_aug.info(f"Using standard processed train NPY as source: {SOURCE_TRAIN_NPY_AUG}")


AUGMENTED_DATA_DIR = config.AUGMENTED_DATA_DIR
TARGET_AUGMENTED_TRAIN_NPY = config.AUGMENTED_TRAIN_NPY_PATH # Path from config

# Oversampling and Augmentation Parameters
MINORITY_CLASS_THRESHOLD = config.MINORITY_CLASS_THRESHOLD if hasattr(config, 'MINORITY_CLASS_THRESHOLD') else 1000
AUGMENTATIONS_PER_MINORITY_SAMPLE = config.AUGMENTATIONS_PER_MINORITY_SAMPLE if hasattr(config, 'AUGMENTATIONS_PER_MINORITY_SAMPLE') else 2

# Use augmentation params from config if available, else define here
AUGMENT_PARAMS = {
    'rotation': getattr(config,'AUGMENT_PARAMS',{}).get('rotation', 5),
    'width_shift': getattr(config,'AUGMENT_PARAMS',{}).get('width_shift', 0.05),
    'height_shift': getattr(config,'AUGMENT_PARAMS',{}).get('height_shift', 0.05),
    'zoom': getattr(config,'AUGMENT_PARAMS',{}).get('zoom', 0.05),
    'brightness': getattr(config,'AUGMENT_PARAMS',{}).get('brightness', [0.95, 1.05])
}

# Ensure target directory exists
os.makedirs(AUGMENTED_DATA_DIR, exist_ok=True)

# --- Phần còn lại của file (hàm main, etc.) giữ nguyên ---
# ... (Paste the rest of the augment_data.py code here starting from the 'main' function definition)
def main():
    if not UTILS_AVAILABLE:
        logger_aug.error("Exiting due to import errors. Cannot perform augmentation.")
        return
    if not os.path.exists(SOURCE_TRAIN_NPY_AUG):
         logger_aug.error(f"Source NPY file not found: {SOURCE_TRAIN_NPY_AUG}")
         logger_aug.error("Please run the data processing script (create_npy.py) first.")
         return

    logger_aug.info("--- Starting Offline Data Augmentation & Oversampling ---")
    logger_aug.info(f"Source: {SOURCE_TRAIN_NPY_AUG}")
    logger_aug.info(f"Target: {TARGET_AUGMENTED_TRAIN_NPY}")
    logger_aug.info(f"Augmentation parameters: {AUGMENT_PARAMS}")
    logger_aug.info(f"Minority Threshold: {MINORITY_CLASS_THRESHOLD}")
    logger_aug.info(f"Augmentations per Minority Sample: {AUGMENTATIONS_PER_MINORITY_SAMPLE}")
    start_time = time.time()

    # 1. Load Original Training Data (expects processed float data)
    # ============================================================
    logger_aug.info("[Step 1/5] Loading original training data...")
    train_images_float, train_labels_one_hot = load_data_npy(SOURCE_TRAIN_NPY_AUG)
    if train_images_float is None or train_labels_one_hot is None:
        logger_aug.error(f"Could not load data from {SOURCE_TRAIN_NPY_AUG}. Exiting.")
        return

    # Ensure data is float32 and normalized
    if not np.issubdtype(train_images_float.dtype, np.floating):
        logger_aug.warning(f"Source image data type is {train_images_float.dtype}. Converting to float32 and normalizing.")
        train_images_float = train_images_float.astype(np.float32) / 255.0
    elif train_images_float.max() > 1.01: # Check if already normalized
        logger_aug.warning(f"Source image data max value > 1 ({train_images_float.max():.2f}). Re-normalizing.")
        train_images_float = np.clip(train_images_float / 255.0, 0.0, 1.0)
    else:
        # Ensure it's float32 even if already normalized
        train_images_float = train_images_float.astype(np.float32)


    num_original_samples = len(train_images_float)
    logger_aug.info(f"Original training samples: {num_original_samples}, dtype: {train_images_float.dtype}")

    # Ensure labels are one-hot
    if len(train_labels_one_hot.shape) == 1 or train_labels_one_hot.shape[1] == 1:
         logger_aug.warning("Source labels seem to be integers, converting to one-hot.")
         try:
             train_labels_int_source = train_labels_one_hot.flatten().astype(np.int32)
             train_labels_one_hot = to_categorical(train_labels_int_source, num_classes=config.NUM_CLASSES)
         except Exception as e:
              logger_aug.error(f"Failed to convert labels to one-hot: {e}. Exiting.", exc_info=True)
              return
    train_labels_int = np.argmax(train_labels_one_hot, axis=1)


    # 2. Analyze Class Distribution & Prepare Index Mapping
    # ===================================================
    logger_aug.info("[Step 2/5] Analyzing class distribution...")
    unique_classes, counts = np.unique(train_labels_int, return_counts=True)
    class_counts = dict(zip(unique_classes, counts))
    logger_aug.info(f"Class distribution (sample): {list(class_counts.items())[:10]}...")

    logger_aug.info("[Step 3/5] Creating and shuffling index mapping...")
    index_mapping = [] # List of tuples: (original_index, is_augmented_copy_flag)
    for i in range(num_original_samples):
        index_mapping.append((i, False)) # Original image index
        label = train_labels_int[i]
        if class_counts.get(label, 0) < MINORITY_CLASS_THRESHOLD:
            for _ in range(AUGMENTATIONS_PER_MINORITY_SAMPLE):
                index_mapping.append((i, True)) # Index for an augmented copy

    final_num_samples = len(index_mapping)
    logger_aug.info(f"Target samples after mapping (original + augmentations): {final_num_samples}")
    random.shuffle(index_mapping)
    logger_aug.info("Index mapping shuffled.")


    # 3. Process Images and Augment (Memory Optimized)
    # ================================================
    logger_aug.info("[Step 4/5] Processing images and augmenting...")
    # Pre-allocate NumPy arrays if possible
    img_h, img_w, img_c = config.IMG_HEIGHT, config.IMG_WIDTH, 3
    dtype_img = np.float32
    dtype_lbl = np.int32 # Store integer labels first

    try:
        # Attempt pre-allocation
        logger_aug.info(f"Attempting to pre-allocate arrays: images=({final_num_samples}, {img_h}, {img_w}, {img_c}), labels=({final_num_samples},)")
        final_images_np = np.empty((final_num_samples, img_h, img_w, img_c), dtype=dtype_img)
        final_labels_int_np = np.empty((final_num_samples,), dtype=dtype_lbl)
        pre_allocated = True
    except MemoryError:
        logger_aug.warning("MemoryError during pre-allocation. Falling back to list append method.")
        final_images_np = [] # Use lists as fallback
        final_labels_int_np = []
        pre_allocated = False
        gc.collect() # Try to free memory

    write_index = 0 # Keep track of where to write in pre-allocated array

    # --- Main Processing Loop ---
    for orig_idx, is_augmented_copy in tqdm(index_mapping, desc="Augmenting"):
        # Get original image and label
        img = train_images_float[orig_idx]
        label = train_labels_int[orig_idx]

        if is_augmented_copy:
            augmented_img = augment_image(img, **AUGMENT_PARAMS)
            target_image = augmented_img
        else:
            target_image = img # Use original

        # Store image and label
        if pre_allocated:
            final_images_np[write_index] = target_image
            final_labels_int_np[write_index] = label
        else:
            final_images_np.append(target_image)
            final_labels_int_np.append(label)

        write_index += 1

    logger_aug.info("Image processing and augmentation loop finished.")

    # --- Release Original Data ---
    logger_aug.info("Releasing original data from memory...")
    del train_images_float
    del train_labels_one_hot
    del train_labels_int
    del index_mapping
    gc.collect()

    # 4. Convert to NumPy (if using lists) and One-Hot Encode
    # ======================================================
    logger_aug.info("[Step 5/5] Finalizing arrays and saving...")
    try:
        if not pre_allocated:
             logger_aug.info("Converting appended lists to NumPy arrays...")
             final_images_np = np.array(final_images_np, dtype=dtype_img)
             final_labels_int_np = np.array(final_labels_int_np, dtype=dtype_lbl)
             logger_aug.info("List to NumPy conversion complete.")
             gc.collect() # Collect memory from lists

        # --- One-Hot Encode Labels ---
        logger_aug.info("Converting integer labels to one-hot encoding...")
        if not isinstance(final_labels_int_np, np.ndarray): # Check needed if fallback occurred
             final_labels_int_np = np.array(final_labels_int_np, dtype=dtype_lbl)

        final_labels_one_hot_np = to_categorical(final_labels_int_np, num_classes=config.NUM_CLASSES)
        logger_aug.info(f"Final data shapes: Images={final_images_np.shape}, Labels={final_labels_one_hot_np.shape}")

        # --- Release Integer Labels Array ---
        del final_labels_int_np
        gc.collect()

        # 5. Save Augmented Data
        # ======================
        logger_aug.info(f"Saving augmented data to: {TARGET_AUGMENTED_TRAIN_NPY}")
        np.savez_compressed(TARGET_AUGMENTED_TRAIN_NPY, images=final_images_np, labels=final_labels_one_hot_np) # Use compression
        end_time = time.time()
        logger_aug.info(f"✅ Augmentation complete. Data saved to {TARGET_AUGMENTED_TRAIN_NPY}.")
        logger_aug.info(f"Total time taken: {end_time - start_time:.2f} seconds.")

    except MemoryError as e:
         logger_aug.critical(f"MemoryError during final array conversion or saving: {e}. Try reducing augmentation amount or using more RAM.", exc_info=True)
    except Exception as e:
         logger_aug.critical(f"An unexpected error occurred during finalization or saving: {e}", exc_info=True)


if __name__ == "__main__":
    main()