# Epic List

*   **Epic 1: Project Foundation & Documentation Infrastructure:** Establish the monorepo, CI/CD, PostgreSQL schema, and the full documentation infrastructure (Docusaurus for user guides, OpenAPI setup for APIs). **Deliverable:** A running application shell and a live documentation site, both deployed.
*   **Epic 2: Pluggable Authentication (Local & Enterprise):** Build the pluggable auth interface. Implement the default **Local Auth** provider and the **Keycloak (Enterprise)** provider.
*   **Epic 3: Core Service Integration - Metrics & Traces:** Integrate with Prometheus and Tempo. Build the UI for visualizing metrics and traces.
*   **Epic 4: Core Service Integration - Logging:** Integrate with Loki. Enhance the UI with log search and filtering.
*   **Epic 5: Unified Search & Cross-Signal Correlation:** Build the unified search bar and the backend logic to correlate data across signals.
*   **Epic 6: Alert Ingestion & Management:** Build the end-to-end alert management system.
*   **Epic 7: Cost Visibility & Insights (All Tiers):** Integrate OpenCost and build the UI for all tiered cost features (basic visibility, historical analysis, and chargeback).
*   **Epic 8: Advanced Enterprise Features:** Implement remaining enterprise-grade features like fine-grained RBAC and audit logging.
*   **Epic 9: The Test Stack - Core Infrastructure & E2E Testing:** Build the foundational test environment and the initial suite of end-to-end tests for the features built in Epics 2-5.
*   **Epic 10: The Test Stack - Advanced Testing (Load & Chaos):** Implement the load testing and chaos engineering capabilities.
*   **Epic 11: Community Installer & Self-Hosted Experience:** Streamline and simplify the self-hosting and installation process for the Community Edition to drive adoption.
*   **Epic 12: Data Collection and Ingestion Pipeline:** Build the scalable, multi-tenant data ingestion pipeline to receive, process, and store logs, metrics, and traces from external customer environments.
