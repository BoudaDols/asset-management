"""Tenant models: municipality and organizational unit isolation."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.import_record import ImportRecord
    from app.models.instance import ActifInstance


class TenantVille(Base):
    """Municipality tenant (e.g., Ville de Montréal)."""

    __tablename__ = "tenant_ville"

    tenant_ville_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    tenant_nom: Mapped[str] = mapped_column(String(255), nullable=False)
    database_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Tenant Aurora DB URL. NULL = not yet provisioned."
    )
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    end_date: Mapped[datetime | None] = mapped_column(nullable=True)

    unites: Mapped[list[TenantUnite]] = relationship(back_populates="ville")
    instances: Mapped[list[ActifInstance]] = relationship(back_populates="ville")
    imports: Mapped[list[ImportRecord]] = relationship(back_populates="ville")


class TenantUnite(Base):
    """Organizational unit within a municipality (e.g., Arrondissement)."""

    __tablename__ = "tenant_unite"

    tenant_unite_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_ville_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tenant_ville.tenant_ville_id"), nullable=False
    )
    unite_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    unite_nom: Mapped[str] = mapped_column(String(255), nullable=False)
    unite_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    categorie_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    end_date: Mapped[datetime | None] = mapped_column(nullable=True)

    ville: Mapped[TenantVille] = relationship(back_populates="unites")
    instances: Mapped[list[ActifInstance]] = relationship(back_populates="unite")
