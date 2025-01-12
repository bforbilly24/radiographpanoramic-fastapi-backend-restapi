# src/models/radiograph_model.py
from datetime import datetime
from src.extensions import db
from werkzeug.utils import secure_filename

class Radiograph(db.Model):
    __tablename__ = 'radiographs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tasks = db.Column(db.String(50), unique=True, nullable=False)
    patient_name = db.Column(db.String(255), nullable=False)
    original = db.Column(db.String(255), nullable=False)
    status_detection = db.Column(db.Enum('success', 'in progress', 'failed', name='status_enum'), nullable=False)
    predicted = db.Column(db.String(255), nullable=True)
    has_lesi_periapikal = db.Column(db.Boolean, default=False)
    has_resorpsi = db.Column(db.Boolean, default=False)       
    has_karies = db.Column(db.Boolean, default=False)         
    has_impaksi = db.Column(db.Boolean, default=False)        
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, patient_name, original, status_detection, predicted=None):
        self.patient_name = patient_name
        self.original = original
        self.status_detection = status_detection
        self.predicted = predicted

    def __repr__(self):
        return f"<Radiograph {self.patient_name} - {self.tasks}>"

    @staticmethod
    def generate_task_id():
        last_task = Radiograph.query.order_by(Radiograph.id.desc()).first()
        next_task_number = 1 if last_task is None else last_task.id + 1
        return f'task-{next_task_number}'

    @classmethod
    def create_and_generate_task(cls, patient_name, original, status_detection, predicted=None):
        task_id = cls.generate_task_id()
        new_radiograph = cls(
            patient_name=patient_name,
            original=original,
            status_detection=status_detection,
            predicted=predicted
        )
        new_radiograph.tasks = task_id
        db.session.add(new_radiograph)
        db.session.commit()
        return new_radiograph
