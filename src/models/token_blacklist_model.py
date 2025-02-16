from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from src.db.base import Base


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String, nullable=False, unique=True)
    blacklisted_at = Column(DateTime, default=datetime.utcnow)
