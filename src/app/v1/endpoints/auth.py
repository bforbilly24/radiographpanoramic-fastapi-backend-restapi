from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import timedelta
from src.utils.dependencies import get_db
from src.models.user_model import User
from src.core.security import verify_password, create_access_token
from src.core.config import settings
from src.handlers.response_handler import ResponseSchema
from src.utils.dependencies import get_db, get_current_user


class LoginRequest(BaseModel):
    username: str
    password: str


router = APIRouter()


@router.post("/login", response_model=ResponseSchema)
async def login(
    response: Response, login_data: LoginRequest, db: Session = Depends(get_db)
):
    try:
        # Cari user berdasarkan email
        user = db.query(User).filter(User.email == login_data.username).first()
        if not user or not verify_password(login_data.password, user.password):
            # Kesalahan autentikasi: Email atau password salah
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return ResponseSchema(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Invalid email or password",
                data=None,
                error="Incorrect email or password",
            )

        # Generate access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )

        # Return structured response for successful login
        return ResponseSchema(
            status_code=status.HTTP_200_OK,
            message="Login successful",
            data={"access_token": access_token, "token_type": "bearer"},
            error=None,
        )

    except Exception as e:
        # Tangani semua kesalahan lainnya sebagai 500
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ResponseSchema(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred",
            data=None,
            error=str(e),
        )


@router.post("/logout")
async def logout(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Handle user logout. Invalidate token if necessary.
    """
    # If you're using token blacklisting or a revocation list, handle that here
    # For example, store the token in a blacklist table (not implemented here)

    return {
        "status_code": status.HTTP_200_OK,
        "message": "Logout successful",
        "data": None,
        "error": None,
    }
