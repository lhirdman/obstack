# Goals and Background Context

## Goals

*   **Unified Experience:** Provide a single, seamless web interface for logs, metrics, traces, alerts, and Kubernetes cost monitoring.
*   **Tiered Open-Core Model:** Deliver the platform via a clear, three-tiered strategy: a self-hostable, open-source **Community** tier; a managed, multi-tenant **SaaS** tier; and a fully isolated, single-tenant **Enterprise** tier.
*   **Value-Driven Monetization:** Reserve advanced, high-value features such as SSO/SAML authentication, detailed cost optimization reporting, and advanced security features for the paid SaaS and Enterprise tiers.
*   **Production-Grade Reliability:** Ensure the platform is highly reliable through a comprehensive, parallel test stack capable of sophisticated automated testing, including load, chaos, and security validation.
*   **Control Plane Driven Automation:** Manage all customer lifecycle operations (provisioning, billing, tier management) for the paid offerings through a dedicated, external **Control Plane**.
*   **Frictionless Community Adoption:** Provide a complete, self-hostable Community edition with local user authentication to foster open-source adoption and community contribution.

## Background Context

Modern software operations require a complex suite of observability tools, often forcing teams to juggle disconnected platforms and pay exorbitant licensing fees. Obstack addresses this by unifying best-in-class open-source tools into a single, cohesive platform.

The project follows an **Open Core** business model, supported by a hybrid technical architecture. The core product is an open-source, self-hostable **Community edition** offering powerful observability fundamentals. Monetization is achieved through two commercial tiers: a managed **SaaS tier** and a high-security **Enterprise tier**, both of which unlock advanced features. This tiered strategy is managed by a separate, proprietary **Control Plane** that handles all business logic, cleanly separating the commercial aspects from the open-source core product. This PRD defines the requirements for the core `obstack/platform` repository, which will contain the functionality for all three tiers, managed via a feature flagging system.

## Market Context & Competitive Landscape

The observability market is dominated by large, proprietary SaaS platforms (e.g., Datadog, New Relic) that offer powerful but expensive solutions. While the open-source world provides best-in-class tools (Prometheus, Grafana, Loki), integrating and managing them at scale is a significant engineering challenge.

Obstack's strategic opportunity is to bridge this gap, offering a "best of both worlds" solution: the power of the open-source stack in a unified, easy-to-use product. Our primary competitor in this space is Grafana Labs, which follows a similar open-core model. Our key differentiator will be a more seamless, out-of-the-box user experience with a stronger focus on cross-signal correlation and cost management.

## Success Metrics & KPIs

To ensure the project is aligned with its goals, the following Key Performance Indicators (KPIs) will be tracked.

| Tier | Metric | KPI Target (First 6 Months) | Rationale |
| :--- | :--- | :--- | :--- |
| **Community** | **Adoption Rate** | Achieve 100+ successful self-hosted deployments. | Measures the initial appeal and ease of use of the open-source product. |
| **Community** | **Weekly Active Users (WAU)** | Reach 250 WAUs. | Indicates that the product is not just being installed, but actively used and providing value. |
| **SaaS** | **Sign-up to Active Trial Rate** | 20% of new sign-ups actively ingest data for at least one week. | Measures the effectiveness of the onboarding process and the initial product experience. |
| **SaaS** | **Trial to Paid Conversion Rate** | 5% of active trials convert to a paid plan. | The ultimate measure of perceived value for the commercial offering. |
| **All Tiers** | **Core Feature Engagement** | 60% of WAUs use the Unified Search feature at least once per session. | Validates that the core value proposition of a unified experience is being realized by users. |

## Change Log

| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-19 | 1.4 | Added Market Context, User Journeys, and Scope Boundaries. | John (PM) |
| 2025-08-19 | 1.3 | Added measurable NFRs and Success Metrics to address checklist blockers. | John (PM) |
| 2025-08-18 | 1.2 | Added Open Core and Feature Tiering strategy. | John (PM) |
| 2025-08-18 | 1.1 | Updated with Hybrid Model and Control Plane. | John (PM) |
| 2025-08-18 | 1.0 | Initial PRD Draft from Specifications. | John (PM) |
