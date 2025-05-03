# models/model_cnn.py
import sys
import os
import logging

# --- Calculate Project Root ---
# Goes up 2 levels from models/model_cnn.py to reach project root
try:
    current_script_path = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(current_script_path))
except NameError:
    project_root = os.path.abspath(os.path.join(os.getcwd(), '..')) # Fallback

# --- Add project root to sys.path ---
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger_model = logging.getLogger("ModelCNN")
logger_model.info(f"Project root added to sys.path: {project_root}")


# --- Import Config and TensorFlow/Keras ---
TF_AVAILABLE = False
CONFIG_LOADED_MODEL = False
try:
    import config # Now this should work
    CONFIG_LOADED_MODEL = True
    from tensorflow import keras
    from tensorflow.keras import layers # type: ignore
    TF_AVAILABLE = True
    logger_model.info("TensorFlow/Keras and Config imported successfully.")
except ImportError as e:
    logger_model.error(f"ERROR: Failed to import TensorFlow/Keras or Config: {e}")
    logger_model.error("Ensure TensorFlow is installed ('pip install tensorflow') and config.py exists in the project root.")
    # No need to exit here, the rest of the code is guarded by TF_AVAILABLE
except Exception as e:
     logger_model.error(f"ERROR: An unexpected error occurred during imports: {e}")


# --- Model Definitions ---

# Only define if TensorFlow and Config are available
if TF_AVAILABLE and CONFIG_LOADED_MODEL:
    def build_basic_cnn(input_shape=(config.IMG_HEIGHT, config.IMG_WIDTH, 3), num_classes=config.NUM_CLASSES):
        """Builds a basic CNN architecture (reference)."""
        logger_model.info(f"Building Basic CNN model: Input={input_shape}, Classes={num_classes}")
        model = keras.Sequential(
            [
                keras.Input(shape=input_shape, name="input_layer"),
                layers.Conv2D(32, kernel_size=(3, 3), activation="relu", name="conv1"),
                layers.MaxPooling2D(pool_size=(2, 2), name="pool1"),
                layers.Conv2D(64, kernel_size=(3, 3), activation="relu", name="conv2"),
                layers.MaxPooling2D(pool_size=(2, 2), name="pool2"),
                layers.Conv2D(128, kernel_size=(3, 3), activation="relu", name="conv3"),
                layers.MaxPooling2D(pool_size=(2, 2), name="pool3"),
                layers.Flatten(name="flatten"),
                layers.Dropout(0.5, name="dropout1"), # Standard dropout rate
                layers.Dense(num_classes, activation="softmax", name="output_layer"),
            ],
            name="basic_gtsrb_cnn"
        )
        logger_model.info("Basic CNN model architecture defined.")
        return model

    def build_improved_cnn(input_shape=(config.IMG_HEIGHT, config.IMG_WIDTH, 3), num_classes=config.NUM_CLASSES):
        """Builds an improved CNN architecture with Batch Normalization and more layers."""
        logger_model.info(f"Building Improved CNN model: Input={input_shape}, Classes={num_classes}")
        model = keras.Sequential(
            [
                keras.Input(shape=input_shape, name="input_layer"),

                # Conv Block 1
                layers.Conv2D(32, kernel_size=(3, 3), padding='same', name="conv1"),
                layers.BatchNormalization(name="bn1"),
                layers.Activation('relu', name='relu1'),
                layers.MaxPooling2D(pool_size=(2, 2), name="pool1"),

                # Conv Block 2
                layers.Conv2D(64, kernel_size=(3, 3), padding='same', name="conv2"),
                layers.BatchNormalization(name="bn2"),
                layers.Activation('relu', name='relu2'),
                layers.MaxPooling2D(pool_size=(2, 2), name="pool2"),

                # Conv Block 3
                layers.Conv2D(128, kernel_size=(3, 3), padding='same', name="conv3"),
                layers.BatchNormalization(name="bn3"),
                layers.Activation('relu', name='relu3'),
                layers.MaxPooling2D(pool_size=(2, 2), name="pool3"),

                # Flattening and Dense Layers
                layers.Flatten(name="flatten"),
                layers.Dropout(0.5, name="dropout_flatten"),

                # Dense Block 1
                layers.Dense(512, name="dense1"),
                layers.BatchNormalization(name="bn_dense1"),
                layers.Activation('relu', name='relu_dense1'),
                layers.Dropout(0.5, name="dropout_dense1"),

                # Output Layer
                layers.Dense(num_classes, activation="softmax", name="output_layer"),
            ],
            name="improved_gtsrb_cnn"
        )
        logger_model.info("Improved CNN model architecture defined.")
        return model
else:
    # Define dummy functions or raise errors if TF/Config are missing but file is imported elsewhere
    def build_basic_cnn(*args, **kwargs):
        logger_model.error("Cannot build basic CNN: TensorFlow or Config not available.")
        return None
    def build_improved_cnn(*args, **kwargs):
        logger_model.error("Cannot build improved CNN: TensorFlow or Config not available.")
        return None

# --- Test Block ---
# This block only runs when the script is executed directly
if __name__ == "__main__":
    logger_model.info("Running model_cnn.py directly for testing...")
    if TF_AVAILABLE and CONFIG_LOADED_MODEL:
        print("\n--- Testing Basic Model Build ---")
        try:
            basic_model = build_basic_cnn()
            if basic_model:
                 print("Basic Model Summary:")
                 basic_model.summary()
            else:
                 print("Failed to build basic model.")
        except Exception as e:
            print(f"ERROR building basic model: {e}")

        print("\n--- Testing Improved Model Build ---")
        try:
            improved_model = build_improved_cnn()
            if improved_model:
                 print("Improved Model Summary:")
                 improved_model.summary()
            else:
                 print("Failed to build improved model.")

        except Exception as e:
            print(f"ERROR building improved model: {e}")

        print("\n--- Model Build Test Finished ---")
    else:
        print("\n--- Skipping Model Build Test (TensorFlow or Config not available) ---")