from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import List
from src.utils.dependencies import get_db, get_current_user
from src.models.radiograph_model import Radiograph
from src.services.radiograph_service import load_model, predict_image
from src.models.user_model import User
import os

router = APIRouter()


@router.post("/predict")
async def predict_radiograph(
    file: UploadFile = File(...),
    patient_name: str = Form(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    os.makedirs("uploads/original", exist_ok=True)
    original_file_path = os.path.join("uploads", "original", file.filename)

    with open(original_file_path, "wb+") as file_object:
        file_object.write(await file.read())

    try:
        status_detection = "process"

        # Load model
        model = await load_model("src/ml_models/unet_gigi_penyakit.h5")

        # Lakukan prediksi
        encoded_image, predicted_file_path, detected_conditions = await predict_image(
            model, original_file_path
        )

        status_detection = "success"

        # Simpan data radiograph ke database
        new_radiograph = Radiograph.create_and_generate_task(
            db=db,
            patient_name=patient_name,
            original=original_file_path,
            status_detection=status_detection,
            predicted=predicted_file_path,
        )

        new_radiograph.has_lesi_periapikal = detected_conditions.get(
            "has_lesi_periapikal", False
        )
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
            "original_file": original_file_path,
            "predicted_file": predicted_file_path,
            "image": encoded_image,
            "detected_conditions": detected_conditions,
            "task_id": new_radiograph.tasks,
        }

    except Exception as e:
        status_detection = "failed"
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/filter")
async def filter_radiographs(
    conditions: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Radiograph)

    if "Lesi Periapikal" in conditions:
        query = query.filter(Radiograph.has_lesi_periapikal.is_(True))
    if "Resorpsi" in conditions:
        query = query.filter(Radiograph.has_resorpsi.is_(True))
    if "Karies" in conditions:
        query = query.filter(Radiograph.has_karies.is_(True))
    if "Impaksi" in conditions:
        query = query.filter(Radiograph.has_impaksi.is_(True))

    radiographs = query.all()
    return radiographs


@router.delete("/{radiograph_id}")
async def delete_radiograph(
    radiograph_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # Find the radiograph
        radiograph = db.query(Radiograph).filter(Radiograph.id == radiograph_id).first()

        if not radiograph:
            raise HTTPException(
                status_code=404, detail=f"Radiograph with ID {radiograph_id} not found"
            )

        # Delete the physical files
        files_to_delete = [radiograph.original, radiograph.predicted]

        for file_path in files_to_delete:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as e:
                    print(f"Error deleting file {file_path}: {e}")

        # Delete from database
        db.delete(radiograph)
        db.commit()

        return {
            "status_code": 200,
            "message": f"Radiograph with ID {radiograph_id} has been deleted successfully",
            "data": None,
            "error": None,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while deleting the radiograph: {str(e)}",
        )
