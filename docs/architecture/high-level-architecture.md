# High Level Architecture

## Technical Summary

The Obstack platform is architected as a hybrid, open-core system designed for both multi-tenant SaaS and single-tenant Enterprise deployments. The core of the platform utilizes a **Backend-for-Frontend (BFF)** pattern, with a **React/Vite** frontend providing the user experience and a **Python/FastAPI** backend orchestrating data from a suite of underlying open-source services (Prometheus, Loki, Tempo, OpenCost). A **PostgreSQL** database will store all core application data, including user accounts for the Community tier, tenant configurations, and commercial feature data. Authentication is designed to be pluggable, supporting local database accounts and Keycloak for enterprise SSO. This architecture directly supports the PRD goals of providing a unified, tiered, and highly reliable observability solution.

## Platform and Infrastructure Choice

To support the flexibility required by our SaaS and Enterprise tiers, the following platform strategy is recommended:

*   **SaaS Tier Recommendation: Amazon Web Services (AWS)**
    *   **Rationale:** AWS provides the most mature and comprehensive set of managed services required to run a complex application like Obstack at scale. It offers industry-standard solutions for container orchestration (EKS/ECS), managed databases (RDS for PostgreSQL), and object storage (S3), which align perfectly with our tech stack. This choice de-risks our operations and provides a clear path to scalability.
    *   **Key Services:**
        *   **Amazon EKS (or ECS):** For running our containerized application and observability services.
        *   **Amazon RDS for PostgreSQL:** For our core application database.
        *   **Amazon S3:** For long-term storage of logs, metrics, and traces (as a backend for Loki/Thanos).
        *   **Amazon ElastiCache for Redis:** For backend caching.
        *   **Amazon API Gateway / ELB:** To manage ingress traffic to our services.

*   **Enterprise Tier Strategy:**
    *   The architecture will be cloud-agnostic. The use of Docker containers and Ansible for deployment ensures that the Enterprise tier can be deployed on any major cloud provider (AWS, GCP, Azure) or in an on-premise data center, as required by the customer.

## Repository Structure

As defined in the PRD, the project will use a monorepo for the core platform to facilitate development and ensure type-safety across the stack.

*   **Structure:** Monorepo (`obstack/platform`).
*   **Monorepo Tool Recommendation: Nx**
    *   **Rationale:** Nx provides excellent tooling and a robust plugin ecosystem that supports mixed-language projects (TypeScript/Python). It will help us manage dependencies, share code efficiently, and run commands across the repository in a structured way.
*   **Package Organization:**
    *   `apps/`: Will contain the deployable applications (`frontend`, `backend`).
    *   `packages/`: Will contain shared code, such as `shared-types`, `ui-components`, and `eslint-config`.
    *   Root-level directories for `docs/` and `ansible/`.

## High Level Architecture Diagram

This diagram illustrates the primary components of the system and their interactions for the SaaS deployment model.

```mermaid
graph TD
    subgraph "Data Sources"
        AppLogs[Instrumented Apps]
        SystemLogs[VMs / Pods / Files]
    end

    subgraph "User"
        User[End User]
    end

    subgraph "Obstack Platform (AWS VPC)"
        subgraph "Collection & Ingestion"
            Otel[OTEL Collector]
            Vector[Vector Agent]
            Redpanda[Redpanda<br>(Data Streaming)]
        end

        subgraph "Gateway Layer"
            Kong[API Gateway<br>(Kong)]
        end

        subgraph "Application Layer"
            Frontend[React Frontend<br>(Vite/S3/CloudFront)]
            Backend[FastAPI BFF]
        end

        subgraph "Core Services"
            DB[(PostgreSQL<br>Users, Tenants, Config)]
            Cache[(Redis<br>Cache, Task Broker)]
            Identity[Identity Provider<br>(Keycloak)]
        end

        subgraph "Observability Backend"
            Loki[Loki<br>(Short-Term Logs)]
            OpenSearch[OpenSearch<br>(Long-Term Logs & Analytics)]
            Prometheus[Prometheus<br>(Metrics)]
            Tempo[Tempo<br>(Traces)]
            OpenCost[OpenCost<br>(Cost)]
        end

        subgraph "Shared Storage"
            S3[Object Storage<br>(MinIO / AWS S3)]
        end
    end

    %% Data Flow
    AppLogs -- Telemetry --> Otel
    SystemLogs -- Logs --> Vector
    Otel -- Unified Telemetry --> Redpanda
    Vector -- Raw Logs --> Redpanda
    Redpanda -- Topic --> Backend

    %% User Flow
    User --> Frontend
    User -- API Calls --> Kong
    Kong --> Backend

    %% Backend Connections
    Backend --> DB
    Backend --> Cache
    Backend --> Identity
    Backend --> Loki
    Backend --> OpenSearch
    Backend --> Prometheus
    Backend --> Tempo
    Backend --> OpenCost

    %% Internal Telemetry Unification
    Prometheus -- remote_write --> Otel

    %% Storage Connections
    Loki --> S3
    Prometheus -- Long Term --> S3
    Tempo --> S3
```

## Log Ingestion Pipeline

To ensure a scalable and reliable data pipeline for logs, the architecture utilizes a two-tier storage strategy supported by a streaming data platform.

1.  **Collection:**
    *   **Vector & OTEL Collector:** These agents collect logs and telemetry and forward them into the Redpanda streaming platform.

2.  **Streaming:**
    *   **Redpanda (Kafka-compatible):** Acts as a durable buffer, decoupling collection from processing.

3.  **Processing & Tiered Storage:**
    *   The **FastAPI Backend** consumes from Redpanda, enriches the data (e.g., adding `tenant_id`), and forwards it to two destinations:
    *   **Tier 1 (Hot Storage): Loki** is used for short-term storage (7-14 days). Its efficient, index-free design is ideal for fast, recent log queries and for powering dashboards in Grafana.
    *   **Tier 2 (Warm Storage): OpenSearch** is used for long-term storage (30-90 days). It provides powerful full-text search capabilities for ad-hoc troubleshooting and deeper analysis. This also serves as the foundation for our ML/AI features.

This decoupled, two-tier pipeline provides a robust and cost-effective solution for handling high-volume log data, balancing the need for fast, recent queries with deep, long-term search.

## Push-Based Telemetry Ingestion

For SaaS and Enterprise customers, a push-based model is essential for receiving telemetry from their external environments. The platform will provide a secure, tenant-aware endpoint to receive this data.

1.  **Primary Protocol: OpenTelemetry Protocol (OTLP)**
    *   **Rationale:** OTLP is the vendor-neutral standard for telemetry data and is the native protocol for OpenTelemetry. It supports logs, metrics, and traces in a unified format, making it the ideal primary ingestion method.
    *   Customers will configure their OpenTelemetry Collectors or instrumented applications to export data via OTLP/HTTP to a dedicated endpoint on the Obstack platform.

2.  **Secondary Protocol: Prometheus `remote_write`**
    *   **Rationale:** To support the vast ecosystem of existing Prometheus deployments, the platform will also expose a Prometheus `remote_write` compatible endpoint.
    *   Customers can configure their Prometheus instances to forward metrics to this endpoint, allowing for seamless integration without requiring a full switch to the OTEL Collector.

### Ingestion Flow Diagram

```mermaid
graph TD
    subgraph "Customer Environment"
        CustomerApp[Customer Application]
        CustomerPrometheus[Customer Prometheus]
        CustomerOtel[Customer OTEL Collector]
    end

    subgraph "Obstack Platform"
        IngestionGateway[API Gateway<br>(Kong)]
        AuthService[Backend BFF<br>(Authentication & Enrichment)]
        OtelCollector[Obstack OTEL Collector]
        
        subgraph "Observability Backend"
            Prometheus[Prometheus]
            Loki[Loki]
            Tempo[Tempo]
            OpenSearch[OpenSearch]
        end
    end

    %% Data Flow
    CustomerApp -- OTLP --> CustomerOtel
    CustomerOtel -- OTLP/HTTP --> IngestionGateway
    CustomerPrometheus -- remote_write --> IngestionGateway

    IngestionGateway -- Tenant-Specific Route --> AuthService

    AuthService -- Authenticates & Enriches --> OtelCollector

    OtelCollector -- Forwards --> Prometheus
    OtelCollector -- Forwards --> Loki
    OtelCollector -- Forwards --> Tempo
    OtelCollector -- Forwards --> OpenSearch
```

### Authentication and Multi-Tenancy

1.  **Endpoint:** All incoming data will be sent to a single, secure endpoint managed by the API Gateway (Kong).
2.  **Authentication:** The **Backend BFF** is the first point of contact. It is responsible for authenticating each incoming request, likely via a unique API key or token provided to the tenant.
3.  **Enrichment:** Upon successful authentication, the BFF will enrich the telemetry data with the correct `tenant_id` label or attribute. This is a critical step for ensuring data isolation.
4.  **Forwarding:** The enriched data is then forwarded to the internal **OpenTelemetry Collector**, which acts as the central processing and routing hub. The collector will then route the data to the appropriate backend service (Loki, Prometheus, or Tempo) based on its type.

This push-based architecture provides a secure and scalable method for ingesting data from diverse customer environments while maintaining strict multi-tenancy.

## Architectural and Design Patterns

Overall Architecture: Backend-for-Frontend (BFF) to provide a tailored API for our UI, and Open Core to separate community and commercial features.

Frontend Patterns: We will use a combination of established patterns to ensure a scalable and maintainable codebase. This includes the use of Container/Presentational components to separate logic from UI, and the extensive use of Custom Hooks to encapsulate and reuse business logic.

Backend Patterns: Repository Pattern to abstract database interactions, making the code more testable and maintainable. Pluggable Modules for the authentication system to allow for easy switching between Local and Keycloak providers.

Integration Patterns: API Gateway (Kong) to act as a single, secure entry point for all API traffic, handling concerns like rate limiting and authentication.

## Development Workflow

A comprehensive guide to setting up the local development environment, including prerequisites, setup instructions, and common commands, is available in the [Development Environment](./development-environment.md) document.

## Security

A comprehensive overview of the security architecture, including data security, API hardening, and infrastructure security, is detailed in the [Security Architecture](./security.md) document.

## Dependency Management

The strategy for managing external dependencies, including versioning, updating, and licensing, is detailed in the [Dependency Management](./dependency-management.md) document.

## Resilience & Operational Readiness

The architectural strategies for resilience, error handling, self-monitoring, and deployment are detailed in the [Resilience & Operational Readiness](./resilience.md) document.

## Frontend Architecture

This section details the technical architecture for the `frontend` application, a React Single-Page Application (SPA) built with Vite and TypeScript. It translates the UI/UX Specification into a concrete implementation plan.

### 1. Folder Structure

The `apps/frontend/src/` directory will be organized by feature/domain to keep related files together and maintain a clean, scalable structure.

```
apps/frontend/src/
├── api/         # Centralized API client and data fetching hooks
├── assets/      # Static assets like images, fonts
├── components/  # Reusable, shared UI components
│   ├── layout/  # Components like Navbar, Sidebar, PageWrapper
│   └── ui/      # Generic components like Button, Modal, Table
├── features/    # Feature-specific components and logic
│   ├── authentication/
│   ├── dashboard/
│   └── logs/
├── hooks/       # Shared, reusable React hooks
├── lib/         # External library configurations (e.g., date-fns)
├── pages/       # Top-level page components for routing
├── providers/   # React Context providers (e.g., AuthProvider)
├── state/       # Global state management stores (Zustand)
├── styles/      # Global styles, Tailwind CSS configuration
└── utils/       # Shared utility functions
```

### 2. Component Strategy

As defined in the UI/UX Specification, our component strategy is as follows:

*   **Styling:** **Tailwind CSS** will be used exclusively for styling via utility classes.
*   **Logic & Accessibility:** **Head-less UI** will be used for the underlying logic and accessibility of complex components like Modals, Dropdowns, and Toggles.
*   **Icons:** **Heroicons** will be used for all iconography.
*   **Implementation:** We will build a custom component library in `src/components/ui/` that combines these technologies to create a consistent and reusable set of UI elements (e.g., `Button.tsx`, `Modal.tsx`).
*   **Documentation:** Each reusable component will include JSDoc comments to document its props, ensuring clarity for both human developers and AI agents.

### 3. State Management

*   **Local/Component State:** For state that is local to a single component (e.g., form input values), we will use React's built-in `useState` and `useReducer` hooks.
*   **Global State:** For state that needs to be shared across the entire application (e.g., the current user, authentication status, global time range), we will use **Zustand**.
    *   **Rationale:** Zustand is chosen for its simplicity, minimal boilerplate, and performance. It provides a centralized store without the complexity of Redux, making it ideal for our needs. Stores will be defined in the `src/state/` directory.

### 4. Data Fetching & Caching

*   **Client:** A single, configured `axios` client will be created in `src/api/` to handle all communication with the backend BFF. It will be responsible for attaching the JWT authentication token to all requests.
*   **Server State Management:** We will use **React Query (TanStack Query)** to manage all server state.
    *   **Rationale:** React Query is the industry standard for data fetching in React. It provides a robust solution for caching, background refetching, request deduplication, and error handling out-of-the-box. This will significantly simplify our data-fetching logic and improve the user experience by making the application feel faster and more responsive.
    *   **Implementation:** Reusable hooks for each API endpoint will be created in `src/api/` (e.g., `useLogsQuery`, `useAlerts`).

### 5. Authentication Flow

1.  **Login:** After a successful login (either via the local provider or Keycloak redirect), the backend will issue a signed JWT.
2.  **Token Storage:** To mitigate XSS risks, the JWT will be stored in a secure, **HttpOnly cookie**. This makes the token inaccessible to client-side JavaScript. The `axios` client will automatically include this cookie in all subsequent requests.
3.  **Session Management:** The application will rely on the presence and validity of this cookie to determine if a user is authenticated. A global `AuthProvider` will manage the user's authentication state, which can be accessed throughout the app via a `useAuth` hook.
4.  **Logout:** The logout function will call a backend endpoint (`/api/v1/auth/logout`) that clears the HttpOnly cookie, effectively ending the user's session.

### 6. Routing & Navigation

*   **Library:** We will use **React Router v7** (`react-router-dom`) for all client-side routing.
*   **Route Definitions:** Routes will be defined centrally. A distinction will be made between public routes (e.g., `/login`, `/register`) and private routes that require authentication.
*   **Route Protection:** A custom `<ProtectedRoute>` component will be implemented. This component will check for the user's authentication status via the `useAuth` hook and redirect unauthenticated users to the login page.
*   **Layouts:** The application will use a layout-based routing system. For example, an `AppLayout` (with sidebar and navbar) for authenticated routes and an `AuthLayout` for login/register pages.

### 7. Frontend Performance

To ensure a fast and responsive user experience, the following performance strategies will be implemented:

*   **Code Splitting:** We will use route-based code splitting with `React.lazy()` and `<Suspense>`. This ensures that users only download the JavaScript needed for the specific page they are viewing.
*   **Image Optimization:** All static images will be optimized (e.g., converted to WebP) and lazy-loaded using the native `loading="lazy"` attribute.
*   **Memoization:** To prevent unnecessary re-renders of complex components, we will strategically use `React.memo` for components and the `useMemo` and `useCallback` hooks for expensive calculations and functions.
*   **Bundling:** Vite's build process, which includes tree-shaking and minification, will be relied upon to produce an optimized production bundle.

## Future Architectural Evolution

To build upon the existing foundation, the platform will be expanded in a phased approach. The following sections outline the proposed architecture for these future capabilities, which are documented in detail in their respective Architectural Decision Records (ADRs).

### Phase 1: Foundational Service Expansion

This phase focuses on adding immediate value by integrating new services that are primarily I/O-bound and can be built using a consistent, containerized backend architecture.

-   **Services:** Synthetic Monitoring, Security & Compliance Scanning, Cloud Cost Management.
-   **Architecture:** As detailed in **ADR-003** and **ADR-004**, these services will be built as modules within a **Node.js/NestJS** backend. They will be deployed as containers within the primary Kubernetes cluster and will orchestrate external actions (e.g., calling cloud provider APIs or triggering global synthetic runners). This introduces a secondary backend stack optimized for asynchronous, I/O-heavy workloads.

### Phase 2: High-Volume RUM & Analytics Pipeline

This phase introduces a new, high-throughput data pipeline designed to ingest and analyze Real User Monitoring (RUM) and other high-volume analytics data from client-side agents.

-   **Services:** Web Analytics (GA-style), Interaction Heatmaps, Conversion Funnels.
-   **Proposed Architecture:**
    -   **Data Collection:** A client-side agent (e.g., **Grafana Faro** or **OpenTelemetry JS SDK**) will capture user interactions and performance metrics.
    -   **Ingestion:** Data will be sent to a scalable ingestion endpoint (e.g., an **OpenTelemetry Collector** service in the K8s cluster).
    -   **Buffering:** The collector will forward data to a **Kafka/Redpanda** streaming platform to decouple ingestion from processing.
    -   **Storage & Processing:** A new stream processing service will consume from the message queue and write the data to a dedicated **ClickHouse** cluster for high-speed analytical querying.

### Phase 3: ML/AI Predictive Features

This phase leverages the rich datasets collected in both the existing observability backend and the new analytics pipeline to provide predictive, AI-driven insights.

-   **Services:** Predictive Resource Scaling, Proactive Anomaly Detection, Outage Prediction.
-   **Proposed Architecture:** The initial implementation of ML features will **leverage the powerful, built-in Machine Learning capabilities of the existing OpenSearch cluster**. This includes anomaly detection for logs and metrics, log clustering, and forecasting. This approach simplifies the architecture and accelerates the delivery of initial AI-powered features.
-   For more advanced, future "moonshot" features that may require custom models or data from multiple sources (PostgreSQL, Prometheus, etc.), the platform may be expanded with a dedicated ML platform like **Kubeflow** or **MLflow**. This will be evaluated after the capabilities of the OpenSearch ML framework have been fully utilized.
