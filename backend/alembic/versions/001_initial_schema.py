"""Initial schema - all tables for municipal asset management.

Revision ID: 001
Revises: None
Create Date: 2025-01-01 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Enable pg_trgm extension for trigram full-text search
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # --- Catalog Hierarchy Tables ---

    op.create_table(
        "actif_famille",
        sa.Column("fami_code", sa.String(50), primary_key=True),
        sa.Column("fami_nom", sa.String(255), nullable=False),
        sa.Column("fami_description", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("end_date", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    op.create_table(
        "actif_service",
        sa.Column("serv_code", sa.String(50), primary_key=True),
        sa.Column("serv_nom", sa.String(255), nullable=False),
        sa.Column(
            "fami_code",
            sa.String(50),
            sa.ForeignKey("actif_famille.fami_code"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("end_date", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    op.create_table(
        "actif_fonction",
        sa.Column("fonc_code", sa.String(50), primary_key=True),
        sa.Column("fonc_nom", sa.String(255), nullable=False),
        sa.Column(
            "serv_code",
            sa.String(50),
            sa.ForeignKey("actif_service.serv_code"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("end_date", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    op.create_table(
        "sous_fonction",
        sa.Column("sous_fonc_code", sa.String(50), primary_key=True),
        sa.Column("sous_fonc_nom", sa.String(255), nullable=False),
        sa.Column(
            "fonc_code",
            sa.String(50),
            sa.ForeignKey("actif_fonction.fonc_code"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("end_date", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    op.create_table(
        "type_actif",
        sa.Column("type_actif_code", sa.String(50), primary_key=True),
        sa.Column("type_actif_nom", sa.String(255), nullable=False),
        sa.Column(
            "sous_fonc_code",
            sa.String(50),
            sa.ForeignKey("sous_fonction.sous_fonc_code"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("end_date", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    op.create_table(
        "actif_discipline",
        sa.Column("disc_code", sa.String(50), primary_key=True),
        sa.Column("disc_nom", sa.String(255), nullable=False),
    )

    op.create_table(
        "actif_primaire",
        sa.Column("prim_code", sa.String(50), primary_key=True),
        sa.Column("prim_nom", sa.String(255), nullable=False),
        sa.Column(
            "type_actif_code",
            sa.String(50),
            sa.ForeignKey("type_actif.type_actif_code"),
            nullable=False,
        ),
        sa.Column("fonc_code", sa.String(50), nullable=False),
        sa.Column("serv_code", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("end_date", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    op.create_table(
        "actif_secondaire",
        sa.Column("seco_code", sa.String(50), primary_key=True),
        sa.Column("seco_nom", sa.String(255), nullable=False),
        sa.Column(
            "prim_code",
            sa.String(50),
            sa.ForeignKey("actif_primaire.prim_code"),
            nullable=False,
        ),
        sa.Column(
            "disc_code",
            sa.String(50),
            sa.ForeignKey("actif_discipline.disc_code"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("end_date", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    op.create_table(
        "actif_tertiaire",
        sa.Column("tert_code", sa.String(50), primary_key=True),
        sa.Column("tert_nom", sa.String(255), nullable=False),
        sa.Column(
            "seco_code",
            sa.String(50),
            sa.ForeignKey("actif_secondaire.seco_code"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("end_date", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    # --- Tenant Tables ---

    op.create_table(
        "tenant_ville",
        sa.Column("tenant_ville_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_code", sa.String(50), unique=True, nullable=False),
        sa.Column("tenant_nom", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("end_date", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    op.create_table(
        "tenant_unite",
        sa.Column("tenant_unite_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "tenant_ville_id",
            sa.Integer(),
            sa.ForeignKey("tenant_ville.tenant_ville_id"),
            nullable=False,
        ),
        sa.Column("unite_code", sa.String(50), unique=True, nullable=False),
        sa.Column("unite_nom", sa.String(255), nullable=False),
        sa.Column("unite_location", sa.String(255), nullable=True),
        sa.Column("categorie_code", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("end_date", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    # --- Instance Table ---

    op.create_table(
        "actif_instance",
        sa.Column("instance_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("instance_code", sa.String(50), nullable=False),
        sa.Column("instance_nom", sa.String(255), nullable=False),
        sa.Column(
            "prim_code",
            sa.String(50),
            sa.ForeignKey("actif_primaire.prim_code"),
            nullable=True,
        ),
        sa.Column(
            "seco_code",
            sa.String(50),
            sa.ForeignKey("actif_secondaire.seco_code"),
            nullable=True,
        ),
        sa.Column(
            "tert_code",
            sa.String(50),
            sa.ForeignKey("actif_tertiaire.tert_code"),
            nullable=True,
        ),
        sa.Column(
            "tenant_ville_id",
            sa.Integer(),
            sa.ForeignKey("tenant_ville.tenant_ville_id"),
            nullable=False,
        ),
        sa.Column(
            "tenant_unite_id",
            sa.Integer(),
            sa.ForeignKey("tenant_unite.tenant_unite_id"),
            nullable=True,
        ),
        sa.Column("installation_date", sa.Date(), nullable=True),
        sa.Column("serial_number", sa.String(120), nullable=True),
        sa.Column("attributes", JSONB, nullable=True),
        sa.Column(
            "status_code", sa.String(50), nullable=False, server_default=sa.text("'ACTIF'")
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("end_date", sa.TIMESTAMP(timezone=True), nullable=True),
        # Unique constraint: instance_code per tenant
        sa.UniqueConstraint("instance_code", "tenant_ville_id", name="uq_instance_code_tenant"),
        # CHECK: exactly one of prim_code/seco_code/tert_code is non-null
        sa.CheckConstraint(
            "(CASE WHEN prim_code IS NOT NULL THEN 1 ELSE 0 END"
            " + CASE WHEN seco_code IS NOT NULL THEN 1 ELSE 0 END"
            " + CASE WHEN tert_code IS NOT NULL THEN 1 ELSE 0 END) = 1",
            name="ck_exactly_one_catalog_ref",
        ),
    )

    # --- Import Audit Table ---

    op.create_table(
        "import_record",
        sa.Column("import_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "tenant_ville_id",
            sa.Integer(),
            sa.ForeignKey("tenant_ville.tenant_ville_id"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("created_count", sa.Integer(), nullable=False),
        sa.Column("skipped_count", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("errors_json", JSONB, nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("imported_by", sa.String(100), nullable=False),
        sa.Column(
            "started_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    # --- Partial Indexes for Active-Record Queries (WHERE end_date IS NULL) ---

    op.create_index(
        "idx_actif_fonction_service",
        "actif_fonction",
        ["serv_code"],
        postgresql_where=sa.text("end_date IS NULL"),
    )

    op.create_index(
        "idx_sous_fonction_fonction",
        "sous_fonction",
        ["fonc_code"],
        postgresql_where=sa.text("end_date IS NULL"),
    )

    op.create_index(
        "idx_type_actif_sous_fonc",
        "type_actif",
        ["sous_fonc_code"],
        postgresql_where=sa.text("end_date IS NULL"),
    )

    op.create_index(
        "idx_actif_primaire_type",
        "actif_primaire",
        ["type_actif_code"],
        postgresql_where=sa.text("end_date IS NULL"),
    )

    op.create_index(
        "idx_actif_secondaire_prim",
        "actif_secondaire",
        ["prim_code"],
        postgresql_where=sa.text("end_date IS NULL"),
    )

    op.create_index(
        "idx_actif_tertiaire_seco",
        "actif_tertiaire",
        ["seco_code"],
        postgresql_where=sa.text("end_date IS NULL"),
    )

    op.create_index(
        "idx_instance_tenant",
        "actif_instance",
        ["tenant_ville_id"],
        postgresql_where=sa.text("end_date IS NULL"),
    )

    op.create_index(
        "idx_instance_prim",
        "actif_instance",
        ["prim_code"],
        postgresql_where=sa.text("end_date IS NULL"),
    )

    op.create_index(
        "idx_instance_seco",
        "actif_instance",
        ["seco_code"],
        postgresql_where=sa.text("end_date IS NULL"),
    )

    op.create_index(
        "idx_instance_tert",
        "actif_instance",
        ["tert_code"],
        postgresql_where=sa.text("end_date IS NULL"),
    )

    op.create_index(
        "idx_instance_code_tenant",
        "actif_instance",
        ["instance_code", "tenant_ville_id"],
    )

    # --- Trigram Index for Full-Text Search ---

    op.execute(
        "CREATE INDEX idx_instance_nom_trgm ON actif_instance "
        "USING gin(instance_nom gin_trgm_ops)"
    )


def downgrade() -> None:
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_instance_nom_trgm")
    op.drop_index("idx_instance_code_tenant", table_name="actif_instance")
    op.drop_index("idx_instance_tert", table_name="actif_instance")
    op.drop_index("idx_instance_seco", table_name="actif_instance")
    op.drop_index("idx_instance_prim", table_name="actif_instance")
    op.drop_index("idx_instance_tenant", table_name="actif_instance")
    op.drop_index("idx_actif_tertiaire_seco", table_name="actif_tertiaire")
    op.drop_index("idx_actif_secondaire_prim", table_name="actif_secondaire")
    op.drop_index("idx_actif_primaire_type", table_name="actif_primaire")
    op.drop_index("idx_type_actif_sous_fonc", table_name="type_actif")
    op.drop_index("idx_sous_fonction_fonction", table_name="sous_fonction")
    op.drop_index("idx_actif_fonction_service", table_name="actif_fonction")

    # Drop tables in reverse dependency order
    op.drop_table("import_record")
    op.drop_table("actif_instance")
    op.drop_table("tenant_unite")
    op.drop_table("tenant_ville")
    op.drop_table("actif_tertiaire")
    op.drop_table("actif_secondaire")
    op.drop_table("actif_primaire")
    op.drop_table("actif_discipline")
    op.drop_table("type_actif")
    op.drop_table("sous_fonction")
    op.drop_table("actif_fonction")
    op.drop_table("actif_service")
    op.drop_table("actif_famille")

    # Drop extension
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
