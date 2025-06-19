from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from src.db.base import Base
from typing import Optional
from sqlalchemy.orm import Session

class Radiograph(Base):
    __tablename__ = "radiographs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tasks = Column(String(50), unique=True, nullable=False)
    patient_name = Column(String(255), nullable=False)
    original = Column(String(255), nullable=False)
    status_detection = Column(
        Enum("success", "in progress", "failed", name="status_enum"), nullable=False
    )
    mask_file = Column(String(255), nullable=True) 
    overlay = Column(String(255), nullable=True)
    has_lesi_periapikal = Column(Boolean, default=False)
    has_resorpsi = Column(Boolean, default=False)
    has_karies = Column(Boolean, default=False)
    has_impaksi = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @staticmethod
    def generate_task_id(db: Session) -> str:
        last_task = db.query(Radiograph).order_by(Radiograph.id.desc()).first()
        next_task_number = 1 if last_task is None else last_task.id + 1
        return f"task-{next_task_number}"

    @classmethod
    def create_and_generate_task(
        cls,
        db: Session,
        patient_name: str,
        original: str,
        status_detection: str,
        mask_file: Optional[str] = None,
        overlay: Optional[str] = None,
        **kwargs,
    ):
        task_id = cls.generate_task_id(db)
        new_radiograph = cls(
            tasks=task_id,
            patient_name=patient_name,
            original=original,
            status_detection=status_detection,
            mask_file=mask_file,
            overlay=overlay,
            **kwargs,
        )
        db.add(new_radiograph)
        db.commit()
        db.refresh(new_radiograph)
        return new_radiograph