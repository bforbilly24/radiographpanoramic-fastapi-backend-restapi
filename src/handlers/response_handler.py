# src/handlers/response_handler.py
from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")


class ResponseSchema(BaseModel, Generic[T]):
    status_code: int
    message: str
    data: Optional[T] = None
    error: Optional[str] = None

    @staticmethod
    def success(data: Any = None, message: str = "Operation successful") -> "ResponseSchema":
        return ResponseSchema(status_code=200, message=message, data=data, error=None)

    @staticmethod
    def error(
        status_code: int = 400, message: str = "Operation failed", error: str = None
    ) -> "ResponseSchema":
        return ResponseSchema(
            status_code=status_code,
            message=message,
            data=None,
            error=error
        )
