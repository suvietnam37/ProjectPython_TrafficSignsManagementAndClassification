# training/train_model.py

import os
import numpy as np
import tensorflow as tf
from tensorflow import keras
# Import để tính class weights (dù có thể không dùng)
from sklearn.utils import class_weight
# Import callbacks
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau # type: ignore

# --- Import các thành phần từ dự án ---
import config
from utils.data_loader import load_data_npy # Hàm tải dữ liệu từ .npy
from models.model_cnn import build_improved_cnn # <<< Import kiến trúc mới
# --- Import hàm plot từ utils ---
from utils.visualization import plot_training_history, MATPLOTLIB_AVAILABLE

# --- Hàm chính ---
def main():
    """
    Hàm chính thực hiện tải dữ liệu (AUGMENTED),
    xây dựng, biên dịch và huấn luyện mô hình CNN cải tiến.
    """
    print("--- Starting Model Training with AUGMENTED Data ---") # <<< Cập nhật tiêu đề log

    # 1. Load Processed Data (from AUGMENTED source)
    # --------------------------------------------
    print("\n[Step 1/6] Loading AUGMENTED training data...")
    # <<< THAY ĐỔI: Sử dụng đường dẫn dữ liệu tăng cường >>>
    train_data_path = config.AUGMENTED_TRAIN_NPY_PATH
    val_data_path = config.VAL_NPY_PATH # Validation set vẫn giữ nguyên từ processed

    print(f"  Augmented Training data from: {train_data_path}")
    print(f"  Validation data from: {val_data_path}")

    train_data = load_data_npy(train_data_path)
    val_data = load_data_npy(val_data_path)

    if train_data is None or val_data is None:
        print("ERROR: Failed to load augmented training or validation data. Exiting.")
        print(f"Ensure {train_data_path} and {val_data_path} exist and are valid .npz files.")
        return

    train_images, train_labels_one_hot = train_data
    val_images, val_labels_one_hot = val_data

    # In ra số lượng mẫu mới sau khi tăng cường
    print(f"  Augmented Training data shapes: Images {train_images.shape}, Labels {train_labels_one_hot.shape}")
    print(f"  Validation data shapes: Images {val_images.shape}, Labels {val_labels_one_hot.shape}")
    print(f"  Training image data type: {train_images.dtype}, Label data type: {train_labels_one_hot.dtype}")

    # Đảm bảo kiểu dữ liệu float32
    if not np.issubdtype(train_images.dtype, np.floating):
         train_images = train_images.astype(np.float32)
    if not np.issubdtype(train_labels_one_hot.dtype, np.floating):
         train_labels_one_hot = train_labels_one_hot.astype(np.float32)
    if not np.issubdtype(val_images.dtype, np.floating):
         val_images = val_images.astype(np.float32)
    if not np.issubdtype(val_labels_one_hot.dtype, np.floating):
         val_labels_one_hot = val_labels_one_hot.astype(np.float32)
    print("  Ensured data types are float32.")


    # 2. Calculate Class Weights (Should be DISABLED for augmented/oversampled data)
    # --------------------------
    print("\n[Step 2/6] Class Weights Calculation...")
    # <<< THAY ĐỔI: Đặt thành False khi dùng dữ liệu đã oversample >>>
    use_class_weights = False
    class_weights_dict = None
    if use_class_weights:
        # Phần tính toán này sẽ không được chạy nếu use_class_weights=False
        try:
            train_labels_int = np.argmax(train_labels_one_hot, axis=1)
            classes_present = np.unique(train_labels_int)
            class_weights_array = class_weight.compute_class_weight(
                class_weight='balanced',
                classes=classes_present,
                y=train_labels_int
            )
            class_weights_dict = dict(zip(classes_present, class_weights_array))
            print(f"  Calculated class weights (examples):")
            for i in range(min(5, config.NUM_CLASSES)):
                 weight = class_weights_dict.get(i, "Not Present/Calculated")
                 if isinstance(weight, (int, float)): print(f"    Class {i}: {weight:.4f}")
                 else: print(f"    Class {i}: {weight}")
            if not all(c in class_weights_dict for c in range(config.NUM_CLASSES)):
                 print("  Warning: Some classes might be missing from the training set.")
        except Exception as e:
            print(f"ERROR calculating class weights: {e}. Proceeding without class weights.")
            class_weights_dict = None
    else:
        print("  Skipping class weight calculation (use_class_weights=False - Recommended for augmented/oversampled data).")


    # 3. Build the Model
    # -------------------------------------
    print("\n[Step 3/6] Building the IMPROVED CNN model...")
    model = build_improved_cnn(
        input_shape=(config.IMG_HEIGHT, config.IMG_WIDTH, 3),
        num_classes=config.NUM_CLASSES
    )
    print("  Model architecture:")
    model.summary(print_fn=lambda x: print(f"    {x}"))


    # 4. Compile the Model
    # -------------------------------------
    print("\n[Step 4/6] Compiling the model...")
    optimizer = keras.optimizers.Adam(learning_rate=config.LEARNING_RATE)
    loss_function = 'categorical_crossentropy'
    metrics_to_track = ['accuracy']

    model.compile(
        optimizer=optimizer,
        loss=loss_function,
        metrics=metrics_to_track
    )
    print("  Model compiled successfully.")


    # 5. Setup Callbacks
    # -------------------------------------
    print("\n[Step 5/6] Setting up Improved Callbacks...")
    model_save_path = config.MODEL_SAVE_PATH # Vẫn lưu model tốt nhất vào đây
    print(f"  Best model (based on val_accuracy) will be saved to: {model_save_path}")

    model_checkpoint = ModelCheckpoint(
        filepath=model_save_path, monitor='val_accuracy', save_best_only=True,
        verbose=1, mode='max'
    )
    early_stopping = EarlyStopping(
        monitor='val_accuracy', patience=config.EARLY_STOPPING_PATIENCE, verbose=1,
        mode='max', restore_best_weights=True # Giữ lại trọng số tốt nhất khi dừng sớm
    )
    reduce_lr = ReduceLROnPlateau(
        monitor='val_accuracy', factor=config.LR_REDUCTION_FACTOR, patience=config.LR_PATIENCE,
        verbose=1, mode='max', min_lr=config.MIN_LR # Giảm LR khi val_accuracy không cải thiện
    )
    print("  Callbacks configured (ModelCheckpoint, EarlyStopping, ReduceLROnPlateau).")


    # 6. Train the Model
    # --------------------------------------
    print("\n[Step 6/6] Starting model training with Augmented Data...") # Cập nhật log
    print(f"  Epochs: {config.EPOCHS}")
    print(f"  Batch Size: {config.BATCH_SIZE}")
    # Kiểm tra và thông báo về việc không dùng class weights
    if class_weights_dict and use_class_weights: print("  WARNING: Using calculated class weights, but it's generally not recommended with oversampled data.")
    elif not use_class_weights: print("  Not using class weights (Correct for augmented/oversampled data).")
    else: print("  Not using class weights (Calculation skipped or failed).")

    history = None
    try:
        history = model.fit(
            x=train_images,
            y=train_labels_one_hot,
            batch_size=config.BATCH_SIZE,
            epochs=config.EPOCHS,
            validation_data=(val_images, val_labels_one_hot),
            callbacks=[model_checkpoint, early_stopping, reduce_lr],
            # <<< Đảm bảo class_weight=None khi use_class_weights=False >>>
            class_weight=class_weights_dict if use_class_weights else None,
            verbose=1 # Hiện progress bar
        )
        print("\n--- Model Training Finished ---")

        # Đánh giá lại model trên tập validation (sau khi EarlyStopping có thể đã restore best weights)
        print("\nEvaluating model with best weights on validation data:")
        # Model đã được restore_best_weights=True nên gọi evaluate trực tiếp
        evaluation_results = model.evaluate(val_images, val_labels_one_hot, batch_size=config.BATCH_SIZE, verbose=0)
        print(f"  Best Validation Loss: {evaluation_results[0]:.4f}")
        print(f"  Best Validation Accuracy: {evaluation_results[1]*100:.2f}%")

    except Exception as e:
        print(f"\nERROR occurred during training: {e}")
        import traceback
        traceback.print_exc()

    # --- Plot training history USING IMPORTED FUNCTION ---
    if MATPLOTLIB_AVAILABLE and history: # <<< Sử dụng cờ import từ visualization
        print("\nPlotting training history...")
        # Tạo tên file plot dựa trên tên model đã lưu
        model_filename_base = os.path.splitext(os.path.basename(config.MODEL_SAVE_PATH))[0]
        plot_filename = f'training_history_{model_filename_base}_augmented.png' # Thêm _augmented vào tên file
        plot_training_history( # <<< Gọi hàm đã import
            history,
            save_path=config.MODELS_DIR,
            filename=plot_filename,
            title_prefix="Improved CNN (Augmented Data)" # <<< Cập nhật tiêu đề plot
        )
    elif not MATPLOTLIB_AVAILABLE:
        print("\nSkipping plot: matplotlib not available (check utils.visualization).")
    else:
        print("\nSkipping plot: training did not complete successfully or history is unavailable.")


if __name__ == "__main__":
    # Cấu hình GPU (giữ nguyên)
    print(f"Using TensorFlow version: {tf.__version__}")
    gpus = tf.config.experimental.list_physical_devices('GPU')
    if gpus:
        try:
            print(f"INFO: Found {len(gpus)} Physical GPU(s).")
            # Giới hạn bộ nhớ hoặc cho phép tăng trưởng động
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
            logical_gpus = tf.config.experimental.list_logical_devices('GPU')
            print(f"INFO: Successfully set memory growth for {len(logical_gpus)} Logical GPU(s).")
        except RuntimeError as e:
            print(f"ERROR setting memory growth: {e}. Check TensorFlow/CUDA compatibility.")
    else:
        print("INFO: No GPU found by TensorFlow, using CPU.")

    main()
