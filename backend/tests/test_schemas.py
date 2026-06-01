"""Tests for app.core.schemas module."""

from app.core.schemas import ErrorResponse, PaginatedResult, ValidationErrorDetail


class TestValidationErrorDetail:
    """Test the ValidationErrorDetail schema."""

    def test_create_with_all_fields(self):
        detail = ValidationErrorDetail(field="instance_code", value="bad!", message="Invalid format")
        assert detail.field == "instance_code"
        assert detail.value == "bad!"
        assert detail.message == "Invalid format"

    def test_create_with_none_value(self):
        detail = ValidationErrorDetail(field="prim_code", value=None, message="Required field")
        assert detail.field == "prim_code"
        assert detail.value is None
        assert detail.message == "Required field"

    def test_serialization(self):
        detail = ValidationErrorDetail(field="name", value=123, message="Must be string")
        data = detail.model_dump()
        assert data == {"field": "name", "value": 123, "message": "Must be string"}


class TestErrorResponse:
    """Test the ErrorResponse schema."""

    def test_create_without_details(self):
        resp = ErrorResponse(error_code="NOT_FOUND", message="Resource not found")
        assert resp.error_code == "NOT_FOUND"
        assert resp.message == "Resource not found"
        assert resp.details is None

    def test_create_with_details(self):
        details = [
            ValidationErrorDetail(field="code", value="bad", message="Invalid format"),
            ValidationErrorDetail(field="name", value="", message="Cannot be empty"),
        ]
        resp = ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Validation failed",
            details=details,
        )
        assert resp.error_code == "VALIDATION_ERROR"
        assert len(resp.details) == 2
        assert resp.details[0].field == "code"
        assert resp.details[1].field == "name"

    def test_serialization_excludes_none_details(self):
        resp = ErrorResponse(error_code="CONFLICT", message="Duplicate entry")
        data = resp.model_dump(exclude_none=True)
        assert "details" not in data
        assert data["error_code"] == "CONFLICT"
        assert data["message"] == "Duplicate entry"

    def test_serialization_includes_details_when_present(self):
        details = [ValidationErrorDetail(field="x", value=None, message="err")]
        resp = ErrorResponse(error_code="VALIDATION_ERROR", message="Failed", details=details)
        data = resp.model_dump(exclude_none=True)
        assert "details" in data
        assert len(data["details"]) == 1


class TestPaginatedResult:
    """Test the PaginatedResult generic schema."""

    def test_create_factory_method(self):
        result = PaginatedResult.create(
            data=["a", "b", "c"],
            total=10,
            page=1,
            page_size=3,
        )
        assert result.data == ["a", "b", "c"]
        assert result.total == 10
        assert result.page == 1
        assert result.page_size == 3
        assert result.total_pages == 4  # ceil(10/3) = 4

    def test_total_pages_exact_division(self):
        result = PaginatedResult.create(data=[], total=20, page=1, page_size=5)
        assert result.total_pages == 4

    def test_total_pages_with_remainder(self):
        result = PaginatedResult.create(data=[], total=21, page=1, page_size=5)
        assert result.total_pages == 5

    def test_total_pages_zero_total(self):
        result = PaginatedResult.create(data=[], total=0, page=1, page_size=25)
        assert result.total_pages == 0

    def test_total_pages_single_item(self):
        result = PaginatedResult.create(data=["x"], total=1, page=1, page_size=25)
        assert result.total_pages == 1

    def test_empty_data_list(self):
        result = PaginatedResult.create(data=[], total=0, page=1, page_size=25)
        assert result.data == []
        assert result.total == 0

    def test_serialization(self):
        result = PaginatedResult.create(
            data=[{"id": 1}, {"id": 2}],
            total=50,
            page=2,
            page_size=2,
        )
        data = result.model_dump()
        assert data["data"] == [{"id": 1}, {"id": 2}]
        assert data["total"] == 50
        assert data["page"] == 2
        assert data["page_size"] == 2
        assert data["total_pages"] == 25
