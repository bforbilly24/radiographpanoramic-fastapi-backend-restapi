from fastapi import HTTPException, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Tuple
from src.models.radiograph_model import Radiograph
from src.services.radiograph_service import load_model, predict_image, apply_filters
from src.models.user_model import User
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BulkDeleteRequest:
    ids: List[int]

def get_radiographs(page: int, limit: int, db: Session, current_user: User) -> Dict:
    try:
        total = db.query(Radiograph).count()
        offset = (page - 1) * limit
        radiographs = db.query(Radiograph).offset(offset).limit(limit).all()
        result = []
        for r in radiographs:
            result.append(
                {
                    "id": r.id,
                    "patient_name": r.patient_name,
                    "status_detection": r.status_detection,
                    "original_file": r.original if r.original and os.path.exists(r.original) else None,
                    "mask_file": r.mask_file if r.mask_file and os.path.exists(r.mask_file) else None,
                    "overlay_file": r.overlay if r.overlay and os.path.exists(r.overlay) else None,
                    "detected_conditions": {
                        "has_impaksi": r.has_impaksi,
                        "has_karies": r.has_karies,
                        "has_lesi_periapikal": r.has_lesi_periapikal,
                        "has_resorpsi": r.has_resorpsi,
                    },
                    "task_id": r.tasks,
                    "created_at": r.created_at,
                }
            )
        return {
            "data": result,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit,
            },
        }
    except Exception as e:
        logger.error(f"Failed to retrieve radiographs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve radiographs: {str(e)}")

async def predict_radiograph(file: UploadFile, patient_name: str, db: Session, current_user: User) -> Dict:
    os.makedirs("uploads/original", exist_ok=True)
    original_file_path = os.path.join("uploads", "original", file.filename)
    with open(original_file_path, "wb") as file_object:
        content = await file.read()
        file_object.write(content)
    try:
        status_detection = "process"
        model = await load_model("src/ml_models/unet_gigi_penyakit_crop_256_512.h5")
        encoded_overlay, mask_file_path, detected_conditions, overlay_file_path = await predict_image(model, original_file_path)
        status_detection = "success"
        new_radiograph = Radiograph.create_and_generate_task(
            db=db,
            patient_name=patient_name,
            original=original_file_path,
            status_detection=status_detection,
            mask_file=mask_file_path,
            overlay=overlay_file_path,
        )
        new_radiograph.has_lesi_periapikal = detected_conditions.get("has_lesi_periapikal", False)
        new_radiograph.has_resorpsi = detected_conditions.get("has_resorpsi", False)
        new_radiograph.has_karies = detected_conditions.get("has_karies", False)
        new_radiograph.has_impaksi = detected_conditions.get("has_impaksi", False)
        db.add(new_radiograph)
        db.commit()
        db.refresh(new_radiograph)
        return {
            "message": "Prediction successful",
            "patient_name": patient_name,
            "status_detection": status_detection,
            "original_file": original_file_path if os.path.exists(original_file_path) else None,
            "mask_file": mask_file_path if os.path.exists(mask_file_path) else None,
            "overlay_file": overlay_file_path if os.path.exists(overlay_file_path) else None,
            "image": encoded_overlay,
            "detected_conditions": detected_conditions,
            "task_id": new_radiograph.tasks,
            "created_at": new_radiograph.created_at,
        }
    except Exception as e:
        status_detection = "failed"
        logger.error(f"Prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

async def filter_radiograph(radiograph_id: int, selected_categories: List[str], db: Session, current_user: User) -> Dict:
    try:
        radiograph = db.query(Radiograph).filter(Radiograph.id == radiograph_id).first()
        if not radiograph:
            raise HTTPException(status_code=404, detail="Radiograph not found")
        if not radiograph.mask_file or not os.path.exists(radiograph.mask_file):
            raise HTTPException(status_code=404, detail="Mask file not found")
        if not radiograph.original or not os.path.exists(radiograph.original):
            raise HTTPException(status_code=404, detail="Original image not found")
        # Always pass the original image path, not the overlay
        encoded_filtered_image, message = await apply_filters(
            radiograph.original,  # Use original image
            radiograph.mask_file,
            selected_categories
        )
        return {
            "message": message or "Filter applied successfully",
            "radiograph_id": radiograph_id,
            "filtered_image": encoded_filtered_image,
            "selected_categories": selected_categories,
        }
    except Exception as e:
        logger.error(f"Filter application failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Filter application failed: {str(e)}")

def bulk_delete_radiographs(request: BulkDeleteRequest, db: Session, current_user: User) -> Dict:
    try:
        if not request.ids:
            raise HTTPException(status_code=400, detail="No IDs provided for deletion")
        existing_records = db.query(Radiograph).filter(Radiograph.id.in_(request.ids)).all()
        existing_ids = {record.id for record in existing_records}
        non_existent_ids = set(request.ids) - existing_ids
        if non_existent_ids:
            logger.warning(f"Some IDs not found: {non_existent_ids}")
        for record in existing_records:
            for file_path in [record.original, record.mask_file, record.overlay]:
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logger.info(f"Deleted file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete file {file_path}: {str(e)}")
        deleted_count = (
            db.query(Radiograph)
            .filter(Radiograph.id.in_(request.ids))
            .delete(synchronize_session=False)
        )
        db.commit()
        logger.info(f"Deleted {deleted_count} radiograph records")
        return {
            "message": "Bulk deletion successful",
            "deleted_count": deleted_count,
            "non_existent_ids": list(non_existent_ids) if non_existent_ids else None,
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete radiographs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete radiographs: {str(e)}")

def delete_radiograph(id: int, db: Session, current_user: User) -> Dict:
    try:
        record = db.query(Radiograph).filter(Radiograph.id == id).first()
        if not record:
            raise HTTPException(status_code=404, detail="Radiograph not found")
        for file_path in [record.original, record.mask_file, record.overlay]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete file {file_path}: {str(e)}")
        db.delete(record)
        db.commit()
        logger.info(f"Deleted radiograph with ID: {id}")
        return {"message": "Radiograph deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete radiograph: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete radiograph: {str(e)}")