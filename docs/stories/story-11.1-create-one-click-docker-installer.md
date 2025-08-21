---
Epic: 11
Story: 1
Title: Create "One-Click" Docker Installer
Status: Draft
---

# Story 11.1: `[Community]` Create "One-Click" Docker Installer

**As a** new user of the open-source Community edition,
**I want** a single command to download, configure, and run the entire ObservaStack platform,
**so that** I can get started with the platform quickly and easily without complex setup.

## Acceptance Criteria

1.  A new `installer/` directory is created in the root of the monorepo.
2.  The `installer/` directory contains a `docker-compose.yml` file that defines all the services required to run the Community edition of ObservaStack (e.g., frontend, backend, postgres, grafana, prometheus, loki, tempo).
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
-   [Source: docs/architecture/unified-project-structure.md]

### Technical Stack
-   The `docker-compose.yml` should be created using the services defined in the tech stack.
-   **Services to include**: frontend, backend, postgres, grafana, prometheus, loki, tempo, and any other services required for the community edition.
-   [Source: docs/architecture/tech-stack.md]

### Coding Standards
-   The `install.sh` script should be written in `bash` and follow general shell scripting best practices for readability and maintainability.
-   [Source: docs/architecture/coding-standards.md]

### Testing Requirements
-   The installer should be manually tested to ensure it works on a clean environment.
-   Consider adding a simple automated test that runs the `install.sh` script and checks if all containers are up and running.
-   [Source: docs/architecture/testing-strategy.md]

## Tasks / Subtasks

1.  **(AC: 1)** Create the `installer/` directory in the project root.
2.  **(AC: 2)** Create the `installer/docker-compose.yml` file.
    *   Define the `frontend` service.
    *   Define the `backend` service.
    *   Define the `postgres` service.
    *   Define the `grafana` service.
    *   Define the `prometheus` service.
    *   Define the `loki` service.
    *   Define the `tempo` service.
    *   Ensure all services are configured to work together with appropriate networking and volumes.
3.  **(AC: 3)** Create the `installer/install.sh` script.
    *   Implement a check for Docker and Docker Compose.
    *   Implement the logic to pull the latest images.
    *   Implement the logic to start the services.
4.  **(AC: 4)** Create the `installer/README.md` file.
    *   Add instructions on how to run the `install.sh` script.
    *   Add a section on prerequisites.
    *   Add a section on how to access the application after installation.
5.  **Testing**
    *   Manually test the `install.sh` script on a clean environment.
    *   (Optional) Create an automated test for the installer.
