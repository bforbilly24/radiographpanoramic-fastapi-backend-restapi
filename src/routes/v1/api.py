# src/app/v1/api.py
from fastapi import APIRouter
from src.routes.v1.endpoints import auth, category, radiograph

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(category.router, prefix="/categories", tags=["categories"])
api_router.include_router(radiograph.router, prefix="/radiograph", tags=["radiograph"])
