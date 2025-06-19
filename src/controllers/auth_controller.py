from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.models.user_model import User
from src.core.security import verify_password, create_access_token, decode_token
from src.core.config import settings
from src.handlers.response_handler import ResponseSchema
from src.models.token_blacklist_model import TokenBlacklist
from datetime import datetime, timedelta

def login(login_data: dict, db: Session) -> ResponseSchema:
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=access_token_expires
    )

    return ResponseSchema(
        status_code=status.HTTP_200_OK,
        message="Login successful",
        data={"access_token": access_token, "token_type": "bearer"},
        error=None,
    )

def logout(current_user: User, db: Session, token: str) -> ResponseSchema:
    if db.query(TokenBlacklist).filter(TokenBlacklist.token == token).first():
        return ResponseSchema(
            status_code=status.HTTP_200_OK,
            message="Already logged out",
            data=None,
            error=None,
        )

    token_data = decode_token(token)
    expires_at = datetime.fromtimestamp(token_data["exp"])

    blacklisted_token = TokenBlacklist(token=token, expires_at=expires_at)
    db.add(blacklisted_token)
    db.commit()

    return ResponseSchema(
        status_code=status.HTTP_200_OK,
        message="Logout successful",
        data=None,
        error=None,
    )