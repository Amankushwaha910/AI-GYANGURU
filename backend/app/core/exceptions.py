"""
Custom application exceptions with structured HTTP responses.
"""
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception."""
    def __init__(self, message: str, status_code: int = 500, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.code = code
        super().__init__(message)


class NotFoundError(AppException):
    def __init__(self, resource: str, identifier: str = ""):
        super().__init__(
            message=f"{resource} not found" + (f": {identifier}" if identifier else ""),
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
        )


class ValidationError(AppException):
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
        )


class AuthError(AppException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="AUTH_ERROR",
        )


class PermissionError(AppException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            code="PERMISSION_DENIED",
        )


class AIProviderError(AppException):
    def __init__(self, message: str = "AI provider error"):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code="AI_PROVIDER_ERROR",
        )


class FileProcessingError(AppException):
    def __init__(self, message: str = "File processing failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="FILE_PROCESSING_ERROR",
        )


# ── Exception Handlers ────────────────────────────────────────────────────────

async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
            },
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
            },
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again.",
            },
        },
    )
