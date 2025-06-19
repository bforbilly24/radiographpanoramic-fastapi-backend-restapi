from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from src.utils.dependencies import get_db
from src.controllers.auth_controller import login, logout
from src.handlers.response_handler import ResponseSchema
from fastapi.security import OAuth2PasswordBearer
from src.utils.dependencies import get_current_user
from src.models.user_model import User

router = APIRouter(tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login", response_model=ResponseSchema)
async def login_endpoint(login_data: LoginRequest, db: Session = Depends(get_db)):
    return login(login_data, db)

@router.post("/logout", response_model=ResponseSchema)
async def logout_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    return logout(current_user, db, token)