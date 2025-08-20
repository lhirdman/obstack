# Epic 5: Unified Search & Cross-Signal Correlation

**Epic Goal:** To deliver a truly unified observability experience by implementing the unified search bar and the backend logic that enables seamless pivoting between logs, metrics, and traces. This epic transforms the platform from a collection of tools into a single, cohesive solution.

## Stories for Epic 5

### Story 5.1: `[Community]` Backend Unified Search Service
*   **As a** Backend Developer,
*   **I want** to create a unified search service that queries Loki, Prometheus, and Tempo simultaneously,
*   **so that** I can provide a single entry point for all user search queries.
*   **Acceptance Criteria:**
    1.  A new API endpoint is created (e.g., `/api/v1/search/unified`).
    2.  The endpoint accepts a free-text query and a time range.
    3.  The backend service dispatches parallel, tenant-aware queries to the Loki, Prometheus, and Tempo services.
    4.  The service aggregates the results from all three sources into a single, structured JSON response, clearly identifying the source of each result.
    5.  The new endpoint is fully documented in Redocly.

### Story 5.2: `[Community]` Frontend Unified Search Bar and Results UI
*   **As a** DevOps engineer,
*   **I want** to use a single search bar on the main dashboard to query all my observability data at once,
*   **so that** I can quickly find relevant information without knowing which tool to check first.
*   **Acceptance Criteria:**
    1.  A prominent, unified search bar is added to the main dashboard or navigation header.
    2.  When a user executes a search, the UI calls the new unified search endpoint.
    3.  A new "Search Results" view is created that can display a heterogeneous list of results (logs, metrics, traces).
    4.  Each result in the list is clearly marked with its type (e.g., with an icon and text) and links to the appropriate detailed view (e.g., the Logs view).
    5.  The feature is documented in the Docusaurus user guide.

### Story 5.3: `[Community]` Cross-Signal Correlation Logic
*   **As a** developer debugging an issue,
*   **I want** to be able to jump from a specific trace to the logs and metrics related to it,
*   **so that** I can correlate different signals to find the root cause of a problem faster.
*   **Acceptance Criteria:**
    1.  When viewing a trace in the "Traces" view, the UI displays a "View related logs" button if a `trace_id` is present in the span's metadata.
    2.  Clicking this button navigates the user to the "Logs" view with a pre-filled query (e.g., `{tenant_id="...", trace_id="..."}`).
    3.  Similarly, when viewing a log that contains a `trace_id`, the UI provides a direct link to view that trace in the "Traces" view.
    4.  Backend services are enhanced to efficiently query for related signals (e.g., an endpoint to find logs for a given trace ID).
    5.  This correlation workflow is documented with a guide in Docusaurus.
