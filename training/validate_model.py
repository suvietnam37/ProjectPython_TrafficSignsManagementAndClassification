# training/validate_model.py
import os
import numpy as np
import tensorflow as tf
# --- THAY ĐỔI: Import utils ---
from utils.data_loader import load_data_npy
from utils.model_utils import load_keras_model
import config

def main():
    print("--- Starting Model Evaluation on VALIDATION Set ---")

    # 1. Load Validation Data
    print(f"\n[Step 1/3] Loading validation data from: {config.VAL_NPY_PATH}...")
    val_data = load_data_npy(config.VAL_NPY_PATH)
    if val_data is None: return
    val_images, val_labels_one_hot = val_data
    print(f"  Validation data shapes: Images {val_images.shape}, Labels {val_labels_one_hot.shape}")
    # ... (Đảm bảo float32 giữ nguyên) ...
    if not np.issubdtype(val_images.dtype, np.floating): val_images = val_images.astype(np.float32)
    if not np.issubdtype(val_labels_one_hot.dtype, np.floating): val_labels_one_hot = val_labels_one_hot.astype(np.float32)

    # 2. Load Trained Model
    model_to_load_path = config.MODEL_SAVE_PATH
    print(f"\n[Step 2/3] Loading trained model from: {model_to_load_path}...")
    # --- THAY ĐỔI: Sử dụng load_keras_model từ utils ---
    model = load_keras_model(model_to_load_path)
    if model is None:
        print("Exiting due to model loading failure.")
        return
    print("  Model architecture loaded:")
    model.summary(print_fn=lambda x: print(f"    {x}"))

    # 3. Evaluate Model Performance
    print("\n[Step 3/3] Evaluating model performance on validation set using model.evaluate()...")
    loss, accuracy = -1.0, -1.0
    try:
        loss, accuracy = model.evaluate(val_images, val_labels_one_hot, batch_size=config.BATCH_SIZE, verbose=1)
        print("\n--- Validation Set Evaluation Results ---")
        print(f"  Validation Loss: {loss:.4f}")
        print(f"  Validation Accuracy: {accuracy:.4f} ({accuracy * 100:.2f}%)")
        print("-------------------------------------------")
    except Exception as e:
        print(f"ERROR: An error occurred during model.evaluate() on validation set: {e}")

    print("\n--- Validation Set Evaluation Finished ---")

if __name__ == "__main__":
    # ... (GPU setup giữ nguyên) ...
    gpus = tf.config.experimental.list_physical_devices('GPU')
    if gpus:
        try:
            # ... (set memory growth) ...
            print(f"INFO: Found {len(gpus)} Physical GPU(s). Setting memory growth...")
            for gpu in gpus: tf.config.experimental.set_memory_growth(gpu, True)
        except RuntimeError as e: print(f"ERROR setting memory growth: {e}.")
    else: print("INFO: No GPU found by TensorFlow, using CPU.")
    main()