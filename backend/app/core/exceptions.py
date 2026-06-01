"""Custom exceptions and FastAPI exception handlers.

Provides application-specific exception classes and handlers that return
consistent JSON error responses using the ErrorResponse schema.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.schemas import ErrorResponse, ValidationErrorDetail


# --- Custom Exception Classes ---


class AppException(Exception):
    """Base application exception.

    All custom exceptions inherit from this class to enable
    centralized exception handling.
    """

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 400,
        details: list[ValidationErrorDetail] | None = None,
    ) -> None:
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class NotFoundException(AppException):
    """Raised when a requested resource is not found (404)."""

    def __init__(
        self,
        message: str = "Resource not found",
        error_code: str = "NOT_FOUND",
    ) -> None:
        super().__init__(error_code=error_code, message=message, status_code=404)


class ConflictException(AppException):
    """Raised when a request conflicts with existing state (409).

    Example: duplicate instance_code within the same tenant.
    """

    def __init__(
        self,
        message: str = "Resource conflict",
        error_code: str = "CONFLICT",
        details: list[ValidationErrorDetail] | None = None,
    ) -> None:
        super().__init__(
            error_code=error_code, message=message, status_code=409, details=details
        )


class ValidationException(AppException):
    """Raised when request data fails business validation (400).

    Carries field-level error details per Requirement 8.1.
    """

    def __init__(
        self,
        message: str = "Validation failed",
        error_code: str = "VALIDATION_ERROR",
        details: list[ValidationErrorDetail] | None = None,
    ) -> None:
        super().__init__(
            error_code=error_code, message=message, status_code=400, details=details
        )


class ServiceUnavailableException(AppException):
    """Raised when a required service (e.g., database) is unavailable (503)."""

    def __init__(
        self,
        message: str = "Service unavailable",
        error_code: str = "SERVICE_UNAVAILABLE",
    ) -> None:
        super().__init__(error_code=error_code, message=message, status_code=503)


class PayloadTooLargeException(AppException):
    """Raised when a file upload exceeds the maximum allowed size (413)."""

    def __init__(
        self,
        message: str = "File size exceeds maximum allowed size",
        error_code: str = "PAYLOAD_TOO_LARGE",
        max_size_bytes: int | None = None,
    ) -> None:
        if max_size_bytes is not None:
            message = f"{message}. Maximum allowed: {max_size_bytes} bytes"
        super().__init__(error_code=error_code, message=message, status_code=413)


# --- FastAPI Exception Handlers ---


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle all AppException subclasses and return a structured JSON error."""
    error_response = ErrorResponse(
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(exclude_none=True),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic/FastAPI request validation errors.

    Transforms FastAPI's default validation errors into our ErrorResponse format
    with field-level details per Requirement 8.1 and 10.8.
    """
    details: list[ValidationErrorDetail] = []
    for error in exc.errors():
        # Build field path from loc (e.g., ("body", "instance_code") -> "instance_code")
        loc = error.get("loc", ())
        field_parts = [str(part) for part in loc if part != "body"]
        field = ".".join(field_parts) if field_parts else "unknown"

        details.append(
            ValidationErrorDetail(
                field=field,
                value=error.get("input"),
                message=error.get("msg", "Invalid value"),
            )
        )

    error_response = ErrorResponse(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        details=details,
    )
    return JSONResponse(
        status_code=400,
        content=error_response.model_dump(exclude_none=True),
    )


# --- Handler Registration ---


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers with the FastAPI application.

    Call this from main.py to wire up error handling.
    """
    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
