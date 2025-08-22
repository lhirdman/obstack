---
Epic: 12
Story: 3
Title: Develop Redpanda Consumer & Data Forwarding Service
Status: Draft
---

# Story 12.3: `[Community]` Develop Redpanda Consumer & Data Forwarding Service

**As a** Backend Developer,
**I want** to create a consumer service that processes data from Redpanda and forwards it to the correct backend storage,
**so that** ingested data becomes available for querying.

## Acceptance Criteria

1.  A new FastAPI service is created that subscribes to the telemetry topics in Redpanda.
2.  The service correctly parses incoming data (OTLP and Prometheus formats).
3.  Metrics are forwarded to Prometheus.
4.  Traces are forwarded to Tempo.
5.  Logs are dual-written to both Loki and OpenSearch into tenant-specific indices.

## Dev Notes

### Previous Story Insights
-   This story consumes the data produced by **Story 12.2**. It assumes that enriched, tenant-aware telemetry data is available on a Redpanda topic (e.g., `telemetry-raw`).
-   It relies on the infrastructure provisioned in **Story 12.1** (Redpanda, OpenSearch, etc.).

### System Architecture
-   This is the final processing step in the **Log Ingestion Pipeline** and **Push-Based Telemetry Ingestion** flow.
-   The consumer service acts as the bridge between the streaming platform (Redpanda) and the long-term storage backends.
-   The dual-writing of logs to Loki and OpenSearch is a key architectural requirement for supporting different query patterns.
-   [Source: docs/architecture/high-level-architecture.md]

### File Locations
-   The consumer logic should be implemented as a new service in `apps/backend/app/services/consumer_service.py`.
-   This service will likely run as a background task or a separate process managed by the main application.
-   [Source: docs/architecture/source-tree.md]
-   [Source: docs/architecture/backend-architecture.md]

### External APIs
-   This service will interact with the internal APIs of several backend systems:
    -   **Prometheus**: For writing metrics.
    -   **Tempo**: For writing traces.
    -   **Loki**: For writing logs.
    -   **OpenSearch**: For indexing logs. The service must create tenant-specific indices (e.g., `logs-tenant-<tenant_id>`).
-   [Source: docs/architecture/external-apis.md]

### Data Models
-   The service needs to be able to deserialize the data format used in Redpanda. This format should be standardized from the producer in Story 12.2.
-   The service will then need to transform this data into the specific formats required by each destination service.

### Testing Requirements
-   **Unit Tests**: The parsing and transformation logic for each data type (logs, metrics, traces) must be thoroughly unit tested.
-   **Integration Tests**: An integration test should be created that:
    1.  Publishes a sample message to a test Redpanda topic.
    2.  Runs the consumer service.
    3.  Verifies that the data is correctly written to mock instances of Prometheus, Tempo, Loki, and OpenSearch.
-   [Source: docs/architecture/testing-strategy.md]

## Tasks / Subtasks

1.  **(AC: 1)** **Implement Redpanda Consumer**
    *   Add the necessary client library to consume from Redpanda topics.
    *   Create the `consumer_service.py` and implement the core logic to subscribe to the `telemetry-raw` topic.
    *   Integrate the consumer to run as a background task within the FastAPI application lifecycle.

2.  **(AC: 2)** **Implement Data Parsing and Routing**
    *   Develop logic to identify the data type (log, metric, trace) of each message from Redpanda.
    *   Implement parsers for the OTLP and Prometheus `remote_write` formats.
    *   Create a router or dispatcher that sends the parsed data to the appropriate forwarding function.

3.  **(AC: 3)** **Implement Metric Forwarding**
    *   Create a function that takes parsed metric data and writes it to Prometheus.

4.  **(AC: 4)** **Implement Trace Forwarding**
    *   Create a function that takes parsed trace data and writes it to Tempo.

5.  **(AC: 5)** **Implement Log Forwarding (Dual-Write)**
    *   Create a function that takes parsed log data.
    *   This function will first write the log data to Loki.
    *   It will then index the same log data in a tenant-specific index in OpenSearch. Implement logic to create the index if it doesn't exist.

6.  **Testing**
    *   Write unit tests for the data parsers and transformation logic.
    *   Write an integration test for the `consumer_service` that validates the end-to-end flow for each data type.
