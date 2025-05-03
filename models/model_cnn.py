# models/model_cnn.py
from tensorflow import keras
from tensorflow.keras import layers # type: ignore
# Import config để lấy các thông số cấu hình cần thiết
import config # Đảm bảo config.py ở thư mục gốc

def build_basic_cnn(input_shape=(config.IMG_HEIGHT, config.IMG_WIDTH, 3), num_classes=config.NUM_CLASSES):
    """
    Xây dựng kiến trúc mô hình CNN cơ bản cho bài toán GTSRB. (Giữ lại để tham khảo)

    Args:
        input_shape (tuple): Kích thước ảnh đầu vào (height, width, channels).
                             Lấy từ config.py.
        num_classes (int): Số lượng lớp đầu ra (số loại biển báo).
                           Lấy từ config.py.

    Returns:
        keras.Model: Trả về một đối tượng mô hình Keras Sequential đã được định nghĩa
                   nhưng chưa được biên dịch (compile).
    """
    print(f"Building Basic CNN model with input shape: {input_shape} and {num_classes} classes.")

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
            layers.Dropout(0.5, name="dropout1"),
            layers.Dense(num_classes, activation="softmax", name="output_layer"),
        ],
        name="basic_gtsrb_cnn"
    )
    print("Basic CNN model architecture defined successfully.")
    return model

def build_improved_cnn(input_shape=(config.IMG_HEIGHT, config.IMG_WIDTH, 3), num_classes=config.NUM_CLASSES):
    """
    Xây dựng kiến trúc mô hình CNN cải tiến với Batch Normalization và tùy chọn Dense layer.
    """
    print(f"Building Improved CNN model with input shape: {input_shape} and {num_classes} classes.")

    model = keras.Sequential(
        [
            keras.Input(shape=input_shape, name="input_layer"),

            # ---------- Khối Tích chập 1 ----------
            layers.Conv2D(32, kernel_size=(3, 3), padding='same', name="conv1"), # Thêm padding='same'
            layers.BatchNormalization(name="bn1"),                                # <<< THÊM BN
            layers.Activation('relu', name='relu1'),                              # <<< Dùng Activation riêng
            layers.MaxPooling2D(pool_size=(2, 2), name="pool1"),

            # ---------- Khối Tích chập 2 ----------
            layers.Conv2D(64, kernel_size=(3, 3), padding='same', name="conv2"),
            layers.BatchNormalization(name="bn2"),                                # <<< THÊM BN
            layers.Activation('relu', name='relu2'),
            layers.MaxPooling2D(pool_size=(2, 2), name="pool2"),

            # ---------- Khối Tích chập 3 ----------
            layers.Conv2D(128, kernel_size=(3, 3), padding='same', name="conv3"),
            layers.BatchNormalization(name="bn3"),                                # <<< THÊM BN
            layers.Activation('relu', name='relu3'),
            layers.MaxPooling2D(pool_size=(2, 2), name="pool3"),

            # ---------- (Tùy chọn) Khối Tích chập 4 ----------
            # layers.Conv2D(256, kernel_size=(3, 3), padding='same', name="conv4"), # Nếu cần mô hình phức tạp hơn
            # layers.BatchNormalization(name="bn4"),
            # layers.Activation('relu', name='relu4'),
            # layers.MaxPooling2D(pool_size=(2, 2), name="pool4"),

            # ---------- Phần Phân loại ----------
            layers.Flatten(name="flatten"),

            # Thêm Dropout trước Dense layer (nếu dùng)
            layers.Dropout(0.5, name="dropout_pre_dense"), # Giữ lại dropout này

            # ---------- (Tùy chọn) Dense Layer ----------
            # Thử nghiệm bỏ comment các dòng này để xem có cải thiện không
            layers.Dense(512, name="dense1"),             # Tăng số units
            layers.BatchNormalization(name="bn_dense1"),  # BN cũng hữu ích cho Dense
            layers.Activation('relu', name='relu_dense1'),
            layers.Dropout(0.5, name="dropout_post_dense"), # Thêm Dropout sau Dense

            # ---------- Lớp Output ----------
            layers.Dense(num_classes, activation="softmax", name="output_layer"),
        ],
        name="improved_gtsrb_cnn" # Đổi tên mô hình
    )

    print("Improved CNN model architecture defined successfully.")
    return model

# ---------- Khối kiểm tra (chỉ chạy khi thực thi file này trực tiếp) ----------
if __name__ == "__main__":
    print("\n--- Testing Basic Model Build ---")
    try:
        img_h = config.IMG_HEIGHT
        img_w = config.IMG_WIDTH
        num_c = config.NUM_CLASSES
        input_s = (img_h, img_w, 3)
        test_model_basic = build_basic_cnn(input_shape=input_s, num_classes=num_c)
        print("\nBasic Model Summary:")
        test_model_basic.summary()
    except AttributeError as e:
        print(f"\nERROR: Config attributes missing for basic model: {e}")
    except Exception as e:
         print(f"\nAn unexpected error occurred during basic model build: {e}")

    print("\n--- Testing Improved Model Build ---")
    try:
        img_h = config.IMG_HEIGHT
        img_w = config.IMG_WIDTH
        num_c = config.NUM_CLASSES
        input_s = (img_h, img_w, 3)
        test_model_improved = build_improved_cnn(input_shape=input_s, num_classes=num_c)
        print("\nImproved Model Summary:")
        test_model_improved.summary()
    except AttributeError as e:
        print(f"\nERROR: Config attributes missing for improved model: {e}")
    except Exception as e:
         print(f"\nAn unexpected error occurred during improved model build: {e}")

    print("\n--- Model Build Test Finished ---")
