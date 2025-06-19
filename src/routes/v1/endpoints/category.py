# src/routes/v1/endpoints/category.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from src.utils.dependencies import get_db, get_current_user
from src.controllers.category_controller import get_categories, create_category
from src.schemas.category_schema import CategoryCreate, Category as CategorySchema
from src.models.user_model import User

router = APIRouter()

@router.get("", response_model=List[CategorySchema])
async def get_categories_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_categories(db)

@router.post("", response_model=CategorySchema)
async def create_category_endpoint(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_category(category, db)