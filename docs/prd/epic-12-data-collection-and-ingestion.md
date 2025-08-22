### **Epic: Data Collection and Ingestion Pipeline (v2)**

**Epic Goal:** To design, build, and deploy a scalable, multi-tenant data ingestion pipeline capable of receiving, processing, and storing logs, metrics, and traces from external customer environments, ensuring data is securely isolated and available for querying within the Obstack platform **via both Loki and OpenSearch**.

**Epic Description:**

*   **Existing System Context:** The Obstack platform currently has a frontend and backend shell, with foundational services like PostgreSQL and authentication in place. However, it lacks the core data pipeline required to ingest telemetry from users. The architecture specifies a decoupled pipeline using Vector, OTEL Collector, Redpanda, and a FastAPI consumer.

*   **Enhancement Details:** This epic will implement the end-to-end data flow for telemetry data. This includes:
    1.  Creating a secure, tenant-aware public endpoint (using Kong) to receive OTLP and Prometheus `remote_write` data.
    2.  Implementing authentication and enrichment logic in the FastAPI backend to validate incoming data and tag it with the correct `tenant_id`.
    3.  Deploying and configuring Redpanda as a durable streaming buffer for all incoming telemetry.
    4.  Building a FastAPI consumer service to read from Redpanda, process the data, and **dual-write logs to both Loki (for recent, label-based queries) and OpenSearch (for indexed, full-text search)**.
    5.  Ensuring the entire pipeline adheres to the NFRs for ingestion lag (`NFR-P4`), security (`NFR-S4`), and reliability.

*   **Success Criteria:**
    *   The platform can successfully receive OTLP data from an external source.
    *   The platform can successfully receive Prometheus `remote_write` data.
    *   All ingested data is correctly tagged with a `tenant_id` and stored in the appropriate backend.
    *   A user can log in and query the data they have sent.
    *   **Logs are successfully indexed in tenant-specific OpenSearch indices.**
    *   The pipeline can handle a baseline load with minimal latency, as defined in the NFRs.

#### **Stories:**

1.  **Story: Provision Core Ingestion Infrastructure (Kong, Redpanda, OpenSearch)**
    *   Configure the API Gateway (Kong) with the necessary routes for the public ingestion endpoints.
    *   Deploy and configure a Redpanda cluster within the Docker environment.
    *   **Deploy and configure an OpenSearch service.**

2.  **Story: Implement Public Ingestion Endpoint & Authentication**
    *   Create the public-facing API endpoints in the FastAPI backend.
    *   Implement the token-based authentication and `tenant_id` enrichment logic.

3.  **Story: Develop Redpanda Consumer & Data Forwarding Service**
    *   Build the FastAPI consumer service that reads from Redpanda topics.
    *   Implement the logic to parse the data and forward it to Loki, Prometheus, and Tempo.
    *   **Enhance the consumer to also index all log data into tenant-specific indices in OpenSearch.**

4.  **Story: End-to-End Integration and Validation**
    *   Configure a test client (e.g., an OTEL Collector) to send data to the new endpoint.
    *   Write an E2E test to verify that data sent to the endpoint is correctly stored and can be queried by a user from the correct tenant.
    *   **Add a test case to verify that logs are searchable via OpenSearch.**

#### **Compatibility Requirements:**

*   The new ingestion endpoint must not interfere with the existing internal APIs.
*   The data formats must be compatible with the existing Loki, Prometheus, and Tempo services.

#### **Risk Mitigation:**

*   **Primary Risk:** Performance bottlenecks in the pipeline under load, especially with dual-writing to Loki and OpenSearch.
*   **Mitigation:** Redpanda is designed to handle backpressure. We will implement robust monitoring on the consumer service to track lag and processing times. Load testing will be a critical part of Story 4.
*   **Rollback Plan:** The entire ingestion pipeline can be disabled via feature flags and Kong configuration without impacting the core application UI. The OpenSearch write path can be disabled separately if needed.
