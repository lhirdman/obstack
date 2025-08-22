# Requirements

## Scope Boundaries & Out of Scope

To maintain focus on the core MVP, the following areas are explicitly **out of scope** for the initial epics:

*   **Log Management:** No log archiving, rehydration, or complex log-based metric creation.
*   **Metrics:** No support for ingesting metrics from proprietary agents. The focus is on Prometheus compatibility.
*   **Traces:** No advanced trace analytics or automatic anomaly detection on trace patterns.
*   **Custom Dashboards:** The initial version will rely on embedded Grafana for complex dashboards; a native dashboard builder is out of scope.
*   **User Management:** No support for teams or fine-grained resource access within a tenant. Initial roles are limited to Admin and Viewer.

## Functional Requirements

*   **FR1: `[Community]`** As a DevOps engineer, I want to access all observability signals (logs, metrics, traces, alerts) through a single unified interface, so that I can efficiently troubleshoot issues without switching between multiple tools.
*   **FR2: `[Community]`** As a developer, I want to search across logs, metrics, and traces using a unified search interface, so that I can quickly find relevant information during debugging sessions.
*   **FR3: `[Community]`** As a site reliability engineer, I want to receive and manage alerts from multiple sources in a centralized location, so that I can respond quickly to incidents and maintain system reliability.
*   **FR4: `[Community]`** As a platform operator, I want a robust and scalable pipeline to ingest logs from various sources (e.g., applications, servers, containers), so that all relevant data is available for analysis in the platform.
*   **FR5: `[Community]`** As a frontend developer, I want the application to provide a responsive and intuitive user interface, so that users can efficiently navigate and interact with observability data across different devices.
*   **FR6: `[Community]`** As an API consumer, I want well-documented REST APIs, so that I can integrate the observability platform with other tools and automate workflows.
*   **FR7: `[Community]`** As a platform operator, I want insights into Kubernetes resource usage and basic cost visibility, so that I can understand my current infrastructure spend.
*   **FR8: `[SaaS]`** As a platform operator, I want to see historical cost analysis and trends, and receive basic optimization recommendations.
*   **FR9: `[Enterprise]`** As a platform operator, I want to receive automated cost anomaly alerts and generate chargeback/showback reports for internal accounting.
*   **FR10: `[Community]`** As an administrator, I want to manage a local set of users (invite, deactivate, assign roles) via a database-backed authentication system, so that my team can securely access the self-hosted instance without needing an external identity provider.
*   **FR10.1: `[SaaS/Enterprise]`** As a platform administrator, I want a secure, local administrative account, so that I can always access the system for emergency maintenance or to reconfigure SSO providers if they are misconfigured.
*   **FR11: `[SaaS]`** As a customer, I want to log in using my existing Google or GitHub account (SSO/OIDC), so that I don't have to manage another set of credentials.
*   **FR12: `[Enterprise]`** As an enterprise administrator, I want to integrate the platform with our corporate directory (SAML/LDAP), so that our employees can log in with their standard company credentials and we can manage access centrally.
*   **FR13: `[Community]`** As a managed service provider, I want multi-tenant isolation, so that I can securely serve multiple clients from a single observability platform instance.
*   **FR14: `[SaaS]`** As an administrator, I want to define custom, fine-grained roles and permissions, so that I can enforce the principle of least privilege for my users.
*   **FR15: `[Enterprise]`** As a compliance officer, I want to view a detailed, immutable audit log of all user actions and system events, so that I can meet our regulatory requirements.
*   **FR16: `[SaaS]`** As a new customer, I want my observability instance to be provisioned automatically and be ready for data ingestion within minutes of signing up.
*   **FR17: `[Enterprise]`** As a system administrator, I want to deploy the entire platform into our on-premise data center or private cloud (VPC), including air-gapped environments.
*   **FR18: `[Enterprise]`** As an enterprise administrator, I want to configure the platform to use our existing corporate data storage and backup solutions.
*   **FR19: `[SaaS]`** As a Pro plan customer, I want to access to email and chat support for troubleshooting and questions.
*   **FR20: `[Enterprise]`** As an Enterprise customer, I want to access to a dedicated support channel and a guaranteed Service Level Agreement (SLA) for uptime.
*   **FR21: `[SaaS]`** As a customer, I want to push telemetry data from my external environment to a secure, tenant-aware endpoint, so that I can monitor all my applications and infrastructure in one place.

## Non-Functional Requirements

This section defines the specific, measurable quality attributes of the system. These are critical for architecture and development decisions.

| Category | Requirement ID | Description | Metric | Target | Tier |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Performance** | **NFR-P1** | API Response Time | 95th Percentile (p95) latency for core API endpoints (e.g., query, login) | < 300ms | Community |
| | **NFR-P2** | Frontend Page Load | Largest Contentful Paint (LCP) for main dashboards | < 1.5 seconds | Community |
| | **NFR-P3** | Data Query Lag | Time from event generation to visibility in UI | < 15 seconds | Community |
| | **NFR-P4** | Log Ingestion Lag | Time from agent collection to visibility in Redpanda | < 2 seconds | Community |
| | **NFR-P5** | Scalability | Concurrent users supported with p95 < 300ms | 500 users | SaaS |
| **Reliability**| **NFR-R1** | System Availability | Uptime of the core platform services | 99.5% | SaaS |
| | **NFR-R2** | System Availability | Uptime of the core platform services | 99.95% | Enterprise |
| | **NFR-R3** | Recovery Time | Recovery Time Objective (RTO) after critical failure | < 4 hours | SaaS |
| | **NFR-R4** | Data Durability | Recovery Point Objective (RPO) | < 1 hour | SaaS |
| **Security** | **NFR-S1** | Tenant Isolation | Automated tests proving zero cross-tenant data access | 100% pass rate | Community |
| | **NFR-S2** | Vulnerability Scan | Critical vulnerabilities in container images or dependencies | Zero | Community |
| | **NFR-S3** | Authentication | Password hashing algorithm | bcrypt (cost=12) | Community |
| | **NFR-S4** | All incoming data via the push ingestion endpoint must be authenticated via a tenant-specific token/key. | Unauthenticated request rejection rate | 100% | SaaS |
| **Usability** | **NFR-U1** | Accessibility | WCAG Compliance Level | AA 2.1 | Community |
| | **NFR-U2** | Local Install | Time from `docker-compose up` to running application | < 5 minutes | Community |
| **Maintainability**| **NFR-M1**| Code Quality | Code coverage from automated tests | > 80% | Community |
| | **NFR-M2**| CI/CD Pipeline | Time from commit to deployment in staging | < 20 minutes | SaaS |

## Feature Tiering Strategy

The platform's features are tiered to support the Open Core model. The tiering is managed by a feature flagging system, with the code for all features residing in the same repository.

| Feature | Community | SaaS | Enterprise |
| :--- | :--- | :--- | :--- |
| **Unified UI** | ✅ | ✅ | ✅ |
| **Unified Search** | ✅ | ✅ | ✅ |
| **Log/Metric/Trace Ingestion** | ✅ | ✅ | ✅ |
| **Local User Authentication** | ✅ (Primary Method) | ✅ (Admin/Recovery Only) | ✅ (Admin/Recovery Only) |
| **Multi-Tenancy** | ✅ | ✅ | ✅ |
| **Basic Cost Visibility** | ✅ | ✅ | ✅ |
| **SSO/OIDC (Google, GitHub)** | ❌ | ✅ | ✅ |
| **SAML/LDAP Integration** | ❌ | ❌ | ✅ |
| **Fine-Grained RBAC** | ❌ | ✅ | ✅ |
| **Audit Logs** | ❌ | ❌ | ✅ |
| **Automated Provisioning** | N/A | ✅ | ✅ |
| **On-Premise Deployment** | ✅ | N/A | ✅ |
| **Advanced Cost Reporting** | ❌ | ✅ | ✅ |
| **Email/Chat Support** | ❌ | ✅ | ✅ |
| **Dedicated Support & SLA** | ❌ | ❌ | ✅ |
| **Push-Based Telemetry Ingestion** | ❌ | ✅ | ✅ |