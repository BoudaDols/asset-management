# Implementation Plan: Municipal Asset Management System

## Overview

This plan implements the Municipal Asset Management System V1 as a modular monolith using Python + FastAPI (backend), React + TypeScript (frontend), PostgreSQL 16 (database), Celery + Redis (background tasks). The implementation proceeds incrementally: infrastructure first, then core shared modules, followed by each domain module (catalog, assets, imports, reports), frontend, and finally integration wiring and deployment configuration.

## Tasks

- [x] 1. Project scaffolding and infrastructure setup
  - [x] 1.1 Create backend project structure with FastAPI entry point
    - Create `backend/` directory with `app/__init__.py`, `app/main.py`, `app/core/`, `app/models/`, and module directories (`catalog/`, `assets/`, `imports/`, `reports/`)
    - Set up `pyproject.toml` with all backend dependencies (fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic, pydantic, openpyxl, xlsxwriter, reportlab, celery[redis], redis, python-multipart, slowapi, hypothesis, pytest, pytest-asyncio, httpx, ruff, mypy)
    - Create `app/main.py` with FastAPI app instance, CORS middleware, versioned router prefix `/api/v1/`, health check endpoint, and OpenAPI docs at `/docs` and `/redoc`
    - _Requirements: 10.1, 10.2, 10.9_

  - [x] 1.2 Create frontend project structure with Vite + React + TypeScript
    - Initialize `frontend/` with Vite React-TS template
    - Install dependencies: react, react-dom, typescript, @tanstack/react-query, @tanstack/react-table, react-router-dom, react-hook-form, zod, tailwindcss, axios, lucide-react
    - Configure Tailwind CSS and set up shadcn/ui
    - Create base routing structure with placeholder pages (Catalog, Assets, Import, Reports)
    - _Requirements: 10.1_

  - [x] 1.3 Create Docker Compose configuration for development
    - Create `docker-compose.dev.yml` with services: PostgreSQL 16, Redis, FastAPI (with hot reload), Celery worker, and frontend dev server
    - Create `backend/Dockerfile` for the FastAPI application
    - Create `frontend/Dockerfile` for the React build
    - Create `.env.example` with all required environment variables
    - _Requirements: 10.1_

- [ ] 2. Database schema and migrations
  - [x] 2.1 Set up Alembic and create initial migration
    - Initialize Alembic in `backend/` with async SQLAlchemy configuration
    - Create the initial migration with all tables: `actif_famille`, `actif_service`, `actif_fonction`, `sous_fonction`, `type_actif`, `actif_discipline`, `actif_primaire`, `actif_secondaire`, `actif_tertiaire`, `tenant_ville`, `tenant_unite`, `actif_instance`, `import_record`
    - Include all CHECK constraints (XOR on catalog refs), UNIQUE constraints (instance_code + tenant_ville_id, tenant_code, unite_code), and foreign keys
    - Create all partial indexes for active-record queries (WHERE end_date IS NULL)
    - Create trigram index on `actif_instance.instance_nom` for full-text search
    - _Requirements: 1.1, 2.3, 7.3, 9.1, 10.7_

  - [~] 2.2 Create seed data migration for development
    - Create a second Alembic migration that inserts sample catalog data (at least 2 services with full hierarchy chains down to tertiaire level)
    - Insert sample tenants (2 municipalities with units)
    - Insert sample asset instances (10+ instances across different hierarchy levels and tenants)
    - _Requirements: 1.1, 7.1_

- [x] 3. Core shared modules
  - [x] 3.1 Implement configuration module (`app/core/config.py`)
    - Create Pydantic Settings class loading from environment variables: DATABASE_URL, REDIS_URL, CORS_ORIGINS, MAX_UPLOAD_SIZE, BATCH_SIZE, PAGE_SIZE_DEFAULT, PAGE_SIZE_MAX
    - Implement singleton pattern for settings access
    - _Requirements: 10.1_

  - [x] 3.2 Implement database module (`app/core/database.py`)
    - Create async SQLAlchemy engine and session factory using asyncpg
    - Implement `get_db` dependency for FastAPI route injection
    - Configure connection pooling (pool_size=5, max_overflow=10)
    - Implement health check function that tests database connectivity
    - _Requirements: 10.3, 10.9_

  - [x] 3.3 Implement shared Pydantic schemas and error handling (`app/core/schemas.py`, `app/core/exceptions.py`)
    - Create `PaginatedResult` generic schema with data, total, page, page_size, total_pages
    - Create `ErrorResponse` schema with error_code, message, and details array
    - Create `ValidationErrorDetail` schema with field, value, message
    - Implement custom exception handlers for 400, 404, 409, 413, 503 responses
    - _Requirements: 10.5, 10.8, 8.1_

  - [x] 3.4 Implement shared validators (`app/core/validators.py`)
    - Create `validate_code_format(code: str) -> bool` enforcing `^[A-Z0-9_]{1,50}$`
    - Create `validate_name(name: str) -> bool` enforcing non-empty, non-whitespace-only, max 255 chars
    - Create `validate_instance_code(code: str) -> bool` enforcing `^[A-Za-z0-9_\-]{1,50}$`
    - Create `validate_xor_catalog_ref(prim, seco, tert) -> bool` enforcing exactly one non-null
    - _Requirements: 8.2, 8.3, 8.4, 8.5_

  - [ ]* 3.5 Write property tests for shared validators
    - **Property 4: Code Format Validation** — any string matching `^[A-Z0-9_]{1,50}$` passes, all others fail
    - **Property 16: Name Field Validation** — non-empty strings ≤255 chars pass, empty or >255 fail
    - **Property 1: Catalog Reference XOR Constraint** — exactly one non-null passes, all other combinations fail
    - **Property 13: Validator Determinism** — same input always produces same output
    - **Validates: Requirements 8.2, 8.3, 8.4, 8.5**

- [~] 4. Checkpoint - Ensure infrastructure tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Catalog module implementation
  - [x] 5.1 Create SQLAlchemy models for catalog hierarchy (`app/models/catalog.py`)
    - Implement all 8 hierarchy level models: `ActifFamille`, `ActifService`, `ActifFonction`, `SousFonction`, `TypeActif`, `ActifDiscipline`, `ActifPrimaire`, `ActifSecondaire`, `ActifTertiaire`
    - Define relationships (parent-child) and back_populates
    - Add soft-delete filtering mixin or query helper for `end_date IS NULL`
    - _Requirements: 1.1, 1.5, 9.1_

  - [~] 5.2 Create Pydantic schemas for catalog module (`app/catalog/schemas.py`)
    - Create request DTOs: `CreateCatalogEntryDto`, `UpdateCatalogEntryDto` with code pattern validation
    - Create response schemas for each hierarchy level
    - Create `HierarchyNode` schema with code, nom, level, children (recursive)
    - _Requirements: 1.7, 1.8, 1.12_

  - [~] 5.3 Implement CatalogService (`app/catalog/service.py`)
    - Implement `get_hierarchy_tree(service_code: str | None)` using CTE query returning tree structure
    - Implement `create_catalog_entry(level, dto)` with parent validation, code uniqueness, code format checks
    - Implement `update_catalog_entry(level, code, dto)` with code immutability enforcement
    - Implement `deactivate_catalog_entry(level, code)` with active-children check
    - Implement `restore_catalog_entry(level, code)` with parent-active check
    - Implement level-specific getters (get_services, get_fonctions, etc.)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 1.12, 9.4, 9.5, 9.6, 9.7_

  - [~] 5.4 Implement catalog API router (`app/catalog/router.py`)
    - `GET /api/v1/catalog/tree` — returns full hierarchy tree, optional `service_code` filter
    - `GET /api/v1/catalog/{level}` — list entries at a specific level
    - `POST /api/v1/catalog/{level}` — create new catalog entry
    - `PUT /api/v1/catalog/{level}/{code}` — update catalog entry (name only, code immutable)
    - `DELETE /api/v1/catalog/{level}/{code}` — soft-delete (deactivate) entry
    - `POST /api/v1/catalog/{level}/{code}/restore` — restore soft-deleted entry
    - _Requirements: 1.1–1.12, 9.1–9.7, 10.1_

  - [ ]* 5.5 Write property tests for catalog module
    - **Property 2: Hierarchy Chain Consistency** — for any created entry, a valid parent chain exists up to root
    - **Property 6: Soft Delete Exclusion** — deactivated entries never appear in tree queries
    - **Property 11: Active Parent Reference Enforcement** — creating a child under an inactive parent is rejected
    - **Property 15: Hierarchy Tree Filtered Containment** — filtered tree only contains nodes from the specified service subtree
    - **Validates: Requirements 1.3, 1.5, 1.6, 3.11, 9.2, 9.4**

  - [ ]* 5.6 Write unit tests for CatalogService
    - Test tree construction with known seed data
    - Test code uniqueness enforcement
    - Test code immutability on update
    - Test deactivation blocked by active children
    - Test restore blocked by inactive parent
    - _Requirements: 1.6, 1.7, 1.9, 1.11, 1.12, 9.5, 9.6_

- [ ] 6. Asset instance module implementation
  - [x] 6.1 Create SQLAlchemy model for asset instances (`app/models/asset_instance.py`)
    - Implement `ActifInstance` model with all fields, relationships, constraints (XOR check, unique code+tenant)
    - Implement `TenantVille` and `TenantUnite` models with relationships
    - _Requirements: 2.1, 2.3, 7.1, 7.3_

  - [~] 6.2 Create Pydantic schemas for asset module (`app/assets/schemas.py`)
    - Create `CreateAssetInstanceDto` with field validators (code pattern, XOR constraint, JSONB size limit 10KB)
    - Create `UpdateAssetInstanceDto` with code immutability enforcement
    - Create `AssetInstanceResponse` with all fields
    - Create `AssetInstanceFilter` with all filterable fields and pagination params
    - _Requirements: 2.1, 2.4, 2.6, 2.7, 2.9, 8.4, 8.7_

  - [~] 6.3 Implement AssetInstanceService (`app/assets/service.py`)
    - Implement `create(dto)` with catalog reference validation, tenant validation, code uniqueness check
    - Implement `find_by_id(instance_id)` returning active instance or None
    - Implement `find_all(filters)` with pagination, multi-field filtering (hierarchy levels, tenant, JSONB attributes), deterministic sort with tiebreaker
    - Implement `update(instance_id, dto)` with same validation as create, code immutability
    - Implement `deactivate(instance_id)` setting end_date
    - _Requirements: 2.1–2.10, 7.1, 7.2, 8.6, 8.7, 9.1_

  - [~] 6.4 Implement asset API router (`app/assets/router.py`)
    - `POST /api/v1/actif-instances` — create asset instance
    - `GET /api/v1/actif-instances` — list with filters and pagination
    - `GET /api/v1/actif-instances/{id}` — get single instance
    - `PUT /api/v1/actif-instances/{id}` — update instance
    - `DELETE /api/v1/actif-instances/{id}` — soft-delete instance
    - _Requirements: 2.1–2.10, 10.1, 10.5_

  - [~] 6.5 Implement tenant API router (`app/assets/tenant_router.py`)
    - `POST /api/v1/tenants` — create tenant with code validation and uniqueness
    - `GET /api/v1/tenants` — list active tenants
    - `GET /api/v1/tenants/{id}/unites` — list units for a tenant
    - `POST /api/v1/tenants/{id}/unites` — create unit
    - _Requirements: 7.1–7.8_

  - [ ]* 6.6 Write property tests for asset instance module
    - **Property 1: Catalog Reference XOR Constraint** — integration test with DB: only exactly-one-ref instances are persisted
    - **Property 5: Instance Code Uniqueness per Tenant** — same code in different tenants succeeds, same code in same tenant fails
    - **Property 9: Tenant Isolation** — queries scoped to tenant t never return instances from other tenants
    - **Validates: Requirements 2.1, 2.3, 7.2, 7.3**

  - [ ]* 6.7 Write unit tests for AssetInstanceService
    - Test creation with valid/invalid catalog references
    - Test code immutability on update
    - Test pagination and filtering
    - Test inactive tenant rejection
    - Test JSONB size limit enforcement
    - _Requirements: 2.1–2.10, 7.8, 8.7_

- [~] 7. Checkpoint - Ensure catalog and asset tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Import module implementation
  - [~] 8.1 Create import schemas and models (`app/imports/schemas.py`, `app/models/import_record.py`)
    - Create `ImportOptions` dataclass (tenant_ville_id, tenant_unite_id, dry_run, skip_duplicates)
    - Create `ImportResult` schema (total_rows, created, skipped, errors, duration_ms)
    - Create `ImportError` schema (row, column, value, message, severity)
    - Create `ImportRecord` SQLAlchemy model for audit persistence
    - _Requirements: 3.6, 3.10, 4.1, 4.6_

  - [~] 8.2 Implement Excel template validation (`app/imports/template_validator.py`)
    - Implement file type validation (.xlsx magic bytes check)
    - Implement file size validation (≤50MB)
    - Implement sheet name validation ("Actifs" sheet required)
    - Implement column header validation (required columns: instance_code, instance_nom, serv_code, fonc_code, sous_fonc_code, type_actif_code, and at least one of prim_code/seco_code/tert_code)
    - Implement row count validation (≤50,000 data rows)
    - _Requirements: 3.1, 3.2, 4.4, 4.5_

  - [~] 8.3 Implement row validation and hierarchy code resolution (`app/imports/row_validator.py`)
    - Implement `validate_import_row(row_data)` checking required fields, code formats, date formats
    - Implement `resolve_hierarchy_codes(row, db)` resolving all codes to active catalog entries
    - Implement hierarchy chain consistency verification (child belongs to declared parent at every level)
    - Implement error collection with row number, column, value (truncated to 255 chars), message (max 500 chars), severity
    - _Requirements: 3.3, 3.4, 3.11, 4.1_

  - [~] 8.4 Implement ImportService core logic (`app/imports/service.py`)
    - Implement `process_excel_import(file, options, db)` with streaming parser (openpyxl read_only mode)
    - Implement batch insertion (100 rows per batch) with per-batch rollback on error
    - Implement duplicate detection with skip_duplicates option
    - Implement dry_run mode (validate without persisting)
    - Implement error cap at 1000 entries with truncation indicator
    - Implement import audit record persistence (filename, SHA-256 hash, counts, timestamps)
    - Enforce accounting identity: created + skipped + errors == total_rows
    - _Requirements: 3.3–3.12, 4.2, 4.3_

  - [~] 8.5 Implement Celery task for async imports (`app/imports/tasks.py`)
    - Create Celery app configuration with Redis broker
    - Implement `import_task.delay(file_bytes, options)` for all imports (always async)
    - Implement task result awaiting (response returned after processing completes)
    - Implement conditional HTTP status codes: 200 (all success), 207 (partial), 422 (total failure)
    - _Requirements: 3.8, 3.12_

  - [~] 8.6 Implement import API router (`app/imports/router.py`)
    - `POST /api/v1/imports/upload` — upload Excel file (multipart/form-data), route to sync or async based on size
    - `GET /api/v1/imports/{task_id}/status` — poll async import status
    - `GET /api/v1/imports/history` — paginated import history (page_size 1–100)
    - `GET /api/v1/imports/template` — download blank Excel template
    - _Requirements: 3.1, 3.8, 3.12, 4.6, 10.4_

  - [ ]* 8.7 Write property tests for import module
    - **Property 3: Import Accounting Identity** — for any set of rows, created + skipped + errors == total_rows
    - **Property 7: Import Idempotency** — importing same file twice with skip_duplicates=True yields created=0 on second run
    - **Property 12: Dry Run No Side Effects** — database state unchanged after dry_run=True import
    - **Validates: Requirements 3.5, 3.6, 3.7**

  - [ ]* 8.8 Write unit tests for import module
    - Test template validation (missing columns, wrong format, oversized file)
    - Test row validation (invalid codes, missing required fields, invalid dates)
    - Test hierarchy chain resolution (valid chain, broken chain, inactive entries)
    - Test batch insertion and rollback behavior
    - Test error cap at 1000 entries
    - _Requirements: 3.1–3.12, 4.1–4.6_

- [~] 9. Checkpoint - Ensure import tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Report module implementation
  - [~] 10.1 Create report schemas (`app/reports/schemas.py`)
    - Create `ReportFilter` with all filter fields (service_code, fonction_code, sous_fonction_code, type_actif_code, tenant_ville_id, tenant_unite_id, discipline, installation_date_from/to, search, page, page_size, sort_by, sort_order)
    - Create `AssetRow` response schema for inventory reports
    - Create `GroupedReport` schema with level_code, level_name, count per group
    - Create `SummaryReport` schema with aggregated counts by hierarchy and tenant
    - Create `ExportRequest` schema with report_type and filters
    - _Requirements: 5.1–5.8, 6.1–6.5_

  - [~] 10.2 Implement ReportService queries (`app/reports/service.py`)
    - Implement `get_asset_inventory(filters)` with paginated results, AND-logic filtering, deterministic sort with instance_id tiebreaker
    - Implement `get_assets_by_hierarchy(level, filters)` grouping assets by specified hierarchy level with counts
    - Implement `get_asset_count_summary(filters)` returning aggregated counts by hierarchy and tenant
    - Implement full-text search on instance_nom/instance_code (case-insensitive substring, min 1 char)
    - Return empty results (not errors) for non-existent filter codes
    - _Requirements: 5.1–5.9_

  - [~] 10.3 Implement report export functionality (`app/reports/export.py`)
    - Implement `export_to_excel(report_type, filters)` generating .xlsx with xlsxwriter (column headers + all matching rows, ignoring pagination)
    - Implement `export_to_pdf(report_type, filters)` generating PDF with reportlab (title, headers, tabular data, page numbers)
    - Implement async export via Celery for result sets >1000 rows
    - Implement export file storage and retrieval endpoint
    - _Requirements: 6.1–6.5_

  - [~] 10.4 Implement report API router (`app/reports/router.py`)
    - `GET /api/v1/reports/inventory` — paginated inventory report with filters
    - `GET /api/v1/reports/by-hierarchy` — grouped report by hierarchy level
    - `GET /api/v1/reports/summary` — aggregated summary report
    - `POST /api/v1/reports/export/excel` — trigger Excel export (sync or async)
    - `POST /api/v1/reports/export/pdf` — trigger PDF export (sync or async)
    - `GET /api/v1/reports/export/{task_id}` — poll/download export result
    - _Requirements: 5.1–5.9, 6.1–6.5, 10.1_

  - [ ]* 10.5 Write property tests for report module
    - **Property 8: Pagination Completeness** — union of all pages equals full result set with no duplicates or missing items
    - **Property 10: Filter Monotonicity** — adding a filter never increases result count
    - **Property 14: Export Data Consistency** — exported data matches API query results for same filters
    - **Validates: Requirements 5.2, 5.8, 6.1, 6.3**

  - [ ]* 10.6 Write unit tests for report module
    - Test pagination with known dataset (verify total_pages, page boundaries)
    - Test all filter combinations (AND logic)
    - Test sort order (ascending/descending, tiebreaker)
    - Test empty results for non-existent filter codes
    - Test export file generation (valid xlsx, valid pdf)
    - _Requirements: 5.1–5.9, 6.1–6.5_

- [~] 11. Checkpoint - Ensure report tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Frontend implementation
  - [~] 12.1 Implement shared frontend infrastructure
    - Create API client with axios (base URL, error interceptors, typed responses)
    - Create React Query configuration and query key factory
    - Create shared UI components: DataTable (with @tanstack/react-table), Pagination, LoadingSpinner, ErrorBoundary, ConfirmDialog
    - Create layout component with navigation sidebar (Catalog, Assets, Import, Reports)
    - _Requirements: 10.1_

  - [~] 12.2 Implement catalog hierarchy view
    - Create tree view component displaying the 8-level hierarchy with expand/collapse
    - Create catalog entry form (create/edit) with code and name validation
    - Implement service filter dropdown for tree filtering
    - Implement soft-delete (deactivate) with confirmation dialog
    - Wire to `GET /api/v1/catalog/tree`, `POST/PUT/DELETE` catalog endpoints
    - _Requirements: 1.1–1.12_

  - [~] 12.3 Implement asset instance management views
    - Create asset list view with DataTable, pagination, column sorting, and multi-field filters
    - Create asset creation form with catalog reference selector (dropdown filtered by hierarchy), tenant selector, JSONB attributes editor
    - Create asset detail/edit view with field validation
    - Implement soft-delete with confirmation
    - Wire to all `/api/v1/actif-instances` endpoints
    - _Requirements: 2.1–2.10, 7.1–7.8_

  - [~] 12.4 Implement Excel import view
    - Create file upload component with drag-and-drop, .xlsx validation, size display
    - Create import options form (tenant selection, dry_run toggle, skip_duplicates toggle)
    - Create import progress indicator (polling for async imports)
    - Create import results view showing created/skipped/error counts and error table (row, column, value, message)
    - Create import history table with pagination
    - Wire to `/api/v1/imports/*` endpoints
    - _Requirements: 3.1–3.12, 4.1–4.6_

  - [~] 12.5 Implement report views
    - Create inventory report view with filter panel (service, fonction, tenant, date range, search) and paginated DataTable
    - Create hierarchy-grouped report view with level selector and grouped display
    - Create summary report view with aggregated counts
    - Create export buttons (Excel, PDF) with async download handling
    - Wire to `/api/v1/reports/*` endpoints
    - _Requirements: 5.1–5.9, 6.1–6.5_

- [ ] 13. Integration wiring and API completion
  - [~] 13.1 Wire all module routers into FastAPI application
    - Register catalog, assets, imports, and reports routers in `app/main.py`
    - Configure CORS middleware with allowed origins from settings
    - Configure rate limiting on import upload endpoint (slowapi)
    - Implement global exception handlers (503 for DB failures, 413 for oversized uploads, 409 for conflicts)
    - Verify OpenAPI docs generation at `/docs` and `/redoc`
    - _Requirements: 10.1–10.9_

  - [~] 13.2 Implement Celery worker configuration
    - Create `app/worker.py` with Celery app instance and Redis broker configuration
    - Register import and export tasks
    - Configure task serialization (JSON), result backend (Redis), and task timeouts
    - _Requirements: 3.8, 6.4_

  - [ ]* 13.3 Write integration tests for full API flows
    - Test complete asset creation flow (create tenant → create catalog entries → create instance → verify)
    - Test complete import flow (upload file → poll status → verify instances created)
    - Test complete report flow (seed data → query with filters → verify results → export)
    - Test error scenarios (invalid file, duplicate codes, inactive references, concurrent conflicts)
    - Test health check endpoint (200 when DB available, 503 when not)
    - _Requirements: 10.3, 10.6, 10.7, 10.9_

- [ ] 14. Docker and deployment configuration
  - [~] 14.1 Create production Docker configuration
    - Create multi-stage `backend/Dockerfile` (build + runtime with slim Python image)
    - Create multi-stage `frontend/Dockerfile` (build with Node + serve with Nginx)
    - Create `docker-compose.yml` for production (API, Celery worker, PostgreSQL, Redis, Nginx reverse proxy)
    - Create Nginx configuration with TLS termination, static file serving, and API proxy
    - Create `docker-compose.dev.yml` override for development (hot reload, exposed ports, volume mounts)
    - _Requirements: 10.1_

  - [~] 14.2 Create CI/CD pipeline configuration
    - Update `.github/workflows/deploy.yml` with: lint (ruff), type check (mypy), test (pytest with PostgreSQL service container), build Docker images, push to registry
    - Add test coverage reporting (pytest-cov)
    - _Requirements: 10.1_

- [~] 15. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The backend uses Python + FastAPI with SQLAlchemy async and Alembic migrations
- The frontend uses React + TypeScript with Vite, TanStack Query/Table, and shadcn/ui
- All code fields use French domain terminology (serv_code, fonc_code, etc.) as specified in the design
- Background processing (Celery + Redis) handles all imports (always async) and large exports (>1000 rows)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["1.3", "3.1"] },
    { "id": 2, "tasks": ["3.2", "3.3", "3.4"] },
    { "id": 3, "tasks": ["3.5", "2.1"] },
    { "id": 4, "tasks": ["2.2", "5.1", "6.1"] },
    { "id": 5, "tasks": ["5.2", "5.3", "6.2"] },
    { "id": 6, "tasks": ["5.4", "5.5", "5.6", "6.3"] },
    { "id": 7, "tasks": ["6.4", "6.5", "6.6", "6.7"] },
    { "id": 8, "tasks": ["8.1", "8.2", "10.1"] },
    { "id": 9, "tasks": ["8.3", "8.4", "10.2"] },
    { "id": 10, "tasks": ["8.5", "8.6", "10.3"] },
    { "id": 11, "tasks": ["8.7", "8.8", "10.4"] },
    { "id": 12, "tasks": ["10.5", "10.6", "12.1"] },
    { "id": 13, "tasks": ["12.2", "12.3"] },
    { "id": 14, "tasks": ["12.4", "12.5"] },
    { "id": 15, "tasks": ["13.1", "13.2"] },
    { "id": 16, "tasks": ["13.3", "14.1"] },
    { "id": 17, "tasks": ["14.2"] }
  ]
}
```
