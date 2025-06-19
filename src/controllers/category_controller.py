# src/controllers/radiograph_controller.py
from sqlalchemy.orm import Session
from fastapi import HTTPException
from src.models.category_model import Category
from src.schemas.category_schema import CategoryCreate
from typing import List

def get_categories(db: Session) -> List[Category]:
    return db.query(Category).all()

def create_category(category: CategoryCreate, db: Session) -> Category:
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    db_category = Category(name=category.name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category