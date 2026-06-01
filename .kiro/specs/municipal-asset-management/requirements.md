# Requirements Document

## Introduction

This document defines the requirements for the Municipal Asset Management System V1. The system manages municipal infrastructure assets (water systems, pumping stations, reservoirs, etc.) organized in a strict 8-level hierarchy. V1 covers: asset catalog management, manual asset instance data entry, Excel bulk import with validation, general and specific reports with export, and multi-tenant support for multiple municipalities.

The system is built with Python + FastAPI (backend), React + TypeScript (frontend), PostgreSQL 16 (database), and Celery + Redis (background processing).

## Glossary

- **System**: The Municipal Asset Management System as a whole
- **Catalog**: The global 8-level asset hierarchy taxonomy shared across all municipalities
- **Hierarchy**: The 8-level tree structure: Service → Fonction → Sous-fonction → Type d'actif → Actif primaire → Discipline → Actif secondaire → Actif tertiaire
- **Catalog_Entry**: A single node in the hierarchy at any level (e.g., a Service, a Fonction, etc.)
- **Asset_Instance**: A concrete physical asset belonging to a specific municipality, linked to exactly one catalog level (primaire, secondaire, or tertiaire)
- **Tenant**: A municipality (ville) that owns asset instances; the unit of data isolation
- **Tenant_Ville**: A municipality entity representing the top-level tenant
- **Tenant_Unite**: A sub-unit within a municipality (e.g., a specific facility or district)
- **Import_Service**: The module responsible for parsing, validating, and bulk-inserting asset instances from Excel files
- **Report_Service**: The module responsible for generating filtered, paginated, and exportable reports
- **Catalog_Service**: The module responsible for managing the 8-level hierarchy
- **Asset_Service**: The module responsible for CRUD operations on asset instances
- **Validator**: The component that validates input data (row-level for imports, schema-level for API requests)
- **Code**: A unique alphanumeric identifier (uppercase + underscore, max 50 chars) assigned to each catalog entry
- **Soft_Delete**: Marking a record as inactive by setting an end_date rather than physically removing it
- **Dry_Run**: An import mode that validates data without persisting changes to the database
- **Import_Result**: The outcome of an import operation containing counts of created, skipped, and errored rows
- **Hierarchy_Chain**: The complete path from a leaf node up through all parent levels to the root Service

## Requirements

### Requirement 1: Asset Catalog Hierarchy Management

**User Story:** As a municipal operator, I want to browse and manage the asset catalog hierarchy, so that I can organize assets according to the standardized 8-level classification.

#### Acceptance Criteria

1. THE Catalog_Service SHALL maintain an 8-level hierarchy structure: Service → Fonction → Sous-fonction → Type d'actif → Actif primaire → Discipline → Actif secondaire → Actif tertiaire
2. WHEN a user requests the hierarchy tree, THE Catalog_Service SHALL return a tree structure where each node contains its code, name, level, and children
3. WHEN a user requests the hierarchy tree filtered by a service code, THE Catalog_Service SHALL return only the subtree rooted at that service
4. IF a user requests the hierarchy tree filtered by a service code that does not exist or is inactive, THEN THE Catalog_Service SHALL return an empty tree structure
5. THE Catalog_Service SHALL return only active entries (entries where end_date IS NULL) in all query results
6. WHEN a user creates a new catalog entry at level 2 or below, THE Catalog_Service SHALL validate that the parent reference exists and is active
7. WHEN a user creates a new catalog entry, THE Catalog_Service SHALL enforce that the code is unique within its hierarchy level
8. WHEN a user creates a new catalog entry, THE Catalog_Service SHALL validate that the code matches the pattern: uppercase alphanumeric plus underscore, between 1 and 50 characters
9. IF a catalog entry creation fails validation due to an inactive parent, a duplicate code, or an invalid code pattern, THEN THE Catalog_Service SHALL return a 400 response with field-level error details indicating the specific validation failure
10. WHEN a user deactivates a catalog entry, THE Catalog_Service SHALL set the end_date field to the current timestamp rather than physically deleting the record
11. IF a user attempts to deactivate a catalog entry that has active child entries, THEN THE Catalog_Service SHALL reject the request with an error message indicating that active children must be deactivated first
12. THE Catalog_Service SHALL enforce that codes are immutable after creation; IF a user attempts to modify a code field, THEN THE Catalog_Service SHALL return a 400 response with an error message indicating that codes cannot be changed

### Requirement 2: Asset Instance Management

**User Story:** As a municipal operator, I want to create, view, update, and deactivate physical asset instances, so that I can maintain an accurate inventory of my municipality's infrastructure.

#### Acceptance Criteria

1. WHEN a user creates an asset instance, THE Asset_Service SHALL validate that exactly one catalog reference (prim_code, seco_code, or tert_code) is provided
2. WHEN a user creates an asset instance, THE Asset_Service SHALL verify that the referenced catalog entry exists and is active (end_date IS NULL)
3. WHEN a user creates an asset instance, THE Asset_Service SHALL enforce that the instance_code is unique within the tenant_ville_id
4. WHEN a user creates an asset instance, THE Asset_Service SHALL validate that the instance_code matches the pattern: alphanumeric plus underscore and hyphen, between 1 and 50 characters
5. WHEN a user creates an asset instance, THE Asset_Service SHALL require a tenant_ville_id referencing an active tenant (end_date IS NULL and is_active is true)
6. WHEN a user requests a list of asset instances, THE Asset_Service SHALL return only active instances (end_date IS NULL) as paginated results with a configurable page size between 1 and 500, filtered by any combination of hierarchy levels (service, fonction, sous-fonction, type_actif, prim_code, seco_code, tert_code), tenant_ville_id, tenant_unite_id, and JSONB attributes
7. WHEN a user updates an asset instance, THE Asset_Service SHALL validate all modified fields against the same rules as creation and SHALL reject changes to the instance_code field
8. WHEN a user deactivates an asset instance, THE Asset_Service SHALL set the end_date field to the current timestamp rather than physically deleting the record
9. THE Asset_Service SHALL store type-specific physical attributes in a JSONB field on the asset instance, limited to 10KB per instance
10. IF any creation or update validation fails, THEN THE Asset_Service SHALL return a 400 response containing field-level error details identifying each invalid field, the rejected value, and a descriptive error message

### Requirement 3: Excel Bulk Import

**User Story:** As a municipal operator, I want to import asset instances in bulk from Excel files, so that I can efficiently populate the system with existing inventory data.

#### Acceptance Criteria

1. WHEN a user uploads an Excel file, THE Import_Service SHALL accept only .xlsx files up to 50MB in size and containing no more than 50,000 data rows
2. WHEN a user uploads an Excel file, THE Import_Service SHALL validate that the file contains a sheet named "Actifs" with at minimum the following column headers: instance_code, instance_nom, serv_code, fonc_code, sous_fonc_code, type_actif_code, and at least one of prim_code, seco_code, or tert_code
3. WHEN processing an import, THE Import_Service SHALL validate each row by resolving all provided hierarchy codes (serv_code, fonc_code, sous_fonc_code, type_actif_code, prim_code, seco_code, tert_code) to active catalog entries with no end_date set
4. WHEN a row references a code that does not exist in the catalog or references an inactive catalog entry, THE Import_Service SHALL skip that row and record an error with the row number, column name, invalid value, and a descriptive message
5. IF a row contains a duplicate instance_code for the same tenant and skip_duplicates is enabled, THEN THE Import_Service SHALL skip that row and increment the skipped count
6. WHEN processing completes, THE Import_Service SHALL return an Import_Result where created + skipped + error count equals total_rows
7. IF dry_run mode is enabled, THEN THE Import_Service SHALL validate all rows without persisting any changes to the database and still return a complete Import_Result
8. WHEN a user uploads an Excel file, THE Import_Service SHALL always process the import asynchronously via a Celery background task regardless of file size, and SHALL return the response only after the entire file has been processed
9. WHEN processing an import, THE Import_Service SHALL insert rows in batches of 100, rolling back only the failing batch and recording errors for its rows if a database error occurs within that batch
10. WHEN an import completes, THE Import_Service SHALL persist an import audit record containing filename, SHA-256 file hash, total_rows, created_count, skipped_count, error_count, errors as JSON, started_at timestamp, and completed_at timestamp
11. WHEN resolving hierarchy codes, THE Import_Service SHALL verify that the complete hierarchy chain is consistent (child belongs to declared parent at every level) and skip the row with a descriptive error if any parent-child relationship is invalid
12. WHEN all rows are imported successfully, THE Import_Service SHALL return HTTP 200. WHEN some rows fail or are skipped, THE Import_Service SHALL return HTTP 207 (Multi-Status). WHEN no rows can be imported, THE Import_Service SHALL return HTTP 422.

### Requirement 4: Import Error Reporting

**User Story:** As a municipal operator, I want detailed error reports from failed imports, so that I can identify and fix data issues in my Excel files.

#### Acceptance Criteria

1. WHEN a row fails validation, THE Import_Service SHALL record an error containing: row number, column name, the invalid value (truncated to 255 characters if longer), an error message (max 500 characters), and severity (error or warning) where "error" means the row was not inserted and "warning" means the row was inserted but a potential issue was detected
2. WHEN an import completes with errors, THE Import_Service SHALL return all collected errors in the Import_Result up to a maximum of 1000 error entries, ordered by row number ascending
3. IF the number of validation errors reaches 1000 during import processing, THEN THE Import_Service SHALL continue processing remaining rows but stop recording additional errors, and SHALL indicate in the Import_Result that the error list was truncated
4. WHEN the uploaded file is not a valid .xlsx file, THE System SHALL return a 400 error with error code "INVALID_TEMPLATE" and a message indicating the file format is not a valid .xlsx file
5. WHEN the uploaded file lacks required columns, THE System SHALL return a 400 error listing the missing column names
6. WHEN a user queries import history, THE Import_Service SHALL return past import records paginated with a configurable page size between 1 and 100, each record containing: import_id, filename, status, total_rows, created_count, skipped_count, error_count, started_at, and completed_at

### Requirement 5: Report Generation

**User Story:** As a municipal operator, I want to generate reports on my asset inventory with filtering and grouping, so that I can analyze and communicate the state of municipal infrastructure.

#### Acceptance Criteria

1. WHEN a user requests an inventory report, THE Report_Service SHALL return a paginated result containing the list of matching asset instances, the total count, current page number, page size, and total pages, returning an empty list with total count of 0 when no assets match the filters
2. WHEN a user provides filter criteria, THE Report_Service SHALL apply all filters using AND logic so that results match every specified criterion
3. WHEN a user requests a hierarchy-grouped report with a valid hierarchy level (Service, Fonction, Sous-fonction, Type d'actif, Actif primaire, Discipline, Actif secondaire, or Actif tertiaire), THE Report_Service SHALL return assets grouped by that level, with each group containing the level code, level name, and the count of matching assets
4. WHEN a user requests a summary report, THE Report_Service SHALL return aggregated counts of assets broken down by hierarchy level and tenant, including the total count per group
5. THE Report_Service SHALL support filtering by: service_code, fonction_code, sous_fonction_code, type_actif_code, tenant_ville_id, tenant_unite_id, discipline, installation_date range (from/to bounds), and case-insensitive substring search on instance_nom or instance_code with a minimum query length of 1 character
6. THE Report_Service SHALL support pagination with configurable page size between 1 and 500 items per page, defaulting to 25 items per page when no page size is specified
7. THE Report_Service SHALL support sorting by any column present in the report response (instance_code, instance_nom, installation_date, status_code, tenant, and hierarchy codes) in ascending or descending order, defaulting to ascending order by instance_code when no sort parameter is specified
8. WHEN paginating results, THE Report_Service SHALL use a deterministic sort order with a tiebreaker (instance_id) to prevent duplicate or missing items across pages
9. IF a filter references a code value that does not exist in the catalog or tenant tables, THEN THE Report_Service SHALL return an empty result set rather than an error, treating the non-existent value as matching zero records

### Requirement 6: Report Export

**User Story:** As a municipal operator, I want to export reports to Excel and PDF formats, so that I can share asset information with stakeholders who do not have system access.

#### Acceptance Criteria

1. WHEN a user requests an Excel export, THE Report_Service SHALL generate a valid .xlsx file containing column headers matching the report schema and all data rows matching the applied filters, regardless of the current pagination page
2. WHEN a user requests a PDF export, THE Report_Service SHALL generate a valid PDF document containing a report title, column headers, tabular data rows matching the applied filters, and page numbers on each page
3. WHEN generating an export, THE Report_Service SHALL apply the same filters as the on-screen report so that exported data matches the filtered view
4. WHEN an export result set exceeds 1000 rows, THE Report_Service SHALL process the export asynchronously via a background task and return a task_id that the user can poll for completion status and file retrieval
5. IF an export generation fails due to a system error, THEN THE Report_Service SHALL return an error indicating the failure reason and shall not produce a partial or corrupted file

### Requirement 7: Multi-Tenant Support

**User Story:** As a system administrator, I want the system to support multiple municipalities, so that each municipality's data is isolated and independently manageable.

#### Acceptance Criteria

1. THE System SHALL associate every asset instance with exactly one Tenant_Ville
2. WHEN querying asset instances scoped to a tenant, THE System SHALL return only instances belonging to that tenant
3. THE System SHALL enforce that instance_code uniqueness is scoped to the tenant_ville_id (the same code may exist in different municipalities)
4. WHEN a user creates a tenant, THE System SHALL validate that the tenant_code is unique across all tenants and matches the pattern: uppercase alphanumeric plus underscore, between 1 and 50 characters
5. THE System SHALL support an optional Tenant_Unite sub-level within each Tenant_Ville, where unite_code is unique across all tenants globally
6. WHEN importing assets, THE Import_Service SHALL associate all created instances with the specified tenant_ville_id from the import options
7. IF a user attempts to create a tenant with a tenant_code that already exists, THEN THE System SHALL return a 400 response with an error message indicating the duplicate code
8. IF a Tenant_Ville has end_date set, THEN THE System SHALL reject creation of new asset instances referencing that tenant with a 400 response indicating the tenant is inactive

### Requirement 8: Data Validation

**User Story:** As a municipal operator, I want the system to validate all input data, so that the database maintains integrity and I receive clear feedback on invalid entries.

#### Acceptance Criteria

1. WHEN an API request contains invalid data, THE System SHALL return a 400 response containing an array of error objects, each specifying the field name, the rejected value, and a message indicating the validation rule that failed, covering all invalid fields in the request rather than stopping at the first error
2. THE Validator SHALL enforce that all code fields match the pattern: uppercase alphanumeric plus underscore, between 1 and 50 characters
3. THE Validator SHALL enforce that all name fields contain at least 1 non-whitespace character and do not exceed 255 characters, rejecting whitespace-only strings as invalid
4. WHEN creating an asset instance, THE Validator SHALL enforce that exactly one of prim_code, seco_code, or tert_code is provided (XOR constraint)
5. THE Validator SHALL produce deterministic results: the same input always produces the same validation outcome
6. WHEN a catalog reference is provided, THE Validator SHALL verify that the referenced entry exists and has no end_date set
7. THE Validator SHALL enforce that optional fields conform to their type constraints: serial_number does not exceed 120 characters, installation_date is a valid ISO 8601 date (YYYY-MM-DD), and tenant_unite_id references an active unit belonging to the specified tenant_ville_id

### Requirement 9: Soft Delete and Data Lifecycle

**User Story:** As a system administrator, I want records to be soft-deleted rather than physically removed, so that historical data is preserved and accidental deletions are recoverable.

#### Acceptance Criteria

1. WHEN a user deletes a catalog entry or asset instance, THE System SHALL set the end_date field to the current timestamp and retain all other field values unchanged
2. WHILE a record has end_date set to a non-null value, THE System SHALL exclude that record from all user-facing API query endpoints, including list, search, filter, and hierarchy tree responses
3. THE System SHALL preserve all soft-deleted records in the database indefinitely without automatic purging
4. IF a user attempts to create a new child catalog entry referencing a parent whose end_date is non-null, THEN THE System SHALL reject the request and return an error indicating that the referenced parent is inactive
5. WHEN a user restores a soft-deleted record, THE System SHALL set the end_date field back to NULL, making the record visible again in standard query results
6. IF a user attempts to restore a catalog entry whose parent has a non-null end_date, THEN THE System SHALL reject the restore and return an error indicating that the parent must be restored first
7. WHEN a parent catalog entry is deactivated, THE System SHALL continue to return existing active child entries in query results but SHALL prevent creation of new child entries referencing that parent

### Requirement 10: API Design and Performance

**User Story:** As a developer integrating with the system, I want a well-structured REST API with predictable performance, so that I can build reliable client applications.

#### Acceptance Criteria

1. THE System SHALL expose a RESTful API with versioned endpoints under the /api/v1/ prefix
2. THE System SHALL provide auto-generated OpenAPI documentation accessible at /docs and /redoc
3. WHEN a database connection fails, THE System SHALL return a 503 response with a JSON body containing an error_code field set to "SERVICE_UNAVAILABLE" and a message field describing the failure
4. WHEN a file upload exceeds 50MB, THE System SHALL return a 413 response with a JSON body containing the maximum allowed size in bytes
5. THE System SHALL validate all request payloads using Pydantic schemas before processing
6. WHEN two concurrent imports create conflicting instance codes, THE System SHALL roll back the conflicting transaction and return a 409 response with a JSON body containing the conflicting instance_code and tenant_ville_id
7. THE System SHALL respond to single-resource API requests within 500 milliseconds and to paginated list requests within 2000 milliseconds under normal operating conditions (database connected, fewer than 100 concurrent requests)
8. WHEN an API request fails validation or encounters an error, THE System SHALL return a JSON error response containing at minimum: error_code (string), message (string), and for validation errors a details array with field-level errors
9. THE System SHALL expose a health check endpoint at /api/v1/health that returns a 200 response when the database connection is available and a 503 response when it is not
