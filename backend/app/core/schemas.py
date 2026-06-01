"""Shared Pydantic schemas used across all modules.

Provides generic response schemas for pagination, error responses,
and validation error details.
"""

import math
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ValidationErrorDetail(BaseModel):
    """Detail about a single field validation error.

    Used within ErrorResponse.details to provide field-level error information.
    """

    field: str = Field(..., description="The field name that failed validation")
    value: Any | None = Field(None, description="The rejected value (if available)")
    message: str = Field(..., description="Description of the validation rule that failed")


class ErrorResponse(BaseModel):
    """Standard error response returned by all API error handlers.

    Conforms to Requirement 10.8: error_code, message, and optional details array.
    """

    error_code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error description")
    details: list[ValidationErrorDetail] | None = Field(
        None, description="Field-level validation errors (for 400 responses)"
    )


class PaginatedResult(BaseModel, Generic[T]):
    """Generic paginated response wrapper.

    Used by all list endpoints to return paginated data with metadata.
    """

    data: list[T] = Field(default_factory=list, description="Page of result items")
    total: int = Field(..., ge=0, description="Total number of items matching the query")
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(..., ge=1, description="Number of items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

    @classmethod
    def create(
        cls, *, data: list[T], total: int, page: int, page_size: int
    ) -> "PaginatedResult[T]":
        """Factory method to create a PaginatedResult with computed total_pages."""
        total_pages = math.ceil(total / page_size) if page_size > 0 else 0
        return cls(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
