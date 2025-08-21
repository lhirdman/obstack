# Epic 11: Community Installer

**Epic Goal:** To provide a simple, "one-click" Docker-based installer for the free, open-source community tier of ObservaStack, enabling users to easily deploy and run the entire platform on their own infrastructure.

## Stories for Epic 11

### Story 11.1: `[Community]` Create "One-Click" Docker Installer
*   **As a** new user of the open-source Community edition,
*   **I want** a single command to download, configure, and run the entire ObservaStack platform,
*   **so that** I can get started with the platform quickly and easily without complex setup.
*   **Acceptance Criteria:**
    1.  A new `installer/` directory is created in the root of the monorepo.
    2.  The `installer/` directory contains a `docker-compose.yml` file that defines all the services required to run the Community edition of ObservaStack (e.g., frontend, backend, postgres, grafana, prometheus, loki, tempo).
    3.  A `install.sh` script is created in the `installer/` directory that:
        *   Checks for Docker and Docker Compose prerequisites.
        *   Pulls the latest Docker images for all services.
        *   Initializes any necessary configurations.
        *   Starts all services using `docker-compose up -d`.
    4.  A `README.md` file is included in the `installer/` directory with clear, simple instructions on how to use the `install.sh` script.
