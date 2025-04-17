import cv2
import os
from matplotlib import pyplot as plt

image_path = 'data/images/mca2322059.jpg'

if not os.path.exists(image_path):
    print("[ERROR] Image file does not exist.")
else:
    image = cv2.imread(image_path)

    if image is None:
        print("[ERROR] cv2 failed to load image. It may be corrupted or unsupported format.")
    else:
        print("[INFO] Image loaded successfully with shape:", image.shape)

        # Show image
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        plt.imshow(image_rgb)
        plt.title("Loaded Image")
        plt.axis('off')
        plt.show()
