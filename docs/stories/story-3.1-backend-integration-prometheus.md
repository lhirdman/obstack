# Story 3.1: Backend Integration with Prometheus

## Status
- Approved

## Story
- **As a** Backend Developer,
- **I want** the backend to query a Prometheus/Thanos instance based on the user's tenant,
- **so that** we can securely serve metrics data to the frontend.

## Acceptance Criteria
1.  The backend provides a service that can connect to and query a Prometheus-compatible API.
2.  All PromQL queries sent from the backend are automatically injected with the `tenant_id` label to enforce data isolation.
3.  A new API endpoint is created (e.g., `/api/v1/metrics/query`) that proxies queries to Prometheus and returns the results.
4.  The endpoint is protected and requires a valid JWT.
5.  The new endpoint is documented in the API reference (Redocly).

## Tasks / Subtasks
- [ ] Task 1: Develop a backend service to connect and query a Prometheus-compatible API. (AC: #1)
- [ ] Task 2: Ensure all outgoing PromQL queries are injected with the `tenant_id` label. (AC: #2)
- [ ] Task 3: Create the `/api/v1/metrics/query` endpoint to proxy queries to Prometheus. (AC: #3)
- [ ] Task 4: Secure the new endpoint, requiring a valid JWT. (AC: #4)
- [ ] Task 5: Document the new endpoint in the Redocly API reference. (AC: #5)

## Dev Notes
- The new metrics service should be located in `apps/backend/app/services/metrics_service.py`.
- Use a Python client library for Prometheus, such as `prometheus-api-client`.
- The `tenant_id` should be extracted from the user's JWT and used to inject a label matcher (e.g., `{tenant_id="..."}`) into every PromQL query. This is a critical security requirement.
- The Prometheus/Thanos API endpoint URL should be configurable via environment variables.

### Testing
- Create integration tests for the `/api/v1/metrics/query` endpoint.
- The tests should mock the Prometheus API.
- Test scenarios:
    - A valid query is correctly proxied and the `tenant_id` label is injected.
    - A query to an unprotected endpoint fails.
    - A query from a user in Tenant A does not return data for Tenant B.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-19 | 1.1 | Enriched with technical details. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 3. | Sarah (PO) |

## Dev Agent Record
*This section is for the development agent.*

## QA Results
*This section is for the QA agent.*
