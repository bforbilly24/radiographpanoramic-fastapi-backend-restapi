from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from src.routes.v1.api import api_router
from src.core.config import settings
from src.db.session import engine, Base

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

app = FastAPI(title=settings.PROJECT_NAME)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom StaticFiles class to add CORS headers
class CORSStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: dict) -> FileResponse:
        response = await super().get_response(path, scope)
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:5173"
        return response

# Mount static files with CORS support
app.mount(
    "/uploads",
    CORSStaticFiles(directory="uploads", html=False),
    name="uploads"
)

app.include_router(api_router, prefix="/api/v1")

@app.on_event("startup")
def startup_event():
    print("Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}