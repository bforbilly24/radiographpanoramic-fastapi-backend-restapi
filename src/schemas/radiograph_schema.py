# src/schemas/radiograph_schema.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RadiographBase(BaseModel):
    patient_name: str
    status_detection: str

class RadiographCreate(RadiographBase):
    pass

class Radiograph(RadiographBase):
    id: int
    tasks: str
    original: str
    predicted: Optional[str] = None
    has_lesi_periapikal: bool = False
    has_resorpsi: bool = False
    has_karies: bool = False
    has_impaksi: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True