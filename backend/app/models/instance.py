"""Asset instance model: physical assets belonging to a municipality."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.catalog import ActifPrimaire, ActifSecondaire, ActifTertiaire
    from app.models.tenant import TenantUnite, TenantVille


class ActifInstance(Base):
    """A concrete physical asset instance belonging to a municipality."""

    __tablename__ = "actif_instance"

    instance_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_code: Mapped[str] = mapped_column(String(50), nullable=False)
    instance_nom: Mapped[str] = mapped_column(String(255), nullable=False)

    # Exactly ONE of these must be set (XOR constraint)
    prim_code: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("actif_primaire.prim_code"), nullable=True
    )
    seco_code: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("actif_secondaire.seco_code"), nullable=True
    )
    tert_code: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("actif_tertiaire.tert_code"), nullable=True
    )

    # Tenant (municipality)
    tenant_ville_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tenant_ville.tenant_ville_id"), nullable=False
    )
    tenant_unite_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tenant_unite.tenant_unite_id"), nullable=True
    )

    # Physical attributes
    installation_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    attributes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Metadata
    status_code: Mapped[str] = mapped_column(String(50), server_default="ACTIF")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    end_date: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    primaire: Mapped[ActifPrimaire | None] = relationship(back_populates="instances")
    secondaire: Mapped[ActifSecondaire | None] = relationship(back_populates="instances")
    tertiaire: Mapped[ActifTertiaire | None] = relationship(back_populates="instances")
    ville: Mapped[TenantVille] = relationship(back_populates="instances")
    unite: Mapped[TenantUnite | None] = relationship(back_populates="instances")

    __table_args__ = (
        UniqueConstraint("instance_code", "tenant_ville_id", name="uq_instance_code_tenant"),
        CheckConstraint(
            "(CASE WHEN prim_code IS NOT NULL THEN 1 ELSE 0 END"
            " + CASE WHEN seco_code IS NOT NULL THEN 1 ELSE 0 END"
            " + CASE WHEN tert_code IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="ck_exactly_one_catalog_ref",
        ),
    )
