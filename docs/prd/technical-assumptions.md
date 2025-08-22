# Technical Assumptions

## Repository Structure

The project will be developed in two separate repositories to support the Open Core model:
1.  **`obstack/platform` (Monorepo):** This open-source repository will contain the core product, including the `frontend`, `backend`, `ansible`, and `docs` packages. It is designed for tight integration between the full-stack components.
2.  **`obstack/control-plane` (Separate Repo):** This proprietary repository will contain the commercial business logic, including the landing page, user sign-up, subscription management, billing integration, and the administrative dashboard for managing SaaS/Enterprise customer instances.

This PRD pertains exclusively to the `obstack/platform` repository.

## Service Architecture

The platform will be built using a **Backend-for-Frontend (BFF)** architecture. A central FastAPI backend will serve as an orchestration and security layer, providing a unified API for the frontend while communicating with the various underlying open-source observability services (Prometheus, Loki, Tempo, OpenCost, etc.).

A **PostgreSQL** database will be included in the architecture to store data for both the open-source and commercial tiers, including local user accounts, tenant-specific settings, and future SaaS-related data like support tickets.

## Pluggable Authentication

The authentication system will be designed to be pluggable to support the tiered business model.
*   **Community Tier:** Will use a built-in **Local Authentication** provider that stores user credentials securely in the PostgreSQL database.
*   **SaaS/Enterprise Tiers:** Will use a **Keycloak Authentication** provider, enabling SSO/OIDC and SAML/LDAP integrations.

The selection of the authentication provider will be managed via configuration (e.g., environment variables).

## Feature Flagging System

To manage the feature differences between the Community, SaaS, and Enterprise tiers within a single codebase, a **feature flagging / entitlement system** will be implemented. The backend will check a user's subscription tier (stored in the PostgreSQL database) and dynamically enable or disable features via a set of flags that are passed to both the backend and frontend.

## Known Risks & Complexities

*   **Unified Search Performance:** The unified search service (Epic 5) is a potential performance bottleneck, as it needs to query multiple data sources in parallel and aggregate the results. This requires careful architectural design to ensure low latency.
*   **Data Correlation Logic:** The logic for seamlessly correlating signals (e.g., finding the exact logs for a specific trace) can be complex. This feature is high-value but also high-risk in terms of implementation.
*   **Test Data Realism:** The success of the parallel Test Stack (Epics 9 & 10) depends heavily on the ability of the Synthetic Data Generator to produce realistic, multi-tenant workloads.

## Stakeholders & Communication

*   **Primary Stakeholder:** The user (`lohi`).
*   **Core Team:** The BMad AI Agent team (`pm`, `architect`, `sm`, `dev`, etc.).
*   **Communication:** As the team is small and co-located in this environment, formal communication plans are not required. All project artifacts, including this PRD and the subsequent architecture documents, will serve as the primary source of truth.

## Testing Requirements

The platform's quality and reliability will be ensured by a comprehensive, parallel **Test Stack**. This separate environment will mirror the production stack and will be capable of automated end-to-end testing, synthetic data generation, load testing, chaos engineering, and security scanning. The Test Stack is a core component of the project, ensuring production-readiness for all tiers.
