# Obstack Fullstack Architecture Document

## High Level Architecture

### Technical Summary

The Obstack platform is architected as a hybrid, open-core system designed for both multi-tenant SaaS and single-tenant Enterprise deployments. The core of the platform utilizes a **Backend-for-Frontend (BFF)** pattern, with a **React/Vite** frontend providing the user experience and a **Python/FastAPI** backend orchestrating data from a suite of underlying open-source services (Prometheus, Loki, Tempo, OpenCost). A **PostgreSQL** database will store all core application data, including user accounts for the Community tier, tenant configurations, and commercial feature data. Authentication is designed to be pluggable, supporting local database accounts and Keycloak for enterprise SSO. This architecture directly supports the PRD goals of providing a unified, tiered, and highly reliable observability solution.

### Platform and Infrastructure Choice

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

### Repository Structure

As defined in the PRD, the project will use a monorepo for the core platform to facilitate development and ensure type-safety across the stack.

*   **Structure:** Monorepo (`obstack/platform`).
*   **Monorepo Tool Recommendation: Nx**
    *   **Rationale:** Nx provides excellent tooling and a robust plugin ecosystem that supports mixed-language projects (TypeScript/Python). It will help us manage dependencies, share code efficiently, and run commands across the repository in a structured way.
*   **Package Organization:**
    *   `apps/`: Will contain the deployable applications (`frontend`, `backend`).
    *   `packages/`: Will contain shared code, such as `shared-types`, `ui-components`, and `eslint-config`.
    *   Root-level directories for `docs/` and `ansible/`.

### High Level Architecture Diagram

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
            Loki[Loki<br>(Logs)]
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
    Backend --> Prometheus
    Backend --> Tempo
    Backend --> OpenCost

    %% Storage Connections
    Loki --> S3
    Prometheus -- Long Term --> S3
    Tempo --> S3
```

### Log Ingestion Pipeline

To ensure a scalable and reliable data pipeline for logs, the architecture includes a streaming data platform (Redpanda) and dedicated collection agents (Vector and the OTEL Collector).

1.  **Collection:**
    *   **Vector:** Deployed as a node-level agent, Vector is responsible for collecting logs from system files, syslog, and other non-application sources.
    *   **OTEL Collector:** Used as a sidecar or gateway, the OTEL Collector receives structured telemetry (logs, metrics, traces) from applications that are instrumented with OpenTelemetry SDKs.

2.  **Streaming:**
    *   Both Vector and the OTEL Collector forward their data into **Redpanda**, a Kafka-compatible streaming platform. This decouples the collection layer from the processing layer, providing a durable buffer that can handle backpressure and ensure data is not lost.

3.  **Processing & Storage:**
    *   The **FastAPI Backend** includes a consumer service that reads from the appropriate topics in Redpanda.
    *   This service is responsible for parsing, enriching (e.g., adding `tenant_id`), and validating the log data before forwarding it to its final destination, **Loki**, for long-term storage and querying.

This decoupled pipeline provides a robust foundation for handling high-volume log data, which is critical for the platform's reliability.

### Push-Based Telemetry Ingestion

For SaaS and Enterprise customers, a push-based model is essential for receiving telemetry from their external environments. The platform will provide a secure, tenant-aware endpoint to receive this data.

1.  **Primary Protocol: OpenTelemetry Protocol (OTLP)**
    *   **Rationale:** OTLP is the vendor-neutral standard for telemetry data and is the native protocol for OpenTelemetry. It supports logs, metrics, and traces in a unified format, making it the ideal primary ingestion method.
    *   Customers will configure their OpenTelemetry Collectors or instrumented applications to export data via OTLP/HTTP to a dedicated endpoint on the Obstack platform.

2.  **Secondary Protocol: Prometheus `remote_write`**
    *   **Rationale:** To support the vast ecosystem of existing Prometheus deployments, the platform will also expose a Prometheus `remote_write` compatible endpoint.
    *   Customers can configure their Prometheus instances to forward metrics to this endpoint, allowing for seamless integration without requiring a full switch to the OTEL Collector.

#### Ingestion Flow Diagram

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
```

#### Authentication and Multi-Tenancy

1.  **Endpoint:** All incoming data will be sent to a single, secure endpoint managed by the API Gateway (Kong).
2.  **Authentication:** The **Backend BFF** is the first point of contact. It is responsible for authenticating each incoming request, likely via a unique API key or token provided to the tenant.
3.  **Enrichment:** Upon successful authentication, the BFF will enrich the telemetry data with the correct `tenant_id` label or attribute. This is a critical step for ensuring data isolation.
4.  **Forwarding:** The enriched data is then forwarded to the internal **OpenTelemetry Collector**, which acts as the central processing and routing hub. The collector will then route the data to the appropriate backend service (Loki, Prometheus, or Tempo) based on its type.

This push-based architecture provides a secure and scalable method for ingesting data from diverse customer environments while maintaining strict multi-tenancy.

### Architectural and Design Patterns

Overall Architecture: Backend-for-Frontend (BFF) to provide a tailored API for our UI, and Open Core to separate community and commercial features.

Frontend Patterns: We will use a combination of established patterns to ensure a scalable and maintainable codebase. This includes the use of Container/Presentational components to separate logic from UI, and the extensive use of Custom Hooks to encapsulate and reuse business logic.

Backend Patterns: Repository Pattern to abstract database interactions, making the code more testable and maintainable. Pluggable Modules for the authentication system to allow for easy switching between Local and Keycloak providers.

Integration Patterns: API Gateway (Kong) to act as a single, secure entry point for all API traffic, handling concerns like rate limiting and authentication.

### Frontend Architecture

This section details the technical architecture for the `frontend` application, a React Single-Page Application (SPA) built with Vite and TypeScript. It translates the UI/UX Specification into a concrete implementation plan.

#### 1. Folder Structure

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

#### 2. Component Strategy

As defined in the UI/UX Specification, our component strategy is as follows:

*   **Styling:** **Tailwind CSS** will be used exclusively for styling via utility classes.
*   **Logic & Accessibility:** **Headless UI** will be used for the underlying logic and accessibility of complex components like Modals, Dropdowns, and Toggles.
*   **Icons:** **Heroicons** will be used for all iconography.
*   **Implementation:** We will build a custom component library in `src/components/ui/` that combines these technologies to create a consistent and reusable set of UI elements (e.g., `Button.tsx`, `Modal.tsx`).

#### 3. State Management

*   **Local/Component State:** For state that is local to a single component (e.g., form input values), we will use React's built-in `useState` and `useReducer` hooks.
*   **Global State:** For state that needs to be shared across the entire application (e.g., the current user, authentication status, global time range), we will use **Zustand**.
    *   **Rationale:** Zustand is chosen for its simplicity, minimal boilerplate, and performance. It provides a centralized store without the complexity of Redux, making it ideal for our needs. Stores will be defined in the `src/state/` directory.

#### 4. Data Fetching & Caching

*   **Client:** A single, configured `axios` client will be created in `src/api/` to handle all communication with the backend BFF. It will be responsible for attaching the JWT authentication token to all requests.
*   **Server State Management:** We will use **React Query (TanStack Query)** to manage all server state.
    *   **Rationale:** React Query is the industry standard for data fetching in React. It provides a robust solution for caching, background refetching, request deduplication, and error handling out-of-the-box. This will significantly simplify our data-fetching logic and improve the user experience by making the application feel faster and more responsive.
    *   **Implementation:** Reusable hooks for each API endpoint will be created in `src/api/` (e.g., `useLogsQuery`, `useAlerts`).

#### 5. Authentication Flow

1.  **Login:** After a successful login (either via the local provider or Keycloak redirect), the backend will issue a signed JWT.
2.  **Token Storage:** To mitigate XSS risks, the JWT will be stored in a secure, **HttpOnly cookie**. This makes the token inaccessible to client-side JavaScript. The `axios` client will automatically include this cookie in all subsequent requests.
3.  **Session Management:** The application will rely on the presence and validity of this cookie to determine if a user is authenticated. A global `AuthProvider` will manage the user's authentication state, which can be accessed throughout the app via a `useAuth` hook.
4.  **Logout:** The logout function will call a backend endpoint (`/api/v1/auth/logout`) that clears the HttpOnly cookie, effectively ending the user's session.

## Tech Stack

The technology stack is defined in the [Tech Stack](./architecture/tech-stack.md) document.
Data Models

The following data models represent the core entities of the Obstack platform. They are defined here as TypeScript interfaces, which will be shared between the frontend and backend to ensure end-to-end type safety. The backend will use Pydantic models that are structurally identical to these interfaces.

Tenant

Represents a customer in the system, providing the primary boundary for data isolation.

Purpose: To define a customer's subscription, features, and serve as the root for all tenant-specific data.

TypeScript Interface (packages/shared-types/src/tenant.ts)

code
TypeScript
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
export interface Tenant {
  id: string;
  keycloak_realm_id?: string; // Optional as Community tier might not have one
  name: string;
  subscription_plan: 'community' | 'saas' | 'enterprise';
  is_active: boolean;
  created_at: string; // ISO 8601 date string
  updated_at: string; // ISO 8601 date string
}```

### User

Represents an individual user within a specific tenant.

**Purpose:** To manage user identity, roles, and application-specific settings.

**TypeScript Interface (`packages/shared-types/src/user.ts`)**
```typescript
export interface User {
  id: string;
  keycloak_user_id?: string; // Optional as Community tier uses local auth
  tenant_id: string;
  email: string;
  roles: ('admin' | 'viewer' | string)[]; // Allows for custom roles
  created_at: string; // ISO 8601 date string
}
Alert

Represents a single alert ingested from an external system like Prometheus Alertmanager.

Purpose: To provide a structured format for all alerts within the unified alert management system.

TypeScript Interface (packages/shared-types/src/alert.ts)

code
TypeScript
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
export type AlertStatus = 'active' | 'acknowledged' | 'resolved';
export type AlertSeverity = 'critical' | 'high' | 'warning' | 'info';

export interface Alert {
  id: string;
  tenant_id: string;
  status: AlertStatus;
  severity: AlertSeverity;
  title: string;
  description: string;
  source: string;
  labels: Record<string, string>;
  created_at: string; // ISO 8601 date string
}
API Specification

The Obstack API is a RESTful service built with FastAPI. The specification follows the OpenAPI 3.0 standard. Documentation will be automatically generated and served by the backend at the /api/docs endpoint, rendered with Redocly. All endpoints are prefixed with /api/v1 and require a valid JWT for access, unless otherwise specified.

REST API Specification (Initial Draft)
code
Yaml
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
openapi: 3.0.3
info:
  title: Obstack API
  version: 1.0.0
  description: The official REST API for the Obstack platform. Provides unified access to observability data, cost monitoring, and platform management.
servers:
  - url: /api/v1
    description: API Server

paths:
  /health:
    get:
      summary: Health Check
      description: Provides a simple health check of the API server. Does not require authentication.
      tags:
        - General
      responses:
        '200':
          description: API is healthy.
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "healthy"

  /auth/register:
    post:
      summary: User Registration (Local Auth)
      description: Allows a new user to register for an account in the Community (self-hosted) edition. This endpoint is only available when `AUTH_METHOD=local`.
      tags:
        - Authentication
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserRegistration'
      responses:
        '201':
          description: User successfully created.
        '400':
          description: Invalid input or user already exists.

  /auth/login:
    post:
      summary: User Login (Local Auth)
      description: Authenticates a user with email and password to get a JWT. This endpoint is only available when `AUTH_METHOD=local`.
      tags:
        - Authentication
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserLogin'
      responses:
        '200':
          description: Login successful. Returns a JWT.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AuthToken'
        '401':
          description: Invalid credentials.

components:
  schemas:
    UserRegistration:
      type: object
      properties:
        email:
          type: string
          format: email
        password:
          type: string
          format: password
        tenant_name:
          type: string
      required:
        - email
        - password
        - tenant_name

    UserLogin:
      type: object
      properties:
        email:
          type: string
          format: email
        password:
          type: string
          format: password
      required:
        - email
        - password

    AuthToken:
      type: object
      properties:
        access_token:
          type: string
        token_type:
          type: string
          example: "bearer"
Components

The Obstack platform is composed of several logical components within the backend application. These components are designed to be cohesive and loosely coupled, each handling a distinct domain of responsibility.

1. Authentication Service (backend/app/services/auth_service.py)

Responsibility: Manages all aspects of user authentication and authorization. It implements the "pluggable" auth strategy, handling either local password-based authentication or delegating to Keycloak for SSO. It is responsible for creating, signing, and validating JWTs.

Dependencies: PostgreSQL Database (for local auth), Keycloak service (for SSO), Security module.

2. Tenant Management Service (backend/app/services/tenant_service.py)

Responsibility: Handles the creation and management of tenants and users within the platform's PostgreSQL database. It ensures that every user is correctly associated with a tenant and manages subscription tier information and feature flags.

Dependencies: PostgreSQL Database.

3. Unified Query Service (backend/app/services/query_service.py)

Responsibility: This is the core of the observability functionality. It acts as a fan-out service, taking a unified search request from the user and dispatching parallel, tenant-aware queries to the appropriate downstream data sources (Loki, Prometheus, Tempo). It is also responsible for aggregating and normalizing the results before returning them to the frontend.

Dependencies: Loki, Prometheus, Tempo services.

4. Cost Monitoring Service (backend/app/services/cost_service.py)

Responsibility: Manages all interactions with the OpenCost API. It fetches cost data, performs historical analysis and aggregation (for paid tiers), and runs the anomaly detection jobs. It provides all data required for the Cost Insights dashboards.

Dependencies: OpenCost API, PostgreSQL Database (for storing historical data).

5. Alerting Service (backend/app/services/alert_service.py)

Responsibility: Manages the lifecycle of alerts. It provides a webhook endpoint to ingest alerts from Prometheus Alertmanager, stores them in the database, and provides APIs for the frontend to list, view, and update their status. It also handles dispatching notifications for paid tiers.

Dependencies: PostgreSQL Database, external notification services (e.g., Slack Webhooks).

6. Frontend Application (frontend/src/)

Responsibility: This is the user-facing React single-page application (SPA). It is responsible for rendering all UI components, managing client-side state, and communicating with the backend BFF via the REST API. It enforces the user experience and visual design of the platform.

Dependencies: Backend API.

Component Interaction Diagram
code
Mermaid
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
graph TD
    User -- Interacts with --> FE[Frontend App]
    FE -- API Request w/ JWT --> API[FastAPI Backend]

    subgraph API [FastAPI Backend]
        Auth[Authentication Service] -- Validates JWT --> Ctx[Tenant/User Context]
        
        subgraph Endpoints
            QueryEP[/api/v1/query]
            CostEP[/api/v1/costs]
            AlertEP[/api/v1/alerts]
        end

        QueryEP --> QuerySvc[Unified Query Service]
        CostEP --> CostSvc[Cost Monitoring Service]
        AlertEP --> AlertSvc[Alerting Service]

        Auth -- Manages Users --> DBLayer
        QuerySvc -- Gets Tenant Info --> DBLayer
        CostSvc -- Stores History --> DBLayer
        AlertSvc -- Stores Alerts --> DBLayer

        DBLayer[Repository Layer<br>(PostgreSQL)]
    end

    QuerySvc -- Queries --> Loki[Loki API]
    QuerySvc -- Queries --> Prometheus[Prometheus API]
    QuerySvc -- Queries --> Tempo[Tempo API]
    CostSvc -- Queries --> OpenCost[OpenCost API]
External APIs
1. Thanos Query API

Purpose: To query for long-term time-series metrics data using PromQL. Thanos acts as the query layer on top of metrics stored in S3.

Documentation: https://thanos.io/tip/thanos/api.md/

Key Endpoints Used: GET /api/v1/query_range

Integration Notes: This is the primary endpoint for historical metrics dashboards. All queries will be injected with a {tenant_id="..."} label.

2. Loki API

Purpose: To query for log data using the Log Query Language (LogQL).

Documentation: https://grafana.com/docs/loki/latest/reference/api/

Key Endpoints Used: GET /loki/api/v1/query_range

Integration Notes: All queries will be injected with a {tenant_id="..."} label.

3. Tempo API

Purpose: To retrieve distributed trace data.

Documentation: https://grafana.com/docs/tempo/latest/reference/api/

Key Endpoints Used: GET /api/traces/{traceID}

Integration Notes: Backend will enforce tenant access before querying.

4. OpenSearch API

Purpose: To provide advanced, full-text search capabilities across log data.

Documentation: https://opensearch.org/docs/latest/api-reference/index/

Key Endpoints Used: POST /{tenant_index}/_search

Integration Notes: Backend will manage tenant-specific indices to guarantee data isolation.

5. OpenCost API

Purpose: To query for Kubernetes cost allocation and optimization data.

Documentation: https://www.opencost.io/docs/apis/apis-overview

Key Endpoints Used: GET /allocation/compute

Integration Notes: Backend will filter results by namespace to enforce tenant isolation.

6. S3-Compatible API (MinIO / AWS S3)

Purpose: To directly interact with object storage for administrative tasks.

Documentation: Varies by provider (e.g., AWS S3).

Integration Notes: Used for administrative tasks. Operations will be strictly scoped to paths prefixed with the tenant_id.

7. Keycloak Admin API

Purpose: (Used by the external Control Plane) To programmatically create and manage Realms, users, and roles.

Documentation: https://www.keycloak.org/docs-api/latest/rest-api/index.html

Integration Notes: Not called by the core backend, but by the separate obstack/control-plane application.

Core Workflows
1. User Login and Authenticated Data Fetch (SaaS/Enterprise Tier)
code
Mermaid
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
sequenceDiagram
    participant User
    participant Frontend (React)
    participant Kong (API Gateway)
    participant Backend (FastAPI)
    participant Keycloak
    participant Loki

    %% Login Flow %%
    User->>Frontend: Clicks "Login"
    Frontend->>User: Redirects to Keycloak Login Page
    User->>Keycloak: Enters Credentials
    Keycloak-->>User: Redirects back to Frontend with Auth Code
    
    Frontend->>Backend: Exchanges Auth Code for Token
    Backend->>Keycloak: Validates Code, requests Token
    Keycloak-->>Backend: Issues signed JWT
    Backend-->>Frontend: Returns JWT to Frontend

    Frontend-->>Frontend: Stores JWT securely

    %% Authenticated Data Fetch Flow %%
    User->>Frontend: Navigates to "Logs" view
    Frontend->>Kong: GET /api/v1/logs/query (with JWT in Header)
    Kong->>Backend: Forwards Request
    
    Backend->>Backend: Auth middleware validates JWT and extracts tenant_id
    
    Note right of Backend: Injects tenant_id into LogQL query
    Backend->>Loki: GET /loki/api/v1/query_range?query={tenant_id="..."}
    Loki-->>Backend: Returns log data for that tenant
    
    Backend-->>Frontend: Returns log data in JSON format
    Frontend->>User: Renders Logs in the UI
Database Schema

The following SQL DDL defines the initial schema for the PostgreSQL database, managed via Alembic.

tenants Table
code
SQL
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
CREATE TYPE subscription_plan AS ENUM ('community', 'saas', 'enterprise');

CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keycloak_realm_id VARCHAR(255) UNIQUE,
    name VARCHAR(255) NOT NULL,
    plan subscription_plan NOT NULL DEFAULT 'community',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
users Table
code
SQL
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    keycloak_user_id UUID UNIQUE,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),
    roles VARCHAR(50)[] NOT NULL DEFAULT ARRAY['viewer']::VARCHAR(50)[],
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_users_tenant_id ON users(tenant_id);
alerts Table
code
SQL
download
content_copy
expand_less
IGNORE_WHEN_COPYING_START
IGNORE_WHEN_COPYING_END
CREATE TYPE alert_status AS ENUM ('active', 'acknowledged', 'resolved');
CREATE TYPE alert_severity AS ENUM ('critical', 'high', 'warning', 'info');

CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    status alert_status NOT NULL DEFAULT 'active',
    severity alert_severity NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    source VARCHAR(100) NOT NULL,
    labels JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_alerts_tenant_id_status ON alerts(tenant_id, status);
## Unified Project Structure

The project structure is defined in the [Source Tree](./architecture/source-tree.md) document.

## Development Workflow & Coding Standards

The development workflow and coding standards are defined in the [Coding Standards](./architecture/coding-standards.md) document.

### Testing Strategy

Our testing strategy is designed to ensure application quality, reliability, and performance by catching bugs early and preventing regressions. We will follow the principles of the Testing Pyramid, emphasizing a strong foundation of fast, isolated unit tests, supported by broader integration and end-to-end tests.

#### Testing Pyramid

We will adhere to a standard testing pyramid model:
-   **Unit Tests (Base):** The majority of our tests. They are fast, reliable, and verify the smallest pieces of our application in isolation.
-   **Integration Tests (Middle):** These tests will verify the interactions between different components, services, or modules (e.g., an API endpoint connecting to a database).
-   **End-to-End (E2E) Tests (Top):** A smaller number of E2E tests will simulate real user workflows from the browser to the database, ensuring the entire system works together as expected.

#### Test Types, Tooling, and Scope

| Test Type | Tooling | Scope & Purpose |
|---|---|---|
| **Unit Tests** | Vitest (Frontend), Pytest (Backend) | Test individual functions, components, or classes in isolation. All external dependencies (e.g., APIs, databases) will be mocked. |
| **Integration Tests** | Pytest, Docker Compose | Test the interaction between backend services, such as an API endpoint and a real test database, to validate data integrity and contracts. |
| **End-to-End (E2E) Tests** | Playwright | Test critical user workflows across the entire application stack (frontend to backend to database) in a production-like environment. |
| **Load & Performance** | k6 / Locust | Assess system performance, scalability, and reliability under heavy load to identify bottlenecks. |
| **Chaos Engineering** | Chaos Mesh | Proactively test system resilience by injecting failures (e.g., network latency, pod failures) into the test environment. |

#### Continuous Testing Workflow

Testing is an integral part of our CI/CD pipeline to provide rapid feedback.
-   **On Every Commit:** All unit and integration tests will be automatically executed.
-   **On Pull Request to `main`:** The full test suite (Unit, Integration, E2E) will run.
-   **Post-Deployment:** E2E tests will run against the staging environment to verify deployment health.
