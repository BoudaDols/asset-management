"""Import record model: audit trail for Excel imports."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.tenant import TenantVille


class ImportRecord(Base):
    """Audit record for each Excel import operation."""

    __tablename__ = "import_record"

    import_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_ville_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tenant_ville.tenant_ville_id"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    created_count: Mapped[int] = mapped_column(Integer, nullable=False)
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False)
    errors_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    imported_by: Mapped[str] = mapped_column(String(100), nullable=False)
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    ville: Mapped[TenantVille] = relationship(back_populates="imports")
