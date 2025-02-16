from fastapi import APIRouter, Depends, HTTPException, status, Response, Security
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from src.utils.dependencies import get_db
from src.models.user_model import User
from src.models.token_blacklist_model import TokenBlacklist
from src.core.security import verify_password, create_access_token, decode_token
from src.core.config import settings
from src.handlers.response_handler import ResponseSchema
from src.utils.dependencies import get_db, get_current_user
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

class LoginRequest(BaseModel):
    username: str
    password: str

router = APIRouter()

@router.post("/login", response_model=ResponseSchema)
async def login(
    response: Response, login_data: LoginRequest, db: Session = Depends(get_db)
):
    try:
        user = db.query(User).filter(User.email == login_data.username).first()
        if not user or not verify_password(login_data.password, user.password):
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return ResponseSchema(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid email or password",
                data=None,
                error="Incorrect email or password",
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )

        return ResponseSchema(
            status_code=status.HTTP_200_OK,
            message="Login successful",
            data={"access_token": access_token, "token_type": "bearer"},
            error=None,
        )

    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseSchema(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred",
            data=None,
            error=str(e),
        )

@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # Decode token to get expiration
        token_data = decode_token(token)
        expires_at = datetime.fromtimestamp(token_data["exp"])
        
        # Add token to blacklist
        blacklisted_token = TokenBlacklist(
            token=token,
            expires_at=expires_at
        )
        db.add(blacklisted_token)
        db.commit()

        return ResponseSchema(
            status_code=status.HTTP_200_OK,
            message="Logout successful",
            data=None,
            error=None,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )