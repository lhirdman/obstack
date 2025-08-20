# Epic 4: Core Service Integration - Logging

**Epic Goal:** To integrate the platform with Loki, providing a powerful and intuitive interface for searching, filtering, and live-tailing log data. This epic completes the core triad of observability signals.

## Stories for Epic 4

### Story 4.1: `[Community]` Backend Integration with Loki
*   **As a** Backend Developer,
*   **I want** the backend to query a Loki instance using tenant-isolated LogQL queries,
*   **so that** we can securely serve log data to the frontend.
*   **Acceptance Criteria:**
    1.  The backend provides a service that can connect to and query the Loki API.
    2.  All LogQL queries sent from the backend are automatically injected with the `tenant_id` label to enforce data isolation.
    3.  A new API endpoint is created (e.g., `/api/v1/logs/query`) that proxies queries to Loki and returns the log streams.
    4.  The endpoint is protected and requires a valid JWT.
    5.  The new endpoint is documented in the API reference (Redocly).

### Story 4.2: `[Community]` Frontend UI for Log Search and Visualization
*   **As a** developer,
*   **I want** to search and filter logs using a powerful query interface,
*   **so that** I can quickly find the information I need to debug issues.
*   **Acceptance Criteria:**
    1.  A new "Logs" view is created in the frontend application.
    2.  The UI includes a LogQL input field and label/facet filters that send requests to the backend's log endpoint.
    3.  The UI displays log lines in a clear, readable format, with color-coding for different log levels.
    4.  The view includes the global time-range selector and supports "live-tailing" of logs.
    5.  The Logs view is documented in the Docusaurus user guide.

### Story 4.3: `[Community]` Log Line Interaction and Details
*   **As a** developer,
*   **I want** to expand log lines to see detailed metadata,
*   **so that** I can get the full context for a specific log event.
*   **Acceptance Criteria:**
    1.  Each log line in the UI is expandable.
    2.  When expanded, the UI displays all labels and parsed fields associated with the log line.
    3.  Users can easily add labels or fields from the detail view to the current query to refine their search.
    4.  The UI provides an easy way to copy the full log message and its metadata.
