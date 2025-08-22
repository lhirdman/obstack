---
Epic: 12
Story: 1
Title: Provision Core Ingestion Infrastructure (Kong, Redpanda, OpenSearch)
Status: Approved
---

# Story 12.1: `[Community]` Provision Core Ingestion Infrastructure (Kong, Redpanda, OpenSearch)

**As a** Platform Engineer,
**I want** the core infrastructure for the ingestion pipeline to be defined and deployable,
**so that** we have a stable foundation for building the data flow.

## Acceptance Criteria

1.  Kong is configured with the necessary routes for the public OTLP and Prometheus `remote_write` endpoints.
2.  A Redpanda cluster is added to the Docker Compose setup.
3.  An OpenSearch service is added to the Docker Compose setup.
4.  All new services are integrated into the project's startup and shutdown scripts and are deployable via a single command.

## Dev Notes

### Previous Story Insights
-   No previous story in this epic. This is the foundational infrastructure story.

### System Architecture
-   This story involves adding three key infrastructure components to the existing Docker Compose setup: Kong, Redpanda, and OpenSearch.
-   These services will form the backbone of the new data ingestion pipeline.
-   **Kong** will act as the API Gateway, managing all incoming traffic.
-   **Redpanda** will serve as the streaming data platform (Kafka-compatible) to buffer incoming telemetry.
-   **OpenSearch** will be used for advanced, full-text search on log data.
-   [Source: docs/architecture/tech-stack.md]
-   [Source: docs/architecture/high-level-architecture.md]

### File Locations
-   The primary file to be modified is the main `docker-compose.yml` in the project root.
-   New configuration files for Kong should be placed in a new `docker/kong/` directory.
-   [Source: docs/architecture/source-tree.md]

### API Specifications
-   Kong needs to be configured to proxy two main public-facing routes (e.g., `/ingest/otlp/v1` and `/ingest/prometheus/v1/write`) to the backend BFF service.
-   The specific endpoint definitions in the backend will be handled in Story 12.2, but the gateway routes should be established here.
-   [Source: docs/architecture/rest-api-spec.md]

### Testing Requirements
-   After running `docker-compose up`, all new services (Kong, Redpanda, OpenSearch) should be running and healthy.
-   A simple health check test should be added to the CI pipeline to verify that the new services start correctly.
-   [Source: docs/architecture/testing-strategy.md]

## Tasks / Subtasks

1.  **(AC: 2)** **Integrate Redpanda Service**
    *   Add a `redpanda` service definition to the main `docker-compose.yml`.
    *   Configure necessary ports and volumes for data persistence.
    *   Ensure the backend service can connect to Redpanda.

2.  **(AC: 3)** **Integrate OpenSearch Service**
    *   Add an `opensearch` service definition to the `docker-compose.yml`.
    *   Configure necessary ports, volumes, and environment variables (e.g., for disabling security in development).
    *   Ensure the backend service can connect to OpenSearch.

3.  **(AC: 1)** **Integrate Kong API Gateway**
    *   Add a `kong` service definition to the `docker-compose.yml`.
    *   Create a `docker/kong/kong.yml` declarative configuration file.
    *   In `kong.yml`, define the backend BFF as an upstream service.
    *   Define the public routes for OTLP and Prometheus `remote_write` and configure them to proxy to the BFF service.

4.  **(AC: 4)** **Update Project Scripts**
    *   Ensure that running `docker-compose up` successfully starts all the new services.
    *   Update any relevant documentation (e.g., the root `README.md`) to reflect the new services.

5.  **Validation**
    *   Run `docker-compose ps` to verify all new containers are up and running.
    *   Access the Kong admin API to confirm the new routes are configured.
    *   Access the OpenSearch API to confirm the cluster is healthy.
