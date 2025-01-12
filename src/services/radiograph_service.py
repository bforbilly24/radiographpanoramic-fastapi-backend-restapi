# src/services/radiograph_service.py
import tensorflow as tf
import numpy as np
import cv2
import os
import base64
from pathlib import Path

classes = {
    "Gigi Sehat": [51, 221, 255],
    "Impaksi": [184, 61, 245],
    "Karies": [221, 255, 51],
    "Lesi Periapikal": [42, 125, 209],
    "Resorpsi": [250, 50, 83],
    "background": [0, 0, 0],
}

def load_model(model_path):
    """Loads the model from the file system."""
    model = tf.keras.models.load_model(model_path)
    return model


def preprocess_image(image_path, target_size=(256, 256)):
    """Read and preprocess the image for prediction."""
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    original_size = image.shape[:2]

    resized_image = cv2.resize(image, target_size)
    normalized_image = resized_image / 255.0

    input_image = np.expand_dims(normalized_image, axis=0)
    return input_image, original_size


def postprocess_prediction(prediction, original_size):
    """Resize the prediction to match the original image size."""
    predicted_mask = np.squeeze(prediction)
    predicted_classes = np.argmax(predicted_mask, axis=-1)
    resized_prediction = cv2.resize(
        predicted_classes.astype(np.uint8),
        (original_size[1], original_size[0]),
        interpolation=cv2.INTER_NEAREST,
    )
    return resized_prediction


def convert_class_to_rgb(mask_class, class_colors):
    """Convert class indices to RGB color masks."""
    height, width = mask_class.shape
    mask_rgb = np.zeros((height, width, 3), dtype="uint8")

    for class_id, rgb in enumerate(class_colors.values()):
        mask_rgb[mask_class == class_id] = rgb

    return mask_rgb


def predict_image(model, image_path):
    try:
        os.makedirs("uploads/predicted", exist_ok=True)

        input_image, original_size = preprocess_image(image_path)

        prediction = model.predict(input_image)

        predicted_mask = postprocess_prediction(prediction, original_size)

        predicted_mask_rgb = convert_class_to_rgb(predicted_mask, classes)

        predicted_filename = "predicted_" + os.path.basename(image_path)
        predicted_file_path = os.path.join("uploads", "predicted", predicted_filename)
        cv2.imwrite(
            predicted_file_path, cv2.cvtColor(predicted_mask_rgb, cv2.COLOR_RGB2BGR)
        )

        detected_conditions = {
            "has_gigi_sehat": False,
            "has_impaksi": False,
            "has_karies": False,
            "has_lesi_periapikal": False,
            "has_resorpsi": False,
        }

        for condition_name, rgb_color in classes.items():
            if condition_name != "background": 
                condition_key = f"has_{condition_name.lower().replace(' ', '_')}"
                condition_mask = np.all(predicted_mask_rgb == rgb_color, axis=-1)
                if np.any(condition_mask):
                    detected_conditions[condition_key] = True

        with open(predicted_file_path, "rb") as img_file:
            encoded_image = base64.b64encode(img_file.read()).decode("utf-8")

        return encoded_image, predicted_file_path, detected_conditions

    except Exception as e:
        raise Exception(f"Prediction failed: {str(e)}")


CONDITIONS = {
    "Impaksi": [184, 61, 245],
    "Karies": [221, 255, 51],
    "Lesi_Periapikal": [42, 125, 209],
    "Resorpsi": [250, 50, 83],
}

def apply_filters(image_path, selected_conditions):
    """
    Apply selected filters to show only specific conditions in the radiograph.

    Args:
        image_path (str): Path to the predicted image
        selected_conditions (list): List of condition names to show

    Returns:
        tuple: (base64 encoded filtered image, path to filtered image)
    """
    try:
        abs_image_path = os.path.abspath(image_path)

        if not os.path.exists(abs_image_path):
            raise FileNotFoundError(f"Image file not found at {abs_image_path}")

        image = cv2.imread(abs_image_path)
        if image is None:
            raise ValueError(f"Failed to load image at {abs_image_path}")

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        mask = np.zeros_like(image)

        for condition in selected_conditions:
            if condition in CONDITIONS:
                color = CONDITIONS[condition]
                condition_mask = np.all(image == color, axis=-1)
                mask[condition_mask] = image[condition_mask]

        filtered_dir = os.path.join("uploads", "filtered")
        os.makedirs(filtered_dir, exist_ok=True)

        base_filename = os.path.basename(image_path)
        filtered_filename = f"filtered_{base_filename}"
        filtered_path = os.path.join(filtered_dir, filtered_filename)

        cv2.imwrite(filtered_path, cv2.cvtColor(mask, cv2.COLOR_RGB2BGR))

        if not os.path.exists(filtered_path):
            raise IOError("Failed to save filtered image")

        with open(filtered_path, "rb") as img_file:
            encoded_image = base64.b64encode(img_file.read()).decode("utf-8")

        return encoded_image, filtered_path

    except FileNotFoundError as e:
        raise Exception(f"File error: {str(e)}")
    except ValueError as e:
        raise Exception(f"Image processing error: {str(e)}")
    except Exception as e:
        raise Exception(f"Filter application failed: {str(e)}")
