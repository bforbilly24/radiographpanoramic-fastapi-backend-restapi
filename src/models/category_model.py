# src/models/category_model.py
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from src.db.session import Base

class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Category {self.name}>"
