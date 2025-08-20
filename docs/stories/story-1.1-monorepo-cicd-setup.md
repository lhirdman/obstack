# Story 1.1: Monorepo and CI/CD Setup

## Status
- Approved

## Story
- **As a** Developer,
- **I want** the `obstack/platform` monorepo to be initialized with frontend and backend apps,
- **so that** I have a structured foundation for building the platform.

## Acceptance Criteria
1.  The monorepo is created with an `apps/` directory containing `frontend` (Vite + React) and `backend` (FastAPI) packages.
2.  A basic CI pipeline (e.g., GitHub Actions) is set up that runs linting and placeholder tests for both apps on every push.
3.  A `docker-compose.yml` file is created that builds and runs the empty frontend and backend containers.
4.  The project includes a root `README.md` with basic setup instructions.

## Tasks / Subtasks
- [ ] Task 1: Initialize an Nx-managed monorepo. (AC: #1)
- [ ] Task 2: Create the `apps/frontend` application using Vite with the `react-ts` template. (AC: #1)
- [ ] Task 3: Create the `apps/backend` application with a basic FastAPI setup. (AC: #1)
- [ ] Task 4: Set up a GitHub Actions workflow in `.github/workflows/ci.yml`. (AC: #2)
- [ ] Task 5: Add linting steps to the CI workflow (ESLint for frontend, Ruff for backend). (AC: #2)
- [ ] Task 6: Add placeholder test execution steps to the CI workflow (Vitest for frontend, Pytest for backend). (AC: #2)
- [ ] Task 7: Create a `docker-compose.yml` file in the project root that builds and runs the frontend and backend services. (AC: #3)
- [ ] Task 8: Create a root `README.md` with instructions on how to set up the local environment and run the applications. (AC: #4)

## Dev Notes
- The monorepo should be managed by **Nx** as specified in the architecture.
- The frontend application must use **Vite (v7.0.0)** with **React (v19.1.0)** and **TypeScript (v5.9.2)**.
- The backend application must use **Python (v3.12+)** and **FastAPI (v0.115+)**.
- Refer to the `docs/architecture/source-tree.md` document for the required directory structure for both the frontend and backend applications.
- All code must adhere to the standards defined in `docs/architecture/coding-standards.md`.

### Testing
- Placeholder unit tests are required for this story.
- For the frontend, create a basic component test using **Vitest** and **React Testing Library**.
- For the backend, create a basic API endpoint test using **Pytest**.
- Refer to the `Testing` section in `coding-standards.md` for general testing principles.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-19 | 1.1 | Enriched with technical details and tasks. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 1. | Sarah (PO) |

## Dev Agent Record
*This section is for the development agent.*

## QA Results
*This section is for the QA agent.*
