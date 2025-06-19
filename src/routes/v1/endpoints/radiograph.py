from fastapi import APIRouter, Depends, File, Form, UploadFile, Query
from sqlalchemy.orm import Session
from typing import List
from src.utils.dependencies import get_db, get_current_user
from src.controllers.radiograph_controller import get_radiographs, predict_radiograph, filter_radiograph, bulk_delete_radiographs, delete_radiograph
from src.models.user_model import User
from src.schemas.radiograph_schema import FilterResponse, PredictResponse
from pydantic import BaseModel

router = APIRouter(tags=["radiograph"])

class BulkDeleteRequest(BaseModel):
    ids: List[int]

class FilterRequest(BaseModel):
    radiograph_id: int
    selected_categories: List[str]

@router.get("/data", response_model=dict)
async def get_radiographs_endpoint(
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_radiographs(page, limit, db, current_user)

@router.post("/predict", response_model=PredictResponse, status_code=200)
async def predict_radiograph_endpoint(
    file: UploadFile = File(...),
    patient_name: str = Form(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await predict_radiograph(file, patient_name, db, current_user)

@router.post("/filter", response_model=FilterResponse, status_code=200)
async def filter_radiograph_endpoint(
    request: FilterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await filter_radiograph(request.radiograph_id, request.selected_categories, db, current_user)

@router.delete("/bulk", status_code=200)
async def bulk_delete_radiographs_endpoint(
    request: BulkDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return bulk_delete_radiographs(request, db, current_user)

@router.delete("/{id}", status_code=200)
async def delete_radiograph_endpoint(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return delete_radiograph(id, db, current_user)