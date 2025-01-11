# src/helpers/radiograph_image_helper.py
import cv2
import numpy as np

def preprocess_image(image_path, target_size=(256, 256)):
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    original_size = image.shape[:2]
    resized_image = cv2.resize(image, target_size)
    normalized_image = resized_image / 255.0
    input_image = np.expand_dims(normalized_image, axis=0)
    return input_image, original_size

def postprocess_prediction(prediction, original_size):
    predicted_mask = np.squeeze(prediction)
    predicted_classes = np.argmax(predicted_mask, axis=-1)
    resized_prediction = cv2.resize(predicted_classes.astype(np.uint8), (original_size[1], original_size[0]), interpolation=cv2.INTER_NEAREST)
    return resized_prediction

def convert_class_to_rgb(mask_class, class_colors):
    height, width = mask_class.shape
    mask_rgb = np.zeros((height, width, 3), dtype='uint8')
    for class_id, rgb in enumerate(class_colors.values()):
        mask_rgb[mask_class == class_id] = rgb
    return mask_rgb
