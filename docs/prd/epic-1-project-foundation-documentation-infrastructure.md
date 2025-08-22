# Epic 1: Project Foundation & Documentation Infrastructure

**Epic Goal:** To establish the complete project monorepo, a live documentation site, a basic CI/CD pipeline, and a running, deployable application shell. This epic delivers the foundational skeleton of the project upon which all future features will be built.

## Stories for Epic 1

**Story 1.1: `[Community]` Monorepo and CI/CD Setup**
*   **As a** Developer,
*   **I want** the `obstack/platform` monorepo to be initialized with frontend and backend apps,
*   **so that** I have a structured foundation for building the platform.
*   **Acceptance Criteria:**
    1.  The monorepo is created with an `apps/` directory containing `frontend` (Vite + React) and `backend` (FastAPI) packages.
    2.  A basic CI pipeline (e.g., GitHub Actions) is set up that runs linting and placeholder tests for both apps on every push.
    3.  A `docker-compose.yml` file is created that builds and runs the empty frontend and backend containers.
    4.  The project includes a root `README.md` with basic setup instructions.

**Story 1.2: `[Community]` Documentation Site Setup**
*   **As a** Developer,
*   **I want** a Docusaurus site to be initialized and deployed,
*   **so that** we have a live platform for project documentation from day one.
*   **Acceptance Criteria:**
    1.  A Docusaurus instance is set up in a `docs/` package within the monorepo.
    2.  The site is configured with a basic structure (User Guide, API Reference, Architecture).
    3.  A CI/CD workflow is created to automatically deploy the Docusaurus site (e.g., to GitHub Pages or Vercel) on every merge to `main`.
    4.  The live documentation site includes a placeholder "Architecture Overview" page.

**Story 1.3: `[Community]` API Documentation Setup**
*   **As a** Developer,
*   **I want** the FastAPI backend to be configured to serve auto-generated OpenAPI documentation using Redocly,
*   **so that** our API documentation is always in sync with the code.
*   **Acceptance Criteria:**
    1.  The FastAPI application is configured to generate an OpenAPI spec from the code.
    2.  The application serves a visually appealing and user-friendly API doc using Redocly at the `/api/docs` endpoint.
    3.  A basic "health check" endpoint (`/api/v1/health`) is created and appears in the Redocly documentation.

**Story 1.4: `[Community]` Core Database and Services Setup**
*   **As a** Backend Developer,
*   **I want** the PostgreSQL database and core application services to be set up,
*   **so that** we have a foundation for storing data and implementing business logic.
*   **Acceptance Criteria:**
    1.  A PostgreSQL service is added to the `docker-compose.yml` file.
    2.  A database migration tool (e.g., Alembic) is configured for the backend.
    3.  The initial database schema for the `tenants` and `users` tables (for Local Auth) is created via a migration.
    4.  The FastAPI backend successfully connects to the PostgreSQL database on startup.
