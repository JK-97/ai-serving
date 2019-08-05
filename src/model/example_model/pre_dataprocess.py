import numpy as np
import cv2


# YOLO pre-process
def pre_dataprocess(image_path, extra_data = []):

    original_image = cv2.imread(image_path)
    h_target, w_target = (544, 544)
    h_org, w_org, _ = original_image.shape
    original_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB).astype(np.float32)

    resize_ratio = min(1.0 * w_target / w_org, 1.0 * h_target / h_org)
    resize_w = int(resize_ratio * w_org)
    resize_h = int(resize_ratio * h_org)
    resized_image = cv2.resize(original_image, (resize_w, resize_h))

    image_paded = np.full((h_target, w_target, 3), 128.0)
    dw = int((w_target - resize_w) / 2)
    dh = int((h_target - resize_h) / 2)
    image_paded[dh:resize_h+dh, dw:resize_w+dw,:] = resized_image
    input_image = image_paded / 255.0
    input_image = input_image[np.newaxis, ...]

    feed_list = []
    # input/input_data:0
    feed_list.append(input_image)
    # input/is_train:0
    feed_list.append(False)

    return original_image, feed_list

