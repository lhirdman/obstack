# Epic 7: Cost Visibility & Insights (All Tiers)

**Epic Goal:** To integrate OpenCost into the platform, providing users with deep insights into their Kubernetes infrastructure costs. This epic will deliver features across all three tiers, from basic cost visibility for the Community to advanced chargeback reporting for the Enterprise.

## Stories for Epic 7

### Story 7.1: `[Community]` Backend Integration with OpenCost
*   **As a** Backend Developer,
*   **I want** the backend to query the OpenCost API for Kubernetes cost data,
*   **so that** we can expose cost allocation metrics to the frontend.
*   **Acceptance Criteria:**
    1.  A new backend service is created to communicate with the OpenCost API.
    2.  The service can query for cost data and aggregate it by namespace, workload, and other labels.
    3.  All queries to OpenCost are tenant-aware.
    4.  A new API endpoint is created (e.g., `/api/v1/costs/current`) to serve basic, current cost data.
    5.  The new endpoint is protected, tenant-isolated, and documented in Redocly.

### Story 7.2: `[Community]` Frontend UI for Basic Cost Visibility
*   **As a** platform operator,
*   **I want** to see a dashboard showing my current Kubernetes costs broken down by namespace,
*   **so that** I can understand where my cloud spend is going.
*   **Acceptance Criteria:**
    1.  A new "Cost Insights" view is created in the frontend.
    2.  The UI displays a dashboard with visualizations (e.g., pie charts, bar charts) of current cost data from the backend.
    3.  The dashboard provides a breakdown of costs by namespace and workload type.
    4.  The feature is available to all tiers.
    5.  The basic dashboard is documented in the Docusaurus user guide.

### Story 7.3: `[SaaS]` Historical Cost Analysis
*   **As a** Pro plan customer,
*   **I want** to view historical cost data and trends,
*   **so that** I can understand how my costs are changing over time.
*   **Acceptance Criteria:**
    1.  The backend is enhanced to query and store historical cost data from OpenCost into the PostgreSQL database.
    2.  A new API endpoint is created to serve historical cost data with selectable time ranges.
    3.  The "Cost Insights" UI is updated with a time-series chart showing cost trends.
    4.  The UI allows users to compare costs across different time periods.
    5.  This feature is protected by a `[SaaS]` feature flag.

### Story 7.4: `[Enterprise]` Advanced Cost Reporting and Anomaly Detection
*   **As an** Enterprise customer,
*   **I want** to generate chargeback/showback reports and be alerted to cost anomalies,
*   **so that** I can perform internal cost accounting and proactively manage unexpected spend.
*   **Acceptance Criteria:**
    1.  The backend includes a service that can generate detailed cost allocation reports suitable for chargeback.
    2.  A new API endpoint is created for generating and downloading these reports (e.g., as CSV).
    3.  The backend includes a scheduled job that analyzes cost data for significant, anomalous spikes.
    4.  When an anomaly is detected, a high-severity alert is created and sent to the Alert Management system.
    5.  The UI is updated to include a "Reporting" section and an "Anomalies" view.
    6.  This feature is protected by an `[Enterprise]` feature flag and documented in the Docusaurus site.
