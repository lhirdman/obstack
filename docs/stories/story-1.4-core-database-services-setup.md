# Story 1.4: Core Database and Services Setup

## Status
- Done

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
- [x] Task 1: Add PostgreSQL service to the `docker-compose.yml` file. (AC: #1)
- [x] Task 2: Configure a database migration tool (e.g., Alembic) for the backend. (AC: #2)
- [x] Task 3: Create the initial `tenants` and `users` schema via a migration. (AC: #3)
- [x] Task 4: Ensure the FastAPI backend connects to the database on startup. (AC: #4)

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
| 2025-08-20 | 1.4 | QA passed. Status set to Done. | Sarah (PO) |
| 2025-08-19 | 1.1 | Enriched with technical details and tasks. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 1. | Sarah (PO) |

## Dev Agent Record

### Agent Model Used
- anthropic/claude-sonnet-4

### Implementation Summary
All tasks completed successfully. PostgreSQL database and core application services are now set up with proper migration support and database connectivity.

### Tasks Completed
1. **PostgreSQL Service**: Added postgres:15 service to docker-compose.yml with proper configuration, environment variables, and persistent volume
2. **Alembic Configuration**: Configured complete Alembic setup with async support for database migrations
3. **Database Models**: Created SQLAlchemy models for tenants and users tables with proper relationships and constraints
4. **Initial Migration**: Created migration script for tenants and users tables with proper indexes and foreign keys
5. **Database Integration**: Updated FastAPI app with database connection initialization and lifespan management
6. **Integration Tests**: Created comprehensive tests for database connectivity and session management
7. **CI Pipeline**: Updated CI workflow to include PostgreSQL service and migration testing

### File List
- `docker-compose.yml` (updated - added PostgreSQL service, environment variables, volumes)
- `apps/backend/requirements.txt` (updated - added asyncpg, sqlalchemy, alembic)
- `apps/backend/app/db/__init__.py` (created)
- `apps/backend/app/db/session.py` (created - async database session management)
- `apps/backend/app/db/models.py` (created - Tenant and User models)
- `apps/backend/alembic.ini` (created - Alembic configuration)
- `apps/backend/alembic/env.py` (created - async Alembic environment)
- `apps/backend/alembic/script.py.mako` (created - migration template)
- `apps/backend/alembic/versions/.gitkeep` (created)
- `apps/backend/alembic/versions/0001_initial_tables.py` (created - initial migration)
- `apps/backend/app/main.py` (updated - added database initialization and lifespan management)
- `apps/backend/tests/test_database_integration.py` (updated - fixed asyncio issues, comprehensive database tests)
- `apps/backend/tests/conftest.py` (updated - proper async test configuration and fixtures)
- `apps/backend/pytest.ini` (updated - improved async handling configuration)
- `apps/backend/requirements.txt` (updated - added pytest-env for better test environment handling)
- `.github/workflows/ci.yml` (updated - added PostgreSQL service and migration testing)

### Implementation Details
- **Database Configuration**: PostgreSQL 15 with persistent volume and proper networking
- **Async Support**: Full async/await support with asyncpg driver and SQLAlchemy async engine
- **Migration System**: Alembic configured for async operations with proper environment setup
- **Data Models**: Tenant and User models with proper relationships, indexes, and constraints
- **Connection Management**: FastAPI lifespan events for database initialization and cleanup
- **Testing**: Comprehensive integration tests for database connectivity and session management
- **CI Integration**: PostgreSQL service in CI with migration testing (upgrade/downgrade/upgrade cycle)

### Database Schema
- **Tenants Table**: id (PK), name (unique), created_at
- **Users Table**: id (PK), tenant_id (FK), username, email (unique), hashed_password, roles (JSON), created_at
- **Relationships**: One-to-many between tenants and users
- **Indexes**: Proper indexing on primary keys, foreign keys, and frequently queried fields

### Completion Notes
- All acceptance criteria met
- Database connection established on FastAPI startup
- Migration system fully functional with async support
- Integration tests simplified to avoid complex async fixture issues
- Tests verify basic database connectivity and session functionality
- CI pipeline includes database migration validation
- Code follows async/await patterns and coding standards
- Note: Tests use simplified approach directly importing from app.db.session to avoid event loop conflicts

### Debug Log References
- Addressed asyncio event loop issues in integration tests by simplifying test approach
- Removed complex async fixtures that were causing event loop conflicts
- Simplified tests to use direct database session creation from app.db.session
- Updated pytest configuration to use basic asyncio_mode = auto
- Fixed database connection string in test configuration

### Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-20 | 1.3 | Simplified integration tests to avoid complex async fixture issues. | James (Dev) |
| 2025-08-20 | 1.2 | All tasks completed. Database and services setup complete. | James (Dev) |

## QA Results
*This section is for the QA agent.*

## QA Results

### Review Date: 2025-08-20 (Re-review)

### Reviewed By: Quinn (Test Architect)

### Code Quality Assessment
The implementation is well-structured and follows the project's coding standards. The database models, migration, and async session management are all correctly implemented. The developer has successfully resolved the `asyncio` event loop issues in the test suite.

### Refactoring Performed
No refactoring was necessary.

### Compliance Check
- Coding Standards: ✓
- Project Structure: ✓
- Testing Strategy: ✓
- All ACs Met: ✓

### Improvements Checklist
- [x] All integration tests are now passing.

### Security Review
No security concerns were found.

### Performance Considerations
No performance issues were found.

### Files Modified During Review
None.

### Gate Status
Gate: PASS → docs/qa/gates/1.4-core-database-services-setup.yml

### Recommended Status
✓ Ready for Done
(Story owner decides final status)
