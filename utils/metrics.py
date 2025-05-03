# utils/metrics.py

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report
)
import config # Có thể cần NUM_CLASSES

def calculate_metrics(y_true_one_hot, y_pred_prob, threshold=0.5):
    """
    Tính toán các metrics cơ bản từ nhãn thật (one-hot) và xác suất dự đoán.

    Args:
        y_true_one_hot (np.ndarray): Mảng one-hot encoding của nhãn thật.
                                      Shape (num_samples, num_classes).
        y_pred_prob (np.ndarray): Mảng xác suất dự đoán từ mô hình.
                                  Shape (num_samples, num_classes).
        threshold (float): Ngưỡng để chuyển đổi xác suất thành lớp dự đoán
                           (Thường không cần thiết cho argmax).

    Returns:
        dict: Một dictionary chứa các metrics:
              'accuracy', 'precision_macro', 'recall_macro', 'f1_macro',
              'precision_weighted', 'recall_weighted', 'f1_weighted'.
              Trả về None nếu có lỗi.
    """
    if y_true_one_hot.shape != y_pred_prob.shape:
        print(f"Error: Shape mismatch between true labels ({y_true_one_hot.shape}) and predictions ({y_pred_prob.shape})")
        return None
    if len(y_true_one_hot.shape) != 2:
         print(f"Error: Input arrays should be 2D (samples, classes). Got shape: {y_true_one_hot.shape}")
         return None

    try:
        # Chuyển đổi one-hot và xác suất sang nhãn lớp số nguyên
        y_true = np.argmax(y_true_one_hot, axis=1)
        y_pred = np.argmax(y_pred_prob, axis=1)

        # --- Accuracy ---
        accuracy = accuracy_score(y_true, y_pred)

        # --- Precision, Recall, F1-Score ---
        # average='macro': Tính trung bình không trọng số (mỗi lớp quan trọng như nhau)
        # average='weighted': Tính trung bình có trọng số theo support (số lượng mẫu) của mỗi lớp
        precision_macro, recall_macro, f1_macro, _ = precision_recall_fscore_support(
            y_true, y_pred, average='macro', zero_division=0
        )
        precision_weighted, recall_weighted, f1_weighted, _ = precision_recall_fscore_support(
            y_true, y_pred, average='weighted', zero_division=0
        )

        metrics = {
            'accuracy': accuracy,
            'precision_macro': precision_macro,
            'recall_macro': recall_macro,
            'f1_macro': f1_macro,
            'precision_weighted': precision_weighted,
            'recall_weighted': recall_weighted,
            'f1_weighted': f1_weighted,
        }
        return metrics

    except Exception as e:
        print(f"Error calculating metrics: {e}")
        return None

def get_classification_report(y_true_one_hot, y_pred_prob, target_names=None):
    """
    Tạo classification report chi tiết từ sklearn.

    Args:
        y_true_one_hot (np.ndarray): Mảng one-hot encoding nhãn thật.
        y_pred_prob (np.ndarray): Mảng xác suất dự đoán.
        target_names (list, optional): Danh sách tên các lớp để hiển thị trong report.
                                     Nếu None, sẽ dùng chỉ số 0, 1, 2,...

    Returns:
        str: Chuỗi chứa classification report.
             Trả về None nếu có lỗi.
    """
    if y_true_one_hot.shape != y_pred_prob.shape:
        print(f"Error: Shape mismatch between true labels ({y_true_one_hot.shape}) and predictions ({y_pred_prob.shape})")
        return None
    if len(y_true_one_hot.shape) != 2:
         print(f"Error: Input arrays should be 2D (samples, classes). Got shape: {y_true_one_hot.shape}")
         return None

    try:
        y_true = np.argmax(y_true_one_hot, axis=1)
        y_pred = np.argmax(y_pred_prob, axis=1)

        if target_names is None:
             num_classes = y_true_one_hot.shape[1]
             target_names = [str(i) for i in range(num_classes)]

        report = classification_report(
            y_true, y_pred, target_names=target_names, digits=3, zero_division=0
        )
        return report

    except Exception as e:
        print(f"Error generating classification report: {e}")
        return None

def calculate_confusion_matrix(y_true_one_hot, y_pred_prob):
    """
    Tính toán ma trận nhầm lẫn.

    Args:
        y_true_one_hot (np.ndarray): Mảng one-hot encoding nhãn thật.
        y_pred_prob (np.ndarray): Mảng xác suất dự đoán.

    Returns:
        np.ndarray: Ma trận nhầm lẫn. Trả về None nếu có lỗi.
    """
    if y_true_one_hot.shape != y_pred_prob.shape:
        print(f"Error: Shape mismatch between true labels ({y_true_one_hot.shape}) and predictions ({y_pred_prob.shape})")
        return None
    if len(y_true_one_hot.shape) != 2:
         print(f"Error: Input arrays should be 2D (samples, classes). Got shape: {y_true_one_hot.shape}")
         return None

    try:
        y_true = np.argmax(y_true_one_hot, axis=1)
        y_pred = np.argmax(y_pred_prob, axis=1)
        cm = confusion_matrix(y_true, y_pred)
        return cm

    except Exception as e:
        print(f"Error calculating confusion matrix: {e}")
        return None


# --- Chạy thử (khi chạy file này trực tiếp) ---
if __name__ == "__main__":
    print("--- Testing Metrics Utils ---")

    # Dữ liệu giả
    num_samples = 100
    num_classes = 5
    y_true_int = np.random.randint(0, num_classes, size=num_samples)
    y_true_oh = np.eye(num_classes)[y_true_int] # One-hot

    # Dự đoán giả (một số đúng, một số sai)
    y_pred_p = np.random.rand(num_samples, num_classes)
    # Làm cho một số dự đoán "chắc chắn" đúng hơn
    for i in range(num_samples // 2):
        true_idx = y_true_int[i]
        y_pred_p[i, :] = 0.1 / (num_classes -1) # xác suất thấp cho các lớp khác
        y_pred_p[i, true_idx] = 0.9 # xác suất cao cho lớp đúng

    # Chuẩn hóa lại xác suất (đảm bảo tổng = 1) - quan trọng
    y_pred_p = y_pred_p / y_pred_p.sum(axis=1, keepdims=True)
    y_pred_int = np.argmax(y_pred_p, axis=1)

    print(f"Dummy data: {num_samples} samples, {num_classes} classes.")
    print(f"Shape y_true_oh: {y_true_oh.shape}, y_pred_p: {y_pred_p.shape}")

    # 1. Test calculate_metrics
    print("\n1. Basic Metrics:")
    metrics_result = calculate_metrics(y_true_oh, y_pred_p)
    if metrics_result:
        for key, value in metrics_result.items():
            print(f"  {key}: {value:.4f}")

    # 2. Test get_classification_report
    print("\n2. Classification Report:")
    report_result = get_classification_report(y_true_oh, y_pred_p)
    if report_result:
        print(report_result)

    # 3. Test calculate_confusion_matrix
    print("\n3. Confusion Matrix:")
    cm_result = calculate_confusion_matrix(y_true_oh, y_pred_p)
    if cm_result is not None:
        print(cm_result)

    print("\n--- Test Finished ---")