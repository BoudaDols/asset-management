"""Tests for app.core.exceptions module."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import (
    AppException,
    ConflictException,
    NotFoundException,
    PayloadTooLargeException,
    ServiceUnavailableException,
    ValidationException,
    register_exception_handlers,
)
from app.core.schemas import ValidationErrorDetail


class TestExceptionClasses:
    """Test custom exception class instantiation and attributes."""

    def test_app_exception_defaults(self):
        exc = AppException(error_code="TEST", message="Test error")
        assert exc.error_code == "TEST"
        assert exc.message == "Test error"
        assert exc.status_code == 400
        assert exc.details is None

    def test_app_exception_with_details(self):
        details = [ValidationErrorDetail(field="x", value="y", message="bad")]
        exc = AppException(
            error_code="ERR", message="msg", status_code=422, details=details
        )
        assert exc.status_code == 422
        assert len(exc.details) == 1

    def test_not_found_exception(self):
        exc = NotFoundException()
        assert exc.status_code == 404
        assert exc.error_code == "NOT_FOUND"
        assert "not found" in exc.message.lower()

    def test_not_found_exception_custom_message(self):
        exc = NotFoundException(message="Asset not found", error_code="ASSET_NOT_FOUND")
        assert exc.message == "Asset not found"
        assert exc.error_code == "ASSET_NOT_FOUND"

    def test_conflict_exception(self):
        exc = ConflictException()
        assert exc.status_code == 409
        assert exc.error_code == "CONFLICT"

    def test_conflict_exception_with_details(self):
        details = [
            ValidationErrorDetail(
                field="instance_code", value="DUP-001", message="Already exists"
            )
        ]
        exc = ConflictException(message="Duplicate code", details=details)
        assert exc.status_code == 409
        assert exc.details is not None
        assert len(exc.details) == 1

    def test_validation_exception(self):
        exc = ValidationException()
        assert exc.status_code == 400
        assert exc.error_code == "VALIDATION_ERROR"

    def test_validation_exception_with_details(self):
        details = [
            ValidationErrorDetail(field="code", value="bad!", message="Invalid format"),
            ValidationErrorDetail(field="name", value="", message="Cannot be empty"),
        ]
        exc = ValidationException(message="Input invalid", details=details)
        assert exc.status_code == 400
        assert len(exc.details) == 2

    def test_service_unavailable_exception(self):
        exc = ServiceUnavailableException()
        assert exc.status_code == 503
        assert exc.error_code == "SERVICE_UNAVAILABLE"

    def test_payload_too_large_exception(self):
        exc = PayloadTooLargeException()
        assert exc.status_code == 413
        assert exc.error_code == "PAYLOAD_TOO_LARGE"

    def test_payload_too_large_with_max_size(self):
        exc = PayloadTooLargeException(max_size_bytes=52428800)
        assert "52428800" in exc.message


class TestExceptionHandlers:
    """Test that exception handlers return proper JSON responses."""

    @pytest.fixture()
    def test_app(self) -> FastAPI:
        """Create a test FastAPI app with exception handlers registered."""
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/not-found")
        async def raise_not_found():
            raise NotFoundException(message="Item not found")

        @app.get("/conflict")
        async def raise_conflict():
            raise ConflictException(
                message="Duplicate entry",
                details=[
                    ValidationErrorDetail(
                        field="instance_code", value="X-001", message="Already exists"
                    )
                ],
            )

        @app.get("/validation")
        async def raise_validation():
            raise ValidationException(
                message="Invalid input",
                details=[
                    ValidationErrorDetail(field="code", value="bad!", message="Invalid format"),
                    ValidationErrorDetail(field="name", value="", message="Required"),
                ],
            )

        @app.get("/unavailable")
        async def raise_unavailable():
            raise ServiceUnavailableException(message="Database connection failed")

        @app.get("/too-large")
        async def raise_too_large():
            raise PayloadTooLargeException(max_size_bytes=52428800)

        return app

    @pytest.fixture()
    def client(self, test_app: FastAPI) -> TestClient:
        return TestClient(test_app)

    def test_not_found_handler(self, client: TestClient):
        resp = client.get("/not-found")
        assert resp.status_code == 404
        body = resp.json()
        assert body["error_code"] == "NOT_FOUND"
        assert body["message"] == "Item not found"
        assert "details" not in body

    def test_conflict_handler(self, client: TestClient):
        resp = client.get("/conflict")
        assert resp.status_code == 409
        body = resp.json()
        assert body["error_code"] == "CONFLICT"
        assert body["message"] == "Duplicate entry"
        assert len(body["details"]) == 1
        assert body["details"][0]["field"] == "instance_code"
        assert body["details"][0]["value"] == "X-001"

    def test_validation_handler(self, client: TestClient):
        resp = client.get("/validation")
        assert resp.status_code == 400
        body = resp.json()
        assert body["error_code"] == "VALIDATION_ERROR"
        assert body["message"] == "Invalid input"
        assert len(body["details"]) == 2

    def test_service_unavailable_handler(self, client: TestClient):
        resp = client.get("/unavailable")
        assert resp.status_code == 503
        body = resp.json()
        assert body["error_code"] == "SERVICE_UNAVAILABLE"
        assert "Database connection failed" in body["message"]

    def test_payload_too_large_handler(self, client: TestClient):
        resp = client.get("/too-large")
        assert resp.status_code == 413
        body = resp.json()
        assert body["error_code"] == "PAYLOAD_TOO_LARGE"
        assert "52428800" in body["message"]

    def test_pydantic_validation_error_handler(self, test_app: FastAPI):
        """Test that Pydantic request validation errors are handled."""
        from pydantic import BaseModel

        class ItemCreate(BaseModel):
            name: str
            count: int

        @test_app.post("/items")
        async def create_item(item: ItemCreate):
            return {"ok": True}

        client = TestClient(test_app)
        resp = client.post("/items", json={"name": 123, "count": "not_a_number"})
        assert resp.status_code == 400
        body = resp.json()
        assert body["error_code"] == "VALIDATION_ERROR"
        assert body["message"] == "Request validation failed"
        assert "details" in body
        assert len(body["details"]) >= 1
