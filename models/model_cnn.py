from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ReduceLROnPlateau
import os


def build_cnn(input_shape=(32, 32, 3), num_classes=43):
    model = Sequential([
        Conv2D(64, (3, 3), activation='relu', padding='same', input_shape=input_shape),
        BatchNormalization(),
        Conv2D(64, (3, 3), activation='relu', padding='same'),
        BatchNormalization(),
        MaxPooling2D(pool_size=(2, 2)),
        Dropout(0.25),

        Conv2D(128, (3, 3), activation='relu', padding='same'),
        BatchNormalization(),
        Conv2D(128, (3, 3), activation='relu', padding='same'),
        BatchNormalization(),
        MaxPooling2D(pool_size=(2, 2)),
        Dropout(0.3),

        Conv2D(256, (3, 3), activation='relu', padding='same'),
        BatchNormalization(),
        Conv2D(256, (3, 3), activation='relu', padding='same'),
        BatchNormalization(),
        MaxPooling2D(pool_size=(2, 2)),
        Dropout(0.4),

        Flatten(),
        Dense(512, activation='relu'),
        BatchNormalization(),
        Dropout(0.5),
        Dense(256, activation='relu'),
        BatchNormalization(),
        Dropout(0.5),
        Dense(num_classes, activation='softmax')
    ])

    # Thêm ReduceLROnPlateau để giảm tốc độ học khi mô hình bị chững lại
    lr_scheduler = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, verbose=1, min_lr=1e-6)

    model.compile(optimizer=Adam(learning_rate=0.0005),  # Giảm learning rate để ổn định quá trình huấn luyện
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])

    return model, lr_scheduler


if __name__ == "__main__":
    model, lr_scheduler = build_cnn()

    # Định nghĩa đường dẫn lưu mô hình
    save_path = "D:/Python/models/"
    os.makedirs(save_path, exist_ok=True)  # Tạo thư mục nếu chưa có
    model.save(os.path.join(save_path, "cnn_model.keras"))

    print("Mô hình CNN đã được lưu thành công!")
