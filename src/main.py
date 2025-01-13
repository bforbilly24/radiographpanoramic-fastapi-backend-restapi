from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from src.app.v1.api import api_router
from src.core.config import settings
from src.db.session import engine, Base

# Define OAuth2PasswordBearer for Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Create FastAPI app instance
app = FastAPI(title=settings.PROJECT_NAME)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Create database tables at startup
@app.on_event("startup")
def startup_event():
    print("Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=engine)

# Root endpoint
@app.get("/")
def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}
