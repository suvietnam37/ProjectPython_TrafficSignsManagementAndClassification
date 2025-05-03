# data/cleaned/clean_data.py
import os
import cv2
import numpy as np
import shutil
from tqdm import tqdm # Thư viện tạo thanh tiến trình (pip install tqdm)
import sys
import logging

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger_clean = logging.getLogger("CleanData")

# --- Calculate Project Root ---
# Goes up 3 levels from data/cleaned/clean_data.py to reach project root
try:
    current_script_path = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_script_path)))
    logger_clean.debug(f"Calculated project root: {project_root}")
except NameError:
    # __file__ might not be defined if running in certain environments (like interactive)
    project_root = os.path.abspath(os.path.join(os.getcwd(), '../..')) # Fallback relative to cwd if needed
    logger_clean.warning(f"__file__ not defined, using relative CWD fallback for project root: {project_root}")


# --- Add project root for config import ---
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logger_clean.info(f"Added to sys.path: {project_root}")


# --- Import Config ---
CONFIG_LOADED = False
SOURCE_TRAIN_DIR = None
CLEANED_TRAIN_DIR = None
try:
    import config
    # Use paths from config relative to the project root (BASE_DIR in config.py)
    SOURCE_TRAIN_DIR = config.TRAIN_DATA_DIR
    # Construct cleaned path relative to project's DATA_DIR
    CLEANED_TRAIN_DIR = os.path.join(config.DATA_DIR, 'cleaned', 'GTSRB', 'Train')
    CONFIG_LOADED = True
    logger_clean.info("config.py loaded successfully.")
    logger_clean.info(f"Source directory from config: {SOURCE_TRAIN_DIR}")
    logger_clean.info(f"Target directory constructed: {CLEANED_TRAIN_DIR}")
except ImportError:
    logger_clean.error("ERROR: config.py not found. Please ensure it's in the project root ({project_root}).")
    # Define fallback paths relative to the *calculated* project_root
    SOURCE_TRAIN_DIR = os.path.join(project_root, 'data', 'raw', 'GTSRB', 'Train')
    CLEANED_TRAIN_DIR = os.path.join(project_root, 'data', 'cleaned', 'GTSRB', 'Train')
    logger_clean.warning(f"Warning: Using fallback paths relative to calculated project root:")
    logger_clean.warning(f"  Source: {SOURCE_TRAIN_DIR}")
    logger_clean.warning(f"  Target: {CLEANED_TRAIN_DIR}")
except AttributeError as e:
     logger_clean.error(f"ERROR: Could not find required paths (e.g., TRAIN_DATA_DIR) in config.py: {e}")
     # Define fallbacks again
     SOURCE_TRAIN_DIR = os.path.join(project_root, 'data', 'raw', 'GTSRB', 'Train')
     CLEANED_TRAIN_DIR = os.path.join(project_root, 'data', 'cleaned', 'GTSRB', 'Train')
     logger_clean.warning(f"Warning: Using fallback paths due to missing config attributes.")
     logger_clean.warning(f"  Source: {SOURCE_TRAIN_DIR}")
     logger_clean.warning(f"  Target: {CLEANED_TRAIN_DIR}")


# --- Cleaning Parameters ---
BLUR_THRESHOLD = 100.0
REMOVE_BLURRY = True
MIN_SIZE = (15, 15)

# --- Phần còn lại của file (variance_of_laplacian, clean_dataset, __main__) giữ nguyên ---
# ... (Paste the rest of the clean_data.py code here starting from the function definitions)

def variance_of_laplacian(image):
    """Calculates the variance of the Laplacian, a measure of image focus."""
    if image is None: return 0
    if len(image.shape) == 3: # Convert to grayscale if color
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    # Compute the Laplacian of the grayscale image and then return the focus
    # measure, which is simply the variance of the Laplacian
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def clean_dataset(source_dir, target_dir, blur_threshold, remove_blurry, min_size):
    """
    Scans the source dataset, identifies and optionally removes/skips blurry or small images,
    and copies the clean images to the target directory.
    """
    # Check if source_dir is valid *before* logging parameters based on it
    if not source_dir or not os.path.isdir(source_dir):
        logger_clean.error(f"Source directory is invalid or not found: {source_dir}")
        logger_clean.error("Please ensure the path is correct and the data exists.")
        return # Stop execution if source is invalid

    logger_clean.info("Starting data cleaning process...")
    logger_clean.info(f"Source Directory: {source_dir}")
    logger_clean.info(f"Target Directory: {target_dir}")
    logger_clean.info(f"Blurry Threshold (Laplacian Variance): {blur_threshold}")
    logger_clean.info(f"Remove/Skip Blurry Images: {remove_blurry}")
    logger_clean.info(f"Minimum Image Size (WxH): {min_size}")


    # Handle existing target directory
    if os.path.exists(target_dir):
        logger_clean.warning(f"Target directory {target_dir} already exists.")
        logger_clean.info("Continuing. Existing files might remain if not overwritten.")
    os.makedirs(target_dir, exist_ok=True)

    total_images = 0
    kept_images = 0
    blurry_skipped = 0
    blurry_kept = 0
    small_skipped = 0
    error_skipped = 0

    # Iterate through class directories (e.g., '0', '1', ..., '42')
    class_dirs = [d for d in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir, d))]
    if not class_dirs:
         logger_clean.error(f"No class directories found in source: {source_dir}")
         return

    for class_id in tqdm(class_dirs, desc="Processing Classes"):
        source_class_path = os.path.join(source_dir, class_id)
        target_class_path = os.path.join(target_dir, class_id)
        os.makedirs(target_class_path, exist_ok=True)

        # Iterate through images within the class directory
        image_files = [f for f in os.listdir(source_class_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.ppm'))]
        for img_name in image_files:
            source_img_path = os.path.join(source_class_path, img_name)
            target_img_path = os.path.join(target_class_path, img_name)
            total_images += 1

            try:
                # Read image using OpenCV
                img = cv2.imread(source_img_path)
                if img is None:
                    logger_clean.warning(f"Could not read image (skipping): {source_img_path}")
                    error_skipped += 1
                    continue

                # 1. Check Size
                h, w = img.shape[:2]
                if w < min_size[0] or h < min_size[1]:
                    # logger_clean.debug(f"Image too small ({w}x{h}) (skipping): {source_img_path}")
                    small_skipped += 1
                    continue # Skip small images

                # 2. Check Blurriness
                focus_measure = variance_of_laplacian(img)
                is_blurry = focus_measure < blur_threshold

                # Decide whether to keep the image
                keep_image = True
                if is_blurry:
                    if remove_blurry:
                        # logger_clean.debug(f"Image blurry ({focus_measure:.2f}) (skipping): {source_img_path}")
                        blurry_skipped += 1
                        keep_image = False
                    else:
                        # logger_clean.debug(f"Image blurry ({focus_measure:.2f}) (keeping): {source_img_path}")
                        blurry_kept += 1
                        keep_image = True # Keep but count it

                # Copy if keeping
                if keep_image:
                    shutil.copy2(source_img_path, target_img_path) # copy2 preserves metadata
                    kept_images += 1

            except Exception as e:
                logger_clean.error(f"Error processing image {source_img_path}: {e}", exc_info=True)
                error_skipped += 1

    logger_clean.info("--- Cleaning Summary ---")
    logger_clean.info(f"Total images scanned: {total_images}")
    logger_clean.info(f"Images kept (copied to target): {kept_images}")
    logger_clean.info(f"Blurry images skipped: {blurry_skipped}" if remove_blurry else f"Blurry images found (but kept): {blurry_kept}")
    logger_clean.info(f"Small images skipped (< {min_size[0]}x{min_size[1]}): {small_skipped}")
    logger_clean.info(f"Read/Processing errors (skipped): {error_skipped}")
    logger_clean.info(f"Cleaned data available in: {target_dir}")

if __name__ == "__main__":
    # Check if paths were determined correctly before running clean_dataset
    if SOURCE_TRAIN_DIR and CLEANED_TRAIN_DIR:
         clean_dataset(SOURCE_TRAIN_DIR, CLEANED_TRAIN_DIR, BLUR_THRESHOLD, REMOVE_BLURRY, MIN_SIZE)
    else:
         logger_clean.critical("Could not determine source or target directory. Aborting clean_dataset execution.")