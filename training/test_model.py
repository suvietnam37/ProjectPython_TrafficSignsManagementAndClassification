# training/test_model.py
import os
import numpy as np
import tensorflow as tf
# --- THAY ĐỔI: Bỏ import keras trực tiếp nếu dùng utils ---
# from tensorflow import keras

# --- Import utils ---
from utils.metrics import calculate_confusion_matrix, get_classification_report
from utils.visualization import plot_confusion_matrix, MATPLOTLIB_AVAILABLE
# --- THAY ĐỔI: Import hàm load model từ utils ---
from utils.model_utils import load_keras_model
# from sklearn.metrics import accuracy_score # Có thể bỏ nếu không cần đối chiếu

# Import các thành phần từ dự án
import config
from utils.data_loader import load_data_npy

def main():
    print("--- Starting Model Evaluation on Test Set ---")

    # 1. Load Test Data
    print("\n[Step 1/4] Loading original test data from .npy file...")
    test_data = load_data_npy(config.TEST_NPY_PATH)
    if test_data is None: return # Lỗi đã được in trong load_data_npy
    test_images, test_labels_one_hot = test_data
    print(f"  Test data shapes: Images {test_images.shape}, Labels {test_labels_one_hot.shape}")
    # ... (Đảm bảo float32 giữ nguyên) ...
    if not np.issubdtype(test_images.dtype, np.floating): test_images = test_images.astype(np.float32)
    if not np.issubdtype(test_labels_one_hot.dtype, np.floating): test_labels_one_hot = test_labels_one_hot.astype(np.float32)

    # 2. Load Trained Model
    model_to_load_path = config.MODEL_SAVE_PATH
    model_filename_base = os.path.splitext(os.path.basename(model_to_load_path))[0]
    print(f"\n[Step 2/4] Loading trained model from: {model_to_load_path}...")
    # --- THAY ĐỔI: Sử dụng load_keras_model từ utils ---
    model = load_keras_model(model_to_load_path)
    if model is None:
        print("Exiting due to model loading failure.")
        return
    print("  Model architecture loaded:")
    model.summary(print_fn=lambda x: print(f"    {x}"))

    # 3. Evaluate Model Performance (model.evaluate)
    print("\n[Step 3/4] Evaluating model performance using model.evaluate()...")
    loss, accuracy = -1.0, -1.0
    try:
        loss, accuracy = model.evaluate(test_images, test_labels_one_hot, batch_size=config.BATCH_SIZE, verbose=1)
        print(f"\n  Test Loss (from evaluate): {loss:.4f}")
        print(f"  Test Accuracy (from evaluate): {accuracy:.4f} ({accuracy * 100:.2f}%)")
    except Exception as e: print(f"ERROR during model.evaluate(): {e}")

    # 4. Detailed Evaluation
    print("\n[Step 4/4] Generating predictions for detailed evaluation...")
    try:
        predictions_prob = model.predict(test_images, batch_size=config.BATCH_SIZE, verbose=1)

        # Classification Report
        print("\nClassification Report:")
        class_names = [str(i) for i in range(config.NUM_CLASSES)]
        report = get_classification_report(test_labels_one_hot, predictions_prob, target_names=class_names)
        if report:
            print(report)
            report_filename = f'test_classification_report_{model_filename_base}.txt'
            report_save_path = os.path.join(config.MODELS_DIR, report_filename)
            try:
                with open(report_save_path, 'w') as f:
                    # ... (Nội dung file report giữ nguyên) ...
                    f.write(f"Model File: {os.path.basename(model_to_load_path)}\n")
                    f.write(f"Test Loss (from evaluate): {loss:.4f}\n")
                    f.write(f"Test Accuracy (from evaluate): {accuracy:.4f}\n\n")
                    f.write("Classification Report:\n")
                    f.write(report)
                print(f"INFO: Classification report saved to {report_save_path}")
            except Exception as e_save: print(f"ERROR: Failed to save classification report: {e_save}")
        else: print("ERROR: Could not generate classification report.")

        # Confusion Matrix
        print("\nCalculating and plotting confusion matrix...")
        cm = calculate_confusion_matrix(test_labels_one_hot, predictions_prob)
        if cm is not None and MATPLOTLIB_AVAILABLE:
            plot_confusion_matrix(
                cm, class_names=class_names, save_path=config.MODELS_DIR,
                filename=f'confusion_matrix_{model_filename_base}.png',
                title=f'Confusion Matrix ({model_filename_base})'
            )
        elif cm is None: print("ERROR: Could not calculate confusion matrix.")
        else: print("INFO: Skipping confusion matrix plot (matplotlib/seaborn unavailable).")

    except Exception as e:
        print(f"\nERROR during prediction or detailed evaluation: {e}")
        import traceback
        traceback.print_exc()

    print("\n--- Model Evaluation Finished ---")

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