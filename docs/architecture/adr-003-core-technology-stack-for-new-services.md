# ADR-003: Core Technology Stack for New Services

**Date:** 2025-08-22

**Status:** Proposed

## Context

With the decision made in ADR-002 to expand the platform with new service pillars (Synthetic Monitoring, Security Scanning, Cost Management), we must select a consistent, modern, and scalable technology stack for the backend implementation. The chosen stack needs to be well-suited for I/O-bound operations (e.g., making external API calls, running checks) and support a container-based deployment model that is portable across on-premise (Kubernetes) and cloud environments.

## Decision

We will adopt the following technology stack for the development of all new backend services and modules:

-   **Language/Runtime:** **Node.js with TypeScript**. Node.js's non-blocking, event-driven model is ideal for the I/O-heavy nature of the new services. TypeScript provides essential type safety, improving code quality and maintainability.

-   **Framework:** **NestJS**. This framework provides a structured, modular architecture out-of-the-box, enforcing consistency and best practices. Its support for dependency injection and a clear module system will accelerate development.

-   **Primary Database:** **PostgreSQL**. A proven, reliable relational database that will be used for storing configuration data, user information, and structured results from the new services.

-   **Deployment Target:** **Containerization (Docker/OCI)**. All new services will be packaged as Docker containers. The primary deployment environment will be a Kubernetes cluster, ensuring portability from the on-premise private cloud to any public cloud provider's Kubernetes service (EKS, GKE, AKS).

This stack will be used for the central orchestration components of the new services.

## Consequences

**Positive:**

-   **High Performance for I/O:** Node.js is highly efficient for the primary workloads of these new services.
-   **Developer Productivity:** NestJS and TypeScript provide a robust framework that will lead to faster development and fewer errors.
-   **Portability:** The "container-on-Kubernetes" approach provides maximum flexibility, allowing the platform to run on the current on-premise infrastructure and seamlessly migrate or scale to the public cloud in the future.
-   **Consistency:** Establishes a clear, modern standard for all new backend development.

**Negative:**

-   **Learning Curve:** Developers unfamiliar with NestJS or TypeScript may require a brief ramp-up period.
-   **Single-Threaded Nature:** While Node.js is non-blocking, CPU-intensive tasks (if any arise) would need to be handled carefully, likely by offloading them to separate worker processes (a pattern well-supported by NestJS).

---
