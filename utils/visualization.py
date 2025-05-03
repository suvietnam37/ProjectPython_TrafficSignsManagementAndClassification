# utils/visualization.py

import os
import numpy as np
import itertools # Sử dụng cho confusion matrix nếu không dùng seaborn

# Import thư viện vẽ đồ thị, xử lý lỗi nếu không có
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("WARNING: matplotlib not found. Plotting functions will not work.")

try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False
    print("WARNING: seaborn not found. Confusion matrix plotting might be limited or unavailable.")

# --- Plot Training History ---
def plot_training_history(history, save_path=None, filename='training_history.png', title_prefix=''):
    """
    Vẽ đồ thị accuracy và loss từ đối tượng history hoặc dictionary.

    Args:
        history (keras.callbacks.History or dict): Đối tượng history từ model.fit
                                                    hoặc dictionary chứa các key
                                                    'accuracy', 'val_accuracy', 'loss', 'val_loss'.
        save_path (str, optional): Thư mục để lưu đồ thị. Nếu None, không lưu.
        filename (str, optional): Tên file để lưu đồ thị.
        title_prefix (str, optional): Tiền tố thêm vào tiêu đề đồ thị.
    """
    if not MATPLOTLIB_AVAILABLE:
        print("ERROR: Cannot plot history, matplotlib is not available.")
        return

    # Kiểm tra xem history là object hay dict và lấy dữ liệu
    history_dict = None
    epochs = None
    if hasattr(history, 'history') and isinstance(history.history, dict):
        history_dict = history.history
        epochs = history.epoch
    elif isinstance(history, dict):
        history_dict = history
        # Ước lượng số epochs nếu không có sẵn key 'epoch'
        if 'loss' in history_dict:
             epochs = range(len(history_dict['loss']))

    required_keys = ['accuracy', 'val_accuracy', 'loss', 'val_loss']
    if not history_dict or not all(key in history_dict for key in required_keys):
        print("WARNING: History object/dictionary missing or incomplete. Skipping plot.")
        if history_dict: print(f"Available keys: {list(history_dict.keys())}")
        return

    if epochs is None:
         print("WARNING: Could not determine epochs range. Skipping plot.")
         return

    try:
        acc = history_dict['accuracy']
        val_acc = history_dict['val_accuracy']
        loss = history_dict['loss']
        val_loss = history_dict['val_loss']
        epochs_range = epochs # Sử dụng epochs đã xác định

        plt.figure(figsize=(12, 5))
        full_title_prefix = f"{title_prefix}: " if title_prefix else ""

        # Accuracy Plot
        plt.subplot(1, 2, 1)
        plt.plot(epochs_range, acc, label='Training Accuracy', marker='o', linestyle='-')
        plt.plot(epochs_range, val_acc, label='Validation Accuracy', marker='x', linestyle='--')
        plt.legend(loc='lower right')
        plt.title(f'{full_title_prefix}Training and Validation Accuracy')
        plt.xlabel('Epochs')
        plt.ylabel('Accuracy')
        plt.grid(True)
        # Giới hạn trục y
        if max(acc + val_acc) > 0.1 : # Tránh lỗi nếu acc = 0
             plt.ylim([min(min(acc, default=0.5), min(val_acc, default=0.5), 0.5), 1.02])

        # Loss Plot
        plt.subplot(1, 2, 2)
        plt.plot(epochs_range, loss, label='Training Loss', marker='o', linestyle='-')
        plt.plot(epochs_range, val_loss, label='Validation Loss', marker='x', linestyle='--')
        plt.legend(loc='upper right')
        plt.title(f'{full_title_prefix}Training and Validation Loss')
        plt.xlabel('Epochs')
        plt.ylabel('Loss')
        plt.grid(True)
        # Giới hạn trục y
        if max(loss + val_loss) > 0: # Tránh lỗi nếu loss = 0
            plt.ylim([0, max(max(loss, default=1.0)*1.1, max(val_loss, default=1.0)*1.1, 1.0)])

        plt.tight_layout()

        # Save Plot
        if save_path:
            os.makedirs(save_path, exist_ok=True)
            plot_file = os.path.join(save_path, filename)
            try:
                plt.savefig(plot_file)
                print(f"INFO: Training history plot saved to {plot_file}")
            except Exception as e:
                print(f"ERROR: Could not save plot to {plot_file}. Reason: {e}")

        plt.show() # Hiển thị đồ thị

    except Exception as e:
         print(f"ERROR: An unexpected error occurred while plotting history: {e}")
         import traceback
         traceback.print_exc()


# --- Plot Confusion Matrix ---
def plot_confusion_matrix(cm, class_names, save_path=None, filename='confusion_matrix.png', title='Confusion Matrix', cmap=plt.cm.Blues, normalize=False):
    """
    Vẽ ma trận nhầm lẫn chi tiết sử dụng Matplotlib (và tùy chọn Seaborn).

    Args:
        cm (np.ndarray): Ma trận nhầm lẫn (tính từ sklearn.metrics.confusion_matrix).
        class_names (list): Danh sách tên các lớp tương ứng với chỉ số của cm.
        save_path (str, optional): Thư mục để lưu đồ thị. Nếu None, không lưu.
        filename (str, optional): Tên file để lưu đồ thị.
        title (str, optional): Tiêu đề của đồ thị.
        cmap (matplotlib.colors.Colormap, optional): Bảng màu sử dụng.
        normalize (bool, optional): True để chuẩn hóa giá trị trong ma trận về [0, 1].
    """
    if not MATPLOTLIB_AVAILABLE:
        print("ERROR: Cannot plot confusion matrix, matplotlib is not available.")
        return

    if normalize:
        # Chuẩn hóa bằng cách chia mỗi hàng cho tổng của nó
        cm_sum = cm.sum(axis=1)[:, np.newaxis]
        # Tránh chia cho 0 nếu một lớp không có mẫu nào trong tập dữ liệu thực tế
        cm_sum[cm_sum == 0] = 1
        cm = cm.astype('float') / cm_sum
        print("Normalized confusion matrix")
        fmt = '.2f' # Định dạng số thực khi chuẩn hóa
        val_max = 1.0
    else:
        print("Confusion matrix, without normalization")
        fmt = 'd' # Định dạng số nguyên
        val_max = cm.max() if cm.size > 0 else 0

    plt.figure(figsize=(max(10, len(class_names)//2), max(8, len(class_names)//2.5))) # Điều chỉnh kích thước tự động

    # Ưu tiên dùng Seaborn nếu có vì đẹp hơn
    if SEABORN_AVAILABLE:
        try:
             sns.heatmap(cm, annot=True, fmt=fmt, cmap=cmap,
                         xticklabels=class_names, yticklabels=class_names,
                         annot_kws={"size": 8}) # Cỡ chữ chú thích
        except Exception as e:
             print(f"INFO: Seaborn heatmap failed ({e}), falling back to Matplotlib imshow.")
             # Fallback nếu Seaborn lỗi
             plt.imshow(cm, interpolation='nearest', cmap=cmap)
             # Thêm text annotations thủ công (có thể chậm với nhiều lớp)
             thresh = val_max / 2.
             for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
                 plt.text(j, i, format(cm[i, j], fmt),
                          horizontalalignment="center",
                          color="white" if cm[i, j] > thresh else "black",
                          fontsize=6) # Cỡ chữ nhỏ hơn cho text
    else:
        # Vẽ bằng Matplotlib nếu không có Seaborn
        plt.imshow(cm, interpolation='nearest', cmap=cmap)
        # Thêm text annotations thủ công
        thresh = val_max / 2.
        for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
             plt.text(j, i, format(cm[i, j], fmt),
                      horizontalalignment="center",
                      color="white" if cm[i, j] > thresh else "black",
                      fontsize=6)

    plt.title(title)
    plt.colorbar() # Thêm thanh màu
    tick_marks = np.arange(len(class_names))
    plt.xticks(tick_marks, class_names, rotation=90, fontsize=8)
    plt.yticks(tick_marks, class_names, rotation=0, fontsize=8)

    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.tight_layout()

    # Save Plot
    if save_path:
        os.makedirs(save_path, exist_ok=True) # Đảm bảo thư mục tồn tại
        plot_file = os.path.join(save_path, filename)
        try:
            plt.savefig(plot_file)
            print(f"INFO: Confusion matrix plot saved to {plot_file}")
        except Exception as e:
            print(f"ERROR: Could not save confusion matrix plot to {plot_file}. Reason: {e}")

    plt.show() # Hiển thị đồ thị

# --- (Ví dụ) Hàm hiển thị ảnh ---
def display_images(images, labels=None, class_names=None, num_rows=3, num_cols=3, title="Sample Images"):
    """Hiển thị một lưới các ảnh."""
    if not MATPLOTLIB_AVAILABLE:
        print("ERROR: Cannot display images, matplotlib is not available.")
        return

    num_images = num_rows * num_cols
    if len(images) < num_images:
        print(f"Warning: Not enough images ({len(images)}) to fill grid ({num_images}).")
        num_images = len(images)
        # Điều chỉnh grid nếu cần? (Tạm thời không)

    plt.figure(figsize=(num_cols * 2, num_rows * 2)) # Kích thước tùy thuộc grid
    plt.suptitle(title)

    indices = np.random.choice(range(len(images)), size=num_images, replace=False)

    for i, idx in enumerate(indices):
        plt.subplot(num_rows, num_cols, i + 1)
        img = images[idx]

        # Xử lý kiểu dữ liệu ảnh để hiển thị
        if img.dtype in [np.float32, np.float64]:
            img_to_show = np.clip(img, 0, 1) # Ảnh đã chuẩn hóa [0, 1]
        elif img.dtype == np.uint8:
            img_to_show = img / 255.0 # Ảnh gốc [0, 255]
        else:
            print(f"Unsupported image dtype: {img.dtype}")
            continue

        plt.imshow(img_to_show)
        plt.axis('off')

        # Hiển thị nhãn nếu có
        img_title = ""
        if labels is not None:
            label = labels[idx]
            # Xử lý nhãn one-hot hoặc integer
            if isinstance(label, (np.ndarray, list)) and len(label) > 1: # One-hot
                label_int = np.argmax(label)
            elif isinstance(label, (int, np.integer)): # Integer
                label_int = label
            else:
                label_int = -1 # Không xác định

            if label_int != -1:
                 if class_names and 0 <= label_int < len(class_names):
                     img_title = f"{class_names[label_int]} ({label_int})"
                 else:
                     img_title = f"Label: {label_int}"
            plt.title(img_title, fontsize=8)


    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Điều chỉnh layout để title không bị che
    plt.show()


# --- Chạy thử ---
if __name__ == "__main__":
    print("--- Testing Visualization Utils ---")

    # 1. Test plot_training_history (với dict giả)
    print("\n1. Testing History Plot:")
    if MATPLOTLIB_AVAILABLE:
        dummy_history_data = {
            'loss': np.array([0.5, 0.3, 0.2]),
            'accuracy': np.array([0.8, 0.9, 0.95]),
            'val_loss': np.array([0.6, 0.4, 0.35]),
            'val_accuracy': np.array([0.75, 0.85, 0.91]),
            'epoch': [0, 1, 2]
        }
        plot_training_history(dummy_history_data, title_prefix="Dummy Test")
    else:
        print("Skipping history plot test - matplotlib not available.")

    # 2. Test plot_confusion_matrix (với cm giả)
    print("\n2. Testing Confusion Matrix Plot:")
    if MATPLOTLIB_AVAILABLE:
        dummy_cm = np.array([[10, 2, 0],
                             [1, 15, 3],
                             [0, 4, 12]])
        dummy_names = ['Class A', 'Class B', 'Class C']
        plot_confusion_matrix(dummy_cm, dummy_names, title="Dummy CM")
        # Test với normalize
        plot_confusion_matrix(dummy_cm, dummy_names, title="Dummy CM (Normalized)", normalize=True)
    else:
        print("Skipping confusion matrix plot test - matplotlib not available.")

    # 3. Test display_images (với ảnh giả)
    print("\n3. Testing Image Display:")
    if MATPLOTLIB_AVAILABLE:
        dummy_images = np.random.rand(10, 32, 32, 3).astype(np.float32) # Ảnh float [0, 1]
        dummy_labels_int = np.random.randint(0, 5, size=10)
        display_images(dummy_images, dummy_labels_int, title="Dummy Float Images")

        dummy_images_uint = (np.random.rand(10, 32, 32, 3) * 255).astype(np.uint8) # Ảnh uint8 [0, 255]
        dummy_labels_onehot = np.eye(5)[dummy_labels_int] # Nhãn one-hot
        display_images(dummy_images_uint, dummy_labels_onehot, class_names=[f'T{i}' for i in range(5)], title="Dummy Uint8 Images")
    else:
        print("Skipping image display test - matplotlib not available.")


    print("\n--- Test Finished ---")