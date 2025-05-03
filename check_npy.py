# check_npy.py
import numpy as np
import matplotlib.pyplot as plt
import config
import random
import os

print(f"Checking NPY file: {config.TRAIN_NPY_PATH}")
if not os.path.exists(config.TRAIN_NPY_PATH):
    print("ERROR: Train NPY file not found!")
else:
    try:
        train_data = np.load(config.TRAIN_NPY_PATH)
        train_images = train_data['images']
        train_labels_one_hot = train_data['labels']
        print(f"Train images shape: {train_images.shape}")
        print(f"Train labels shape: {train_labels_one_hot.shape}")

        plt.figure(figsize=(10, 5))
        plt.suptitle("Sample Training Images (Post-Cleaning)")
        indices = random.sample(range(len(train_images)), min(9, len(train_images)))
        for i, idx in enumerate(indices):
            plt.subplot(3, 3, i + 1)
            img = train_images[idx]

            if img.dtype in [np.float32, np.float64]:
                img_to_show = np.clip(img, 0, 1)
            elif img.dtype == np.uint8:
                img_to_show = img / 255.0
            else:
                print(f"Unsupported image dtype: {img.dtype}")
                continue

            plt.imshow(img_to_show)
            label_int = np.argmax(train_labels_one_hot[idx])
            plt.title(f"Label: {label_int}")
            plt.axis('off')
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.show()
    except Exception as e:
        print(f"Error loading or plotting train data: {e}")
