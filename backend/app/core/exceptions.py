"""
Unified error response schema and custom exceptions.
All API errors return: {"error": "<CODE>", "message": "<user-friendly text>"}
"""
from typing import Any

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response returned by all exception handlers."""
    error: str
    message: str
    detail: Any = None


class AppException(Exception):
    """Custom application exception with structured error info."""

    def __init__(
        self,
        status_code: int,
        error: str,
        message: str,
        detail: Any = None,
    ):
        self.status_code = status_code
        self.error = error
        self.message = message
        self.detail = detail
        super().__init__(message)
