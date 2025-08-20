# Story 1.4: Core Database and Services Setup

## Status
- Approved

## Story
- **As a** Backend Developer,
- **I want** the PostgreSQL database and core application services to be set up,
- **so that** we have a foundation for storing data and implementing business logic.

## Acceptance Criteria
1.  A PostgreSQL service is added to the `docker-compose.yml` file.
2.  A database migration tool (e.g., Alembic) is configured for the backend.
3.  The initial database schema for the `tenants` and `users` tables (for Local Auth) is created via a migration.
4.  The FastAPI backend successfully connects to the PostgreSQL database on startup.

## Tasks / Subtasks
- [ ] Task 1: Add PostgreSQL service to the `docker-compose.yml` file. (AC: #1)
- [ ] Task 2: Configure a database migration tool (e.g., Alembic) for the backend. (AC: #2)
- [ ] Task 3: Create the initial `tenants` and `users` schema via a migration. (AC: #3)
- [ ] Task 4: Ensure the FastAPI backend connects to the database on startup. (AC: #4)

## Dev Notes
- **Dependency:** This story depends on the completion of **Story 1.1**, which sets up the backend application and the initial `docker-compose.yml`.
- The `docker-compose.yml` file should be updated to include a `postgres` service using the official `postgres:15` image.
- **Alembic** should be configured for database migrations. This will involve creating an `alembic.ini` file and an `alembic/` directory within `apps/backend/app/db`.
- The initial migration script should create two tables:
    - `tenants`: with columns like `id`, `name`, `created_at`.
    - `users`: with columns like `id`, `tenant_id` (foreign key to `tenants`), `username`, `hashed_password`, `email`, `roles`, `created_at`.
- The FastAPI application's database connection logic should be placed in `apps/backend/app/db/session.py` or a similar file, following the structure in `source-tree.md`.
- The application should read the `DATABASE_URL` from environment variables.

### Testing
- An integration test is required to verify that the FastAPI application can successfully connect to the PostgreSQL database on startup.
- This test should be part of the backend's test suite and use **Pytest**.
- The test should attempt to establish a database session and perform a simple query (e.g., `SELECT 1`) to confirm the connection is live.
- No unit tests are required for the Alembic migration scripts themselves, but the CI pipeline should be updated to run the migrations against a test database to ensure they are valid.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-19 | 1.1 | Enriched with technical details and tasks. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 1. | Sarah (PO) |

## Dev Agent Record
*This section is for the development agent.*

## QA Results
*This section is for the QA agent.*
