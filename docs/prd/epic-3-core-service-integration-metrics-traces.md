# Epic 3: Core Service Integration - Metrics & Traces

**Epic Goal:** To integrate the platform with Prometheus and Tempo, enabling users to visualize metrics and distributed traces through the unified interface. This epic delivers the first two core observability signals.

## Stories for Epic 3

**Story 3.1: `[Community]` Backend Integration with Prometheus**
*   **As a** Backend Developer,
*   **I want** the backend to query a Prometheus/Thanos instance based on the user's tenant,
*   **so that** we can securely serve metrics data to the frontend.
*   **Acceptance Criteria:**
    1.  The backend provides a service that can connect to and query a Prometheus-compatible API.
    2.  All PromQL queries sent from the backend are automatically injected with the `tenant_id` label to enforce data isolation.
    3.  A new API endpoint is created (e.g., `/api/v1/metrics/query`) that proxies queries to Prometheus and returns the results.
    4.  The endpoint is protected and requires a valid JWT.
    5.  The new endpoint is documented in the API reference (Redocly).

**Story 3.2: `[Community]` Backend Integration with Tempo**
*   **As a** Backend Developer,
*   **I want** the backend to query a Tempo instance for trace data,
*   **so that** we can securely serve distributed traces to the frontend.
*   **Acceptance Criteria:**
    1.  The backend provides a service that can connect to and query the Tempo API.
    2.  All Tempo queries are secured by tenant context.
    3.  A new API endpoint is created (e.g., `/api/v1/traces/{trace_id}`) that retrieves a specific trace from Tempo.
    4.  The endpoint is protected and requires a valid JWT.
    5.  The new endpoint is documented in the API reference (Redocly).

**Story 3.3: `[Community]` Frontend UI for Metrics Visualization**
*   **As a** DevOps engineer,
*   **I want** to visualize metrics from my services in the Obstack UI,
*   **so that** I can monitor the health and performance of my applications.
*   **Acceptance Criteria:**
    1.  A new "Metrics" view is created in the frontend application.
    2.  The UI includes a query builder or raw PromQL input field that sends requests to the backend's metrics endpoint.
    3.  The UI uses a charting library (e.g., embedding Grafana panels or using a library like Apache ECharts) to render the time-series data returned by the API.
    4.  The view includes the global time-range selector.
    5.  A user guide for the Metrics view is added to the Docusaurus site.

**Story 3.4: `[Community]` Frontend UI for Trace Visualization**
*   **As a** developer,
*   **I want** to view distributed traces in a waterfall diagram,
*   **so that** I can debug performance issues and understand service dependencies.
*   **Acceptance Criteria:**
    1.  A new "Traces" view is created in the frontend.
    2.  The UI allows users to search for traces by ID or other tags.
    3.  When a trace is selected, the UI displays a detailed waterfall view of all spans.
    4.  Each span in the waterfall is clickable and shows detailed metadata (tags, logs, etc.).
    5.  The view is documented in the Docusaurus user guide.
