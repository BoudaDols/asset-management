"""SQLAlchemy models for the Municipal Asset Management System.

All models are imported here so that Base.metadata is fully populated
when Alembic or other tools import this package.
"""

from app.models.catalog import (  # noqa: F401
    ActifDiscipline,
    ActifFamille,
    ActifFonction,
    ActifPrimaire,
    ActifSecondaire,
    ActifService,
    ActifTertiaire,
    SousFonction,
    TypeActif,
)
from app.models.import_record import ImportRecord  # noqa: F401
from app.models.instance import ActifInstance  # noqa: F401
from app.models.tenant import TenantUnite, TenantVille  # noqa: F401
