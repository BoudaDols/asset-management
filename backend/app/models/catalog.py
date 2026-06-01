"""Catalog hierarchy models: the 8-level asset taxonomy.

Hierarchy: Famille → Service → Fonction → Sous-fonction → Type d'actif
           → Actif primaire → Actif secondaire → Actif tertiaire
Plus: Discipline (classifies secondaire assets)
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.instance import ActifInstance


class ActifFamille(Base):
    """Top-level asset family (e.g., Infrastructure)."""

    __tablename__ = "actif_famille"

    fami_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    fami_nom: Mapped[str] = mapped_column(String(255), nullable=False)
    fami_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    end_date: Mapped[datetime | None] = mapped_column(nullable=True)

    services: Mapped[list[ActifService]] = relationship(back_populates="famille")


class ActifService(Base):
    """Service level (e.g., Eau potable)."""

    __tablename__ = "actif_service"

    serv_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    serv_nom: Mapped[str] = mapped_column(String(255), nullable=False)
    fami_code: Mapped[str] = mapped_column(
        String(50), ForeignKey("actif_famille.fami_code"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    end_date: Mapped[datetime | None] = mapped_column(nullable=True)

    famille: Mapped[ActifFamille] = relationship(back_populates="services")
    fonctions: Mapped[list[ActifFonction]] = relationship(back_populates="service")


class ActifFonction(Base):
    """Fonction level (e.g., Distribution)."""

    __tablename__ = "actif_fonction"

    fonc_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    fonc_nom: Mapped[str] = mapped_column(String(255), nullable=False)
    serv_code: Mapped[str] = mapped_column(
        String(50), ForeignKey("actif_service.serv_code"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    end_date: Mapped[datetime | None] = mapped_column(nullable=True)

    service: Mapped[ActifService] = relationship(back_populates="fonctions")
    sous_fonctions: Mapped[list[SousFonction]] = relationship(back_populates="fonction")


class SousFonction(Base):
    """Sous-fonction level (e.g., Réseau de distribution)."""

    __tablename__ = "sous_fonction"

    sous_fonc_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    sous_fonc_nom: Mapped[str] = mapped_column(String(255), nullable=False)
    fonc_code: Mapped[str] = mapped_column(
        String(50), ForeignKey("actif_fonction.fonc_code"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    end_date: Mapped[datetime | None] = mapped_column(nullable=True)

    fonction: Mapped[ActifFonction] = relationship(back_populates="sous_fonctions")
    types_actif: Mapped[list[TypeActif]] = relationship(back_populates="sous_fonction")


class TypeActif(Base):
    """Type d'actif level (e.g., Conduite)."""

    __tablename__ = "type_actif"

    type_actif_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    type_actif_nom: Mapped[str] = mapped_column(String(255), nullable=False)
    sous_fonc_code: Mapped[str] = mapped_column(
        String(50), ForeignKey("sous_fonction.sous_fonc_code"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    end_date: Mapped[datetime | None] = mapped_column(nullable=True)

    sous_fonction: Mapped[SousFonction] = relationship(back_populates="types_actif")
    primaires: Mapped[list[ActifPrimaire]] = relationship(back_populates="type_actif")


class ActifDiscipline(Base):
    """Discipline classification for secondary assets (e.g., Mécanique)."""

    __tablename__ = "actif_discipline"

    disc_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    disc_nom: Mapped[str] = mapped_column(String(255), nullable=False)

    secondaires: Mapped[list[ActifSecondaire]] = relationship(back_populates="discipline")


class ActifPrimaire(Base):
    """Primary asset (e.g., Station de pompage SP-001)."""

    __tablename__ = "actif_primaire"

    prim_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    prim_nom: Mapped[str] = mapped_column(String(255), nullable=False)
    type_actif_code: Mapped[str] = mapped_column(
        String(50), ForeignKey("type_actif.type_actif_code"), nullable=False
    )
    fonc_code: Mapped[str] = mapped_column(String(50), nullable=False)
    serv_code: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    end_date: Mapped[datetime | None] = mapped_column(nullable=True)

    type_actif: Mapped[TypeActif] = relationship(back_populates="primaires")
    secondaires: Mapped[list[ActifSecondaire]] = relationship(back_populates="primaire")
    instances: Mapped[list[ActifInstance]] = relationship(back_populates="primaire")


class ActifSecondaire(Base):
    """Secondary asset (e.g., Pompe P-001)."""

    __tablename__ = "actif_secondaire"

    seco_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    seco_nom: Mapped[str] = mapped_column(String(255), nullable=False)
    prim_code: Mapped[str] = mapped_column(
        String(50), ForeignKey("actif_primaire.prim_code"), nullable=False
    )
    disc_code: Mapped[str] = mapped_column(
        String(50), ForeignKey("actif_discipline.disc_code"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    end_date: Mapped[datetime | None] = mapped_column(nullable=True)

    primaire: Mapped[ActifPrimaire] = relationship(back_populates="secondaires")
    discipline: Mapped[ActifDiscipline] = relationship(back_populates="secondaires")
    tertiaires: Mapped[list[ActifTertiaire]] = relationship(back_populates="secondaire")
    instances: Mapped[list[ActifInstance]] = relationship(back_populates="secondaire")


class ActifTertiaire(Base):
    """Tertiary asset (e.g., Roulement R-001)."""

    __tablename__ = "actif_tertiaire"

    tert_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    tert_nom: Mapped[str] = mapped_column(String(255), nullable=False)
    seco_code: Mapped[str] = mapped_column(
        String(50), ForeignKey("actif_secondaire.seco_code"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    end_date: Mapped[datetime | None] = mapped_column(nullable=True)

    secondaire: Mapped[ActifSecondaire] = relationship(back_populates="tertiaires")
    instances: Mapped[list[ActifInstance]] = relationship(back_populates="tertiaire")
