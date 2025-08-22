# Development Environment & Workflow

This document provides a comprehensive guide to setting up and working with the Obstack monorepo for local development.

## 1. Prerequisites

Before you begin, you must have the following tools installed on your local machine:

-   **Node.js**: Version 20.x or higher
-   **pnpm**: As the primary package manager for the monorepo.
-   **Python**: Version 3.12 or higher
-   **Poetry**: For managing Python dependencies.
-   **Docker** & **Docker Compose**: To run the backend services (PostgreSQL, Redis, etc.).
-   **Nx CLI**: The monorepo management tool. Install it globally:
    ```bash
    npm install -g nx
    ```

## 2. Initial Project Setup

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/your-org/obstack.git
    cd obstack
    ```

2.  **Install Dependencies**:
    -   **Frontend**: Run `pnpm install` in the root of the repository. This will install all Node.js dependencies for all projects.
    -   **Backend**: Navigate to `apps/backend` and run `poetry install` to create a virtual environment and install all Python dependencies.

3.  **Environment Variables**:
    -   Create a `.env` file in the root of the repository by copying the `.env.example` file.
    -   Populate the `.env` file with the necessary secrets and configuration for local development (e.g., database connection strings, API keys).

4.  **Start Backend Services**:
    -   From the root of the repository, run the following command to start all the necessary infrastructure services (PostgreSQL, Redis, Keycloak, etc.):
        ```bash
        docker-compose up -d
        ```

## 3. Common Development Commands

All commands should be run from the root of the monorepo using the Nx CLI.

-   **Run Frontend Dev Server**:
    ```bash
    nx serve frontend
    ```
    This will start the React application on `http://localhost:3000`.

-   **Run Backend Dev Server**:
    ```bash
    nx serve backend
    ```
    This will start the FastAPI application on `http://localhost:8000` with auto-reloading.

-   **Run All Tests**:
    ```bash
    nx run-many --target=test
    ```

-   **Run Tests for a Specific App**:
    ```bash
    # Frontend tests
    nx test frontend

    # Backend tests
    nx test backend
    ```

## 4. Source Control & Workflow

-   **Branching**: All new work should be done on a feature branch, named descriptively (e.g., `feat/add-login-page`, `fix/user-auth-bug`).
-   **Commits**: Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for all commit messages. This is enforced by a pre-commit hook.
-   **Pull Requests**: All work must be submitted as a Pull Request to the `main` branch. PRs must pass all CI checks (linting, testing, type-checking) before they can be merged.
