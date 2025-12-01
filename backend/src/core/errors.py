"""
Custom exception classes and error handlers following RFC 7807 Problem Details
"""
from typing import Any, Dict, Optional

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ProblemDetail(BaseModel):
    """RFC 7807 Problem Details model"""
    type: str
    title: str
    status: int
    detail: str
    errors: Optional[Dict[str, Any]] = None


class CustomException(Exception):
    """Base exception class for custom application errors"""
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_type: str = "/errors/internal-error",
        title: str = "Internal Error",
        errors: Optional[Dict[str, Any]] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_type = error_type
        self.title = title
        self.errors = errors
        super().__init__(detail)


class ValidationException(CustomException):
    """Exception for validation errors"""
    def __init__(self, detail: str, errors: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_type="/errors/validation-error",
            title="Validation Error",
            errors=errors
        )


class NotFoundException(CustomException):
    """Exception for resource not found"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_type="/errors/not-found",
            title="Not Found"
        )


class UnauthorizedException(CustomException):
    """Exception for unauthorized access"""
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_type="/errors/unauthorized",
            title="Unauthorized"
        )


class ForbiddenException(CustomException):
    """Exception for forbidden access"""
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_type="/errors/forbidden",
            title="Forbidden"
        )


class DocumentAIException(CustomException):
    """Exception for Document AI API errors"""
    def __init__(self, detail: str, original_error: Optional[Exception] = None):
        self.original_error = original_error
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_type="/errors/document-ai-error",
            title="Document AI Error"
        )


class OpenRouterException(CustomException):
    """Exception for OpenRouter API errors"""
    def __init__(
        self,
        detail: str,
        api_status_code: Optional[int] = None,
        original_error: Optional[Exception] = None,
        retry_count: int = 0
    ):
        self.api_status_code = api_status_code
        self.original_error = original_error
        self.retry_count = retry_count
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_type="/errors/openrouter-error",
            title="OpenRouter API Error"
        )


class VisionOCRException(CustomException):
    """Exception for Vision OCR API errors (Gemini via OpenRouter)"""
    def __init__(self, detail: str, original_error: Optional[Exception] = None):
        self.original_error = original_error
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_type="/errors/vision-ocr-error",
            title="Vision OCR Error"
        )


async def custom_exception_handler(request: Request, exc: CustomException) -> JSONResponse:
    """Handler for custom application exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": exc.error_type,
            "title": exc.title,
            "status": exc.status_code,
            "detail": exc.detail,
            "errors": exc.errors
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler for FastAPI validation errors"""
    errors = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        if field not in errors:
            errors[field] = []
        errors[field].append(error["msg"])

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "type": "/errors/validation-error",
            "title": "Validation Error",
            "status": 422,
            "detail": "Request validation failed",
            "errors": errors
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for unhandled exceptions"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "/errors/internal-error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred",
        }
    )
