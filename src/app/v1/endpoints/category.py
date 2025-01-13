# src/app/v1/endpoints/category.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from src.utils.dependencies import get_db, get_current_user
from src.models.category_model import Category
from src.schemas.category_schema import CategoryCreate, Category as CategorySchema
from src.models.user_model import User

router = APIRouter()

@router.get("", response_model=List[CategorySchema])
async def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    categories = db.query(Category).all()
    return categories

@router.post("", response_model=CategorySchema)
async def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    db_category = Category(name=category.name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category
