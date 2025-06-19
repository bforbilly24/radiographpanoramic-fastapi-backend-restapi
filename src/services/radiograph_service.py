import tensorflow as tf
import numpy as np
import cv2
import os
import base64
from pathlib import Path
from typing import Tuple, Dict, List, Optional
from fastapi import UploadFile, HTTPException
from PIL import Image
import logging
from io import BytesIO

logging.basicConfig(level=logging.INFO)

classes = {
    "Impaksi": [184, 61, 245],
    "Karies": [221, 255, 51],
    "Lesi_Periapikal": [42, 125, 209],
    "Resorpsi": [250, 50, 83],
    "background": [0, 0, 0],
}

CONDITIONS = {
    "Impaksi": [184, 61, 245],
    "Karies": [221, 255, 51],
    "Lesi_Periapikal": [42, 125, 209],
    "Resorpsi": [250, 50, 83],
}

MASK_COLOR_MAPPINGS = {}

async def load_model(model_path: str):
    try:
        # Load model without compilation to avoid custom objects issues
        model = tf.keras.models.load_model(model_path, compile=False)
        return model
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

def apply_clahe(img):
    """Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)"""
    try:
        lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        merged = cv2.merge((cl, a, b))
        return cv2.cvtColor(merged, cv2.COLOR_LAB2RGB)
    except Exception as e:
        logging.warning(f"CLAHE application failed, using original image: {str(e)}")
        return img

def apply_gamma(img, gamma=1.5):
    """Apply gamma correction"""
    try:
        inv_gamma = 1.0 / gamma
        table = np.array([(i / 255.0) ** inv_gamma * 255 for i in np.arange(256)]).astype("uint8")
        return cv2.LUT(img, table)
    except Exception as e:
        logging.warning(f"Gamma correction failed, using original image: {str(e)}")
        return img

async def preprocess_image_4patch(image_path: str, target_size: Tuple[int, int] = (512, 256)):
    """
    Preprocess image for 4-patch model:
    - Resize to 512x256
    - Split into 4 patches of 256x128 each
    - Apply CLAHE and gamma correction
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise HTTPException(status_code=400, detail="Failed to read image")
        
        # Convert BGR to RGB
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        original_size = image.shape[:2]
        
        # Resize to target size (512x256)
        resized_image = cv2.resize(image, target_size)
        
        # Define patch dimensions
        patch_h, patch_w = 128, 256
        patches = []
        
        # Split into 4 patches (2x2 grid)
        for i in range(2):  # Vertical
            for j in range(2):  # Horizontal
                y0, y1 = i * patch_h, (i + 1) * patch_h
                x0, x1 = j * patch_w, (j + 1) * patch_w
                patch = resized_image[y0:y1, x0:x1]
                
                # Apply preprocessing to each patch
                patch = apply_clahe(patch)
                patch = apply_gamma(patch)
                patch = patch / 255.0  # Normalize
                patches.append(patch)
        
        patches_array = np.array(patches)
        logging.info(f"Created {len(patches)} patches with shape: {patches_array.shape}")
        
        return patches_array, original_size, resized_image
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image preprocessing failed: {str(e)}")

async def postprocess_prediction_4patch(predictions, target_size: Tuple[int, int] = (512, 256)):
    """
    Postprocess predictions from 4-patch model:
    - Combine 4 patch predictions into single mask
    - Convert to class indices
    """
    try:
        if len(predictions) != 4:
            raise HTTPException(status_code=500, detail=f"Expected 4 patch predictions, got {len(predictions)}")
        
        # Get predicted classes for each patch
        predicted_classes_patches = []
        for pred in predictions:
            if len(pred.shape) >= 3:
                pred_squeezed = np.squeeze(pred)
                if len(pred_squeezed.shape) == 3:
                    predicted_classes_patches.append(np.argmax(pred_squeezed, axis=-1))
                else:
                    predicted_classes_patches.append(pred_squeezed)
            else:
                predicted_classes_patches.append(pred)
        
        # Initialize full mask
        full_mask = np.zeros(target_size[::-1], dtype=np.uint8)  # (width, height) -> (height, width)
        patch_h, patch_w = 128, 256
        
        # Combine patches back into full mask
        idx = 0
        for i in range(2):  # Vertical
            for j in range(2):  # Horizontal
                y0, y1 = i * patch_h, (i + 1) * patch_h
                x0, x1 = j * patch_w, (j + 1) * patch_w
                full_mask[y0:y1, x0:x1] = predicted_classes_patches[idx]
                idx += 1
        
        unique_classes = np.unique(full_mask)
        logging.info(f"Unique class indices in combined prediction: {unique_classes}")
        
        return full_mask
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction postprocessing failed: {str(e)}")

async def convert_class_to_rgb(mask_class: np.ndarray, class_colors: Dict, mask_file_path: str):
    try:
        height, width = mask_class.shape
        mask_rgb = np.zeros((height, width, 3), dtype="uint8")
        class_list = list(class_colors.values())
        for class_id, color in enumerate(class_list):
            mask_rgb[mask_class == class_id] = color
        unique_colors = np.unique(mask_rgb.reshape(-1, mask_rgb.shape[2]), axis=0)
        logging.info(f"Unique colors in converted mask before saving: {unique_colors}")
        return mask_rgb
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RGB conversion failed: {str(e)}")

async def create_overlay_image(original_image: np.ndarray, predicted_mask_rgb: np.ndarray, image_path: str) -> Tuple[str, str]:
    try:
        predicted_mask_rgb = cv2.resize(predicted_mask_rgb, (original_image.shape[1], original_image.shape[0]))
        alpha = 0.5
        overlay = original_image.copy()
        cv2.addWeighted(predicted_mask_rgb, alpha, overlay, 1 - alpha, 0, overlay)

        _, buffer = cv2.imencode(".jpg", cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])
        encoded_image = base64.b64encode(buffer).decode("utf-8")

        if len(encoded_image) < 100:
            raise HTTPException(status_code=500, detail="Generated base64 image string is too short or invalid")

        base_filename = os.path.basename(image_path)
        overlay_filename = f"overlay_{base_filename}"
        overlay_path = os.path.join("uploads", "overlay", overlay_filename)
        os.makedirs(os.path.dirname(overlay_path), exist_ok=True)
        cv2.imwrite(overlay_path, cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])

        logging.info(f"Overlay image created at {overlay_path}, base64 length: {len(encoded_image)}")
        return encoded_image, overlay_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create overlay: {str(e)}")

async def predict_image(model, image_path: str):
    """
    Updated prediction function for 4-patch model with improved mask handling
    """
    try:
        os.makedirs("uploads/masks", exist_ok=True)
        
        # Store original image dimensions for later use
        original_image = cv2.imread(image_path)
        original_image_rgb = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
        original_height, original_width = original_image_rgb.shape[:2]
        
        # Preprocess image into 4 patches
        patches_array, original_size, processed_image = await preprocess_image_4patch(image_path)
        
        # Predict on all patches at once
        predictions = model.predict(patches_array, batch_size=4)
        logging.info(f"Model prediction shape: {predictions.shape if hasattr(predictions, 'shape') else type(predictions)}")
        
        # If predictions is a single array, split it back into patches
        if hasattr(predictions, 'shape') and len(predictions.shape) == 4:
            # predictions shape: (4, height, width, classes)
            patch_predictions = [predictions[i] for i in range(4)]
        else:
            patch_predictions = predictions
        
        # Postprocess predictions to combine patches
        predicted_mask = await postprocess_prediction_4patch(patch_predictions)
        
        # Generate file paths
        base_filename = os.path.basename(image_path)
        mask_filename = f"mask_{base_filename.rsplit('.', 1)[0]}.png"
        mask_file_path = os.path.join("uploads", "masks", mask_filename)
        
        # Convert class indices to RGB
        predicted_mask_rgb = await convert_class_to_rgb(predicted_mask, classes, mask_file_path)
        
        # **IMPORTANT: Resize mask to match original image dimensions before saving**
        # This ensures the saved mask can be properly used in filtering
        if predicted_mask_rgb.shape[:2] != (original_height, original_width):
            logging.info(f"Resizing mask from {predicted_mask_rgb.shape[:2]} to ({original_height}, {original_width})")
            predicted_mask_rgb = cv2.resize(predicted_mask_rgb, (original_width, original_height), 
                                          interpolation=cv2.INTER_NEAREST)
        
        # Save mask using PIL to preserve exact colors
        mask_pil = Image.fromarray(predicted_mask_rgb)
        mask_pil.save(mask_file_path, format="PNG", compress_level=0)
        
        # Verify saved mask colors
        saved_mask = cv2.imread(mask_file_path, cv2.IMREAD_COLOR)
        saved_mask = cv2.cvtColor(saved_mask, cv2.COLOR_BGR2RGB)
        unique_colors_saved = np.unique(saved_mask.reshape(-1, saved_mask.shape[2]), axis=0)
        logging.info(f"Unique colors in saved mask: {unique_colors_saved}")
        logging.info(f"Saved mask dimensions: {saved_mask.shape[:2]}")

        # Detect conditions
        detected_conditions = {
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
                    logging.info(f"Detected {condition_name} with {np.sum(condition_mask)} pixels")

        # Create overlay with original image (mask is already the right size)
        encoded_overlay, overlay_path = await create_overlay_image(original_image_rgb, predicted_mask_rgb, image_path)
        return encoded_overlay, mask_file_path, detected_conditions, overlay_path
        
    except Exception as e:
        logging.error(f"Prediction error details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
    
async def apply_filters(original_image_path: str, mask_path: str, selected_conditions: List[str]):
    try:
        abs_mask_path = os.path.abspath(mask_path)
        if not os.path.exists(abs_mask_path):
            raise HTTPException(status_code=404, detail=f"Mask file not found at {abs_mask_path}")
        mask_image = cv2.imread(abs_mask_path, cv2.IMREAD_COLOR)
        if mask_image is None:
            raise HTTPException(status_code=400, detail=f"Failed to load mask at {abs_mask_path}")
        mask_image = cv2.cvtColor(mask_image, cv2.COLOR_BGR2RGB)

        unique_colors = np.unique(mask_image.reshape(-1, mask_image.shape[2]), axis=0)
        logging.info(f"Unique colors in mask image: {unique_colors}")

        abs_original_path = os.path.abspath(original_image_path)
        if not os.path.exists(abs_original_path):
            raise HTTPException(status_code=404, detail=f"Original image not found at {abs_original_path}")
        original_image = cv2.imread(abs_original_path, cv2.IMREAD_COLOR)
        if original_image is None:
            raise HTTPException(status_code=400, detail=f"Failed to load original image at {abs_original_path}")
        original_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)

        # Resize mask to match original image dimensions
        mask_image = cv2.resize(mask_image, (original_image.shape[1], original_image.shape[0]))

        valid_conditions = [cond for cond in selected_conditions if cond in CONDITIONS]
        logging.info(f"Selected conditions: {selected_conditions}")
        logging.info(f"Valid conditions: {valid_conditions}")

        blended_filtered = original_image.copy().astype(np.uint8)
        filtered_mask = np.zeros_like(original_image, dtype=np.uint8)

        if valid_conditions:
            for condition in valid_conditions:
                expected_color = np.array(CONDITIONS[condition], dtype=np.uint8)
                logging.info(f"Processing condition {condition} with expected color {expected_color}")
                
                # Try exact match first
                condition_mask = np.all(mask_image == expected_color, axis=-1)
                pixel_count = np.sum(condition_mask)
                logging.info(f"Exact match: Found {pixel_count} pixels for {condition} with color {expected_color}")
                
                # Fallback to color tolerance if no exact match
                if pixel_count == 0:
                    color_diffs = np.abs(mask_image - expected_color).sum(axis=-1)
                    condition_mask = color_diffs <= 15  # Tolerance of ±5 per channel
                    pixel_count = np.sum(condition_mask)
                    logging.info(f"Tolerance match: Found {pixel_count} pixels for {condition} within tolerance")
                
                if pixel_count > 0:
                    filtered_mask[condition_mask] = expected_color
                else:
                    logging.warning(f"No pixels found for {condition} with color {expected_color} or within tolerance")

            logging.info(f"Filtered mask pixel sum: {np.sum(filtered_mask)}")
            if np.sum(filtered_mask) > 0:
                alpha = 0.5
                filtered_mask_float = filtered_mask.astype(np.float32) / 255.0
                blended_filtered_float = blended_filtered.astype(np.float32) / 255.0
                cv2.addWeighted(filtered_mask_float, alpha, blended_filtered_float, 1 - alpha, 0, blended_filtered_float)
                blended_filtered = (blended_filtered_float * 255).astype(np.uint8)
            else:
                logging.warning("Filtered mask is empty, returning original image with message")
                return (
                    base64.b64encode(cv2.imencode(".jpg", cv2.cvtColor(original_image, cv2.COLOR_RGB2BGR))[1]).decode("utf-8"),
                    "No valid pixels found for selected conditions. The mask may not contain the expected colors."
                )

        _, buffer = cv2.imencode(".jpg", cv2.cvtColor(blended_filtered, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])
        encoded_image = base64.b64encode(buffer).decode("utf-8")

        if len(encoded_image) < 100:
            raise HTTPException(status_code=500, detail="Generated filtered base64 image string is too short or invalid")

        logging.info(f"Encoded filtered overlay length: {len(encoded_image)}")
        return encoded_image, None
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Filter application failed: {str(e)}")
    try:
        abs_mask_path = os.path.abspath(mask_path)
        if not os.path.exists(abs_mask_path):
            raise HTTPException(status_code=404, detail=f"Mask file not found at {abs_mask_path}")
        mask_image = cv2.imread(abs_mask_path, cv2.IMREAD_COLOR)
        if mask_image is None:
            raise HTTPException(status_code=400, detail=f"Failed to load mask at {abs_mask_path}")
        mask_image = cv2.cvtColor(mask_image, cv2.COLOR_BGR2RGB)

        unique_colors = np.unique(mask_image.reshape(-1, mask_image.shape[2]), axis=0)
        logging.info(f"Unique colors in mask image: {unique_colors}")

        abs_original_path = os.path.abspath(original_image_path)
        if not os.path.exists(abs_original_path):
            raise HTTPException(status_code=404, detail=f"Original image not found at {abs_original_path}")
        original_image = cv2.imread(abs_original_path, cv2.IMREAD_COLOR)
        if original_image is None:
            raise HTTPException(status_code=400, detail=f"Failed to load original image at {abs_original_path}")
        original_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)

        valid_conditions = [cond for cond in selected_conditions if cond in CONDITIONS]
        logging.info(f"Selected conditions: {selected_conditions}")
        logging.info(f"Valid conditions: {valid_conditions}")

        blended_filtered = original_image.copy().astype(np.uint8)
        filtered_mask = np.zeros_like(mask_image, dtype=np.uint8)

        if valid_conditions:
            for condition in valid_conditions:
                expected_color = np.array(CONDITIONS[condition], dtype=np.uint8)
                logging.info(f"Processing condition {condition} with expected color {expected_color}")
                
                # Try exact match first
                condition_mask = np.all(mask_image == expected_color, axis=-1)
                pixel_count = np.sum(condition_mask)
                logging.info(f"Exact match: Found {pixel_count} pixels for {condition} with color {expected_color}")
                
                # Fallback to color tolerance if no exact match
                if pixel_count == 0:
                    color_diffs = np.abs(mask_image - expected_color).sum(axis=-1)
                    condition_mask = color_diffs <= 15  # Tolerance of ±5 per channel
                    pixel_count = np.sum(condition_mask)
                    logging.info(f"Tolerance match: Found {pixel_count} pixels for {condition} within tolerance")
                
                if pixel_count > 0:
                    filtered_mask[condition_mask] = expected_color
                else:
                    logging.warning(f"No pixels found for {condition} with color {expected_color} or within tolerance")

            logging.info(f"Filtered mask pixel sum: {np.sum(filtered_mask)}")
            if np.sum(filtered_mask) > 0:
                alpha = 0.5
                filtered_mask_float = filtered_mask.astype(np.float32) / 255.0
                blended_filtered_float = blended_filtered.astype(np.float32) / 255.0
                cv2.addWeighted(filtered_mask_float, alpha, blended_filtered_float, 1 - alpha, 0, blended_filtered_float)
                blended_filtered = (blended_filtered_float * 255).astype(np.uint8)
            else:
                logging.warning("Filtered mask is empty, returning original image with message")
                return (
                    base64.b64encode(cv2.imencode(".jpg", cv2.cvtColor(original_image, cv2.COLOR_RGB2BGR))[1]).decode("utf-8"),
                    "No valid pixels found for selected conditions. The mask may not contain the expected colors."
                )

        _, buffer = cv2.imencode(".jpg", cv2.cvtColor(blended_filtered, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])
        encoded_image = base64.b64encode(buffer).decode("utf-8")

        if len(encoded_image) < 100:
            raise HTTPException(status_code=500, detail="Generated filtered base64 image string is too short or invalid")

        logging.info(f"Encoded filtered overlay length: {len(encoded_image)}")
        return encoded_image, None
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Filter application failed: {str(e)}")