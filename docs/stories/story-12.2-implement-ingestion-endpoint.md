---
Epic: 12
Story: 2
Title: Implement Public Ingestion Endpoint & Authentication
Status: Approved
---

# Story 12.2: `[SaaS]` Implement Public Ingestion Endpoint & Authentication

**As a** Backend Developer,
**I want** to implement the secure, public-facing API endpoint for data ingestion,
**so that** customers can begin sending their telemetry data to the platform.

## Acceptance Criteria

1.  A new FastAPI endpoint is created to handle incoming OTLP and Prometheus `remote_write` requests.
2.  The endpoint validates a tenant-specific, token-based authentication header.
3.  Upon successful authentication, the endpoint enriches the incoming data with a `tenant_id` label/attribute.
4.  The enriched data is published to the appropriate topic in Redpanda.
5.  Unauthenticated requests are rejected with a `401 Unauthorized` error.

## Dev Notes

### Previous Story Insights
-   This story builds directly on **Story 12.1**, which provisions the necessary infrastructure (Kong, Redpanda). It assumes that Kong is configured to route traffic to the backend service.

### System Architecture
-   This story implements a critical component of the **Push-Based Telemetry Ingestion** flow.
-   The backend BFF is responsible for the authentication and enrichment steps.
-   The endpoint will receive data from the Kong API Gateway.
-   [Source: docs/architecture/high-level-architecture.md#push-based-telemetry-ingestion]

### File Locations
-   The new API endpoint should be created in `apps/backend/app/api/v1/endpoints/ingest.py`.
-   The business logic should be handled by a new service in `apps/backend/app/services/ingestion_service.py`.
-   [Source: docs/architecture/source-tree.md]
-   [Source: docs/architecture/backend-architecture.md]

### API Specifications
-   The new endpoint should be defined under a path like `/ingest`. The full path will be determined by the Kong configuration (e.g., `/ingest/otlp/v1`).
-   The endpoint must handle POST requests.
-   Authentication will be handled via a custom header (e.g., `X-Obstack-Auth-Token`). The token will be a unique, per-tenant secret.
-   The response for a successful ingestion should be `202 Accepted`.
-   The response for an authentication failure must be `401 Unauthorized`.
-   [Source: docs/architecture/rest-api-spec.md]

### Data Models
-   The endpoint will need to handle raw OTLP (protobuf) and Prometheus `remote_write` (protobuf) data formats. Pydantic models will not be used for the raw request body, but the authenticated and enriched data sent to Redpanda should have a defined structure.

### Testing Requirements
-   **Unit Tests**: The `ingestion_service.py` logic for token validation, data enrichment, and publishing to Redpanda must be unit tested with mocked dependencies.
-   **Integration Tests**: An integration test should be created to test the API endpoint. It will send a sample payload, use a test database to validate the tenant token, and check that the data is correctly published to a test Redpanda instance.
-   [Source: docs/architecture/testing-strategy.md]

## Tasks / Subtasks

1.  **(AC: 1)** **Create Ingestion Endpoint**
    *   Create the new `ingest.py` file in the `apps/backend/app/api/v1/endpoints/` directory.
    *   Define the FastAPI router and the main POST endpoint.

2.  **(AC: 2, 3)** **Implement Authentication and Enrichment Service**
    *   Create the `ingestion_service.py` file.
    *   Implement a function to validate the `X-Obstack-Auth-Token` against a stored value (initially, this can be a simple lookup; it will be integrated with the `tenants` table later).
    *   Implement a function that takes the raw data and the tenant ID and adds the `tenant_id` to the data.
    *   Implement the dependency injection to provide this service to the endpoint.

3.  **(AC: 4)** **Implement Redpanda Producer**
    *   Add the necessary client library to connect to Redpanda.
    *   In the `ingestion_service.py`, implement the logic to publish the enriched data to a Redpanda topic (e.g., `telemetry-raw`).

4.  **(AC: 5)** **Error Handling**
    *   Ensure the endpoint returns a `401 Unauthorized` HTTP exception for invalid or missing tokens.
    *   Implement appropriate error handling for the Redpanda publishing step.

5.  **Testing**
    *   Write unit tests for the `ingestion_service.py` functions.
    *   Write an integration test for the `/ingest` endpoint that covers both successful and failed authentication scenarios.
