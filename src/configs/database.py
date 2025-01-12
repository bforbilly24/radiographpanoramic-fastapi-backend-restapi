# src/configs/database.py
import os
from dotenv import load_dotenv

load_dotenv() 

class Config:
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '7bt7p4dzqBeX1E3LMl2/KPtT4FhD+7kEQlrBnfaSocI=')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:postgre@localhost/radiograph')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
