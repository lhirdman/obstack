---
Epic: 11
Story: 1
Title: Create "One-Click" Docker Installer
Status: Approved
---

# Story 11.1: `[Community]` Create "One-Click" Docker Installer

**As a** new user of the open-source Community edition,
**I want** a single command to download, configure, and run the entire ObservaStack platform,
**so that** I can get started with the platform quickly and easily without complex setup.

## Acceptance Criteria

1.  A new `installer/` directory is created in the root of the monorepo.
2.  The `installer/` directory contains a `docker-compose.yml` file that defines all the services required to run the Community edition of ObservaStack.
3.  A `install.sh` script is created in the `installer/` directory that:
    *   Checks for Docker and Docker Compose prerequisites.
    *   Pulls the latest Docker images for all services.
    *   Initializes any necessary configurations.
    *   Starts all services using `docker-compose up -d`.
4.  A `README.md` file is included in the `installer/` directory with clear, simple instructions on how to use the `install.sh` script.

## Dev Notes

### File Locations
-   New files and directories should be created according to the project structure.
-   **Installer Directory**: `/installer/`
-   **Docker Compose File**: `/installer/docker-compose.yml`
-   **Install Script**: `/installer/install.sh`
-   **README**: `/installer/README.md`
-   [Source: `docs/architecture/source-tree.md`]

### Technical Stack & Configuration
-   The `docker-compose.yml` should be a simplified version of the main `docker/docker-compose.yml`, focusing on the core services for the community edition.
-   **Services to include**: `frontend`, `backend`, `postgres`, `grafana`, `prometheus`, `loki`, `tempo`.
-   Use the existing `docker-compose.yml` files as a reference for service definitions, but adapt them for a local, single-machine setup.
-   **Frontend**: Expose port `3000`.
-   **Backend**: Expose port `8000`.
-   **Postgres**: Use the same image and environment variables as the root `docker-compose.yml`.
-   **Grafana**: Expose port `3000` (Note: this conflicts with the frontend, adjust to `3001` or similar). Use a simplified provisioning setup.
-   **Prometheus**: Expose port `9090`. Use a basic `prometheus.yml` configuration.
-   **Loki**: Expose port `3100`.
-   **Tempo**: Expose port `3200`.
-   [Source: `docs/architecture/tech-stack.md`, `/docker-compose.yml`, `/docker/docker-compose.yml`]

### Coding Standards
-   The `install.sh` script should be written in `bash` and follow general shell scripting best practices for readability and maintainability.
-   [Source: `docs/architecture/coding-standards.md`]

### Testing Requirements
-   **Manual Validation**:
    1.  Run the `install.sh` script on a clean environment (e.g., a fresh VM or a machine without the containers running).
    2.  Verify that all containers start successfully by running `docker ps`.
    3.  Access the frontend application at `http://localhost:3000` and ensure it loads.
    4.  Access Grafana at its exposed port and verify that you can log in.
    5.  Check the logs of each service to ensure there are no critical errors on startup.
-   **Automated Check**:
    -   The `install.sh` script should include a final step that polls the health of each service endpoint and reports success only when all services are healthy.

## Tasks / Subtasks

1.  **(AC: 1)** Create the `installer/` directory in the project root.
2.  **(AC: 2)** Create the `installer/docker-compose.yml` file with the following services:
    *   `frontend`: Based on the root `docker-compose.yml`.
    *   `backend`: Based on the root `docker-compose.yml`.
    *   `postgres`: Based on the root `docker-compose.yml`.
    *   `grafana`: Based on `docker/docker-compose.yml`, expose port `3001`.
    *   `prometheus`: Based on `docker/docker-compose.yml`.
    *   `loki`: Based on `docker/docker-compose.yml`.
    *   `tempo`: Based on `docker/docker-compose.yml`.
    *   Define a shared network for all services.
3.  **(AC: 3)** Create the `installer/install.sh` script.
    *   Implement a function to check for `docker` and `docker-compose` commands.
    *   Implement `docker-compose pull` to fetch images.
    *   Implement `docker-compose up -d` to start services.
    *   Add a health check loop that waits for services to be available.
4.  **(AC: 4)** Create the `installer/README.md` file.
    *   Add instructions on how to run the `install.sh` script.
    *   List prerequisites: `Docker` and `Docker Compose`.
    *   List the URLs for the frontend and Grafana.
5.  **Testing**
    *   Execute the manual validation steps outlined in "Testing Requirements".
