# Epic 6: Alert Ingestion & Management

**Epic Goal:** To provide a centralized system for receiving, viewing, and managing the lifecycle of alerts from various sources. This epic enables users to proactively respond to issues in their monitored systems.

## Stories for Epic 6

### Story 6.1: `[Community]` Backend Alert Ingestion
*   **As a** Backend Developer,
*   **I want** to create a webhook endpoint that can receive alerts from Prometheus Alertmanager,
*   **so that** we can ingest alerts into the Obstack platform.
*   **Acceptance Criteria:**
    1.  A new API endpoint is created (e.g., `/api/v1/alerts/webhook/alertmanager`) that accepts POST requests with the Alertmanager webhook format.
    2.  The backend service parses the incoming alert data and stores it in a structured format in the PostgreSQL `alerts` table.
    3.  All incoming alerts are automatically tagged with the correct `tenant_id` based on a unique identifier in the webhook URL or payload.
    4.  The endpoint handles alert grouping and deduplication.
    5.  The webhook is documented in the API reference (Redocly) and the Docusaurus developer guide.

### Story 6.2: `[Community]` Alert Management API
*   **As a** Backend Developer,
*   **I want** to provide API endpoints for viewing and managing alerts,
*   **so that** the frontend can display and interact with alert data.
*   **Acceptance Criteria:**
    1.  A GET endpoint (`/api/v1/alerts`) is created to list all active alerts for a user's tenant, with support for filtering and sorting.
    2.  A POST endpoint (e.g., `/api/v1/alerts/{alert_id}/status`) is created to allow users to change the status of an alert (e.g., to "Acknowledged" or "Resolved").
    3.  The API enforces that users can only view or modify alerts belonging to their tenant.
    4.  The endpoints are protected and require a valid JWT.
    5.  All endpoints are documented in Redocly.

### Story 6.3: `[Community]` Frontend UI for Alert Management
*   **As a** site reliability engineer,
*   **I want** to view and manage all of my alerts in a centralized dashboard,
*   **so that** I can track and respond to incidents efficiently.
*   **Acceptance Criteria:**
    1.  A new "Alerts" view is created in the frontend application.
    2.  The UI displays a list of all active alerts, showing severity, source, title, and timestamp.
    3.  The UI allows users to filter alerts by status, severity, or other labels.
    4.  Users can click on an alert to see a detailed view with all its metadata.
    5.  From the detail view, users with appropriate permissions can change the alert's status (e.g., Acknowledge, Resolve).
    6.  The Alerts view is documented in the Docusaurus user guide.

### Story 6.4: `[SaaS]` Advanced Alert Notifications
*   **As a** Pro plan customer,
*   **I want** to configure Obstack to send alert notifications to external systems like Slack or PagerDuty,
*   **so that** my team can be notified of issues through our existing on-call workflows.
*   **Acceptance Criteria:**
    1.  The Admin view is updated to include a "Notification Channels" configuration page.
    2.  The backend provides a service to securely store and manage webhook URLs and API keys for external services.
    3.  When a new, high-severity alert is ingested, the backend triggers a notification to all configured channels for that tenant.
    4.  This feature is protected by a `[SaaS]` feature flag.
    5.  The setup process is documented in the Docusaurus user guide.
