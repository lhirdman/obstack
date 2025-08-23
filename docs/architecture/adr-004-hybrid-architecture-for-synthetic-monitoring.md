# ADR-004: Hybrid Architecture for Synthetic Monitoring

**Date:** 2025-08-22

**Status:** Proposed

## Context

The Synthetic Monitoring service, decided upon in ADR-002, requires a technical architecture that can initiate checks from globally distributed locations. The core orchestration logic and data storage will reside within our primary infrastructure (the on-premise Kubernetes cluster), but the execution of the checks (the "runners" or "exit points") must be geographically diverse to provide a true measure of global availability and performance.

We need a solution that is cost-effective, scalable, and avoids locking us into a single public cloud provider, especially during the initial phases of the project.

## Decision

We will implement a hybrid, distributed architecture for the Synthetic Monitoring service:

1.  **Central Orchestrator:** The core logic will run as a service (the "Orchestrator") within our primary Kubernetes cluster. This service, built on the NestJS stack from ADR-003, will be responsible for scheduling checks, managing configurations, and storing results in the central PostgreSQL database.

2.  **Global Execution Grid:** The check execution will be handled by a fleet of lightweight, stateless runners deployed on low-cost Virtual Private Servers (VPS) from multiple, geographically diverse providers (e.g., Vultr, DigitalOcean, Hetzner).

3.  **Communication Protocol:** The Orchestrator will communicate with the runners via a simple, secure, outbound HTTPS-based API. The Orchestrator will call a runner's API endpoint to request a check, and the runner will execute the check and return the result in the API response.

Each runner will be a standardized, containerized application (Docker), making it easy to deploy and manage across different VPS providers.

## Consequences

**Positive:**

-   **Geographic Diversity:** Provides the necessary global footprint for accurate synthetic monitoring.
-   **Cost-Effective:** Leverages low-cost VPS providers for the execution grid, minimizing recurring monthly costs compared to using a major cloud provider's full compute instances for this task.
-   **Portable & Cloud-Agnostic:** The core logic remains on our portable Kubernetes platform, and the runner grid is not tied to any single provider's ecosystem. This model can be migrated or expanded to use cloud-native services (like AWS Lambda) in the future with no change to the central architecture.
-   **Secure:** The communication model is simple and secure. The runners are isolated from the core infrastructure, and communication is initiated from the trusted core to the untrusted edge.

**Negative:**

-   **Management Overhead:** We are responsible for provisioning and managing the lifecycle of the VPS instances. This can be mitigated through automation with tools like Ansible or Terraform.
-   **Network Latency:** Communication between the on-premise orchestrator and the global runners will be subject to public internet latency. However, this is acceptable as the communication is asynchronous to the user experience and the measured latency of the check itself is calculated at the runner, independent of the orchestration communication lag.

---
