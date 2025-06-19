from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RadiographBase(BaseModel):
    patient_name: str
    status_detection: str

class RadiographCreate(RadiographBase):
    pass

class FilterResponse(BaseModel):
    message: str
    radiograph_id: int
    filtered_image: str
    selected_categories: list[str]

class Radiograph(RadiographBase):
    id: int
    tasks: str
    original: str
    mask_file: Optional[str] = None
    overlay: Optional[str] = None
    has_lesi_periapikal: bool = False
    has_resorpsi: bool = False
    has_karies: bool = False
    has_impaksi: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PredictResponse(BaseModel):
    message: str
    patient_name: str
    status_detection: str
    original_file: Optional[str] = None
    mask_file: Optional[str] = None
    overlay_file: Optional[str] = None
    image: Optional[str] = None
    detected_conditions: dict
    task_id: str