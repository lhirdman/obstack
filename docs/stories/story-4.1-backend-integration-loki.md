# Story 4.1: Backend Integration with Loki

## Status
- Approved

## Story
- **As a** Backend Developer,
- **I want** the backend to query a Loki instance using tenant-isolated LogQL queries,
- **so that** we can securely serve log data to the frontend.

## Acceptance Criteria
1.  The backend provides a service that can connect to and query the Loki API.
2.  All LogQL queries sent from the backend are automatically injected with the `tenant_id` label to enforce data isolation.
3.  A new API endpoint is created (e.g., `/api/v1/logs/query`) that proxies queries to Loki and returns the log streams.
4.  The endpoint is protected and requires a valid JWT.
5.  The new endpoint is documented in the API reference (Redocly).

## Tasks / Subtasks
- [ ] Task 1: Develop a backend service to connect and query the Loki API. (AC: #1)
- [ ] Task 2: Ensure all outgoing LogQL queries are injected with the `tenant_id` label. (AC: #2)
- [ ] Task 3: Create the `/api/v1/logs/query` endpoint to proxy queries to Loki. (AC: #3)
- [ ] Task 4: Secure the new endpoint, requiring a valid JWT. (AC: #4)
- [ ] Task 5: Document the new endpoint in the Redocly API reference. (AC: #5)

## Dev Notes
- The new Loki service should be located in `apps/backend/app/services/loki_service.py`.
- Use a standard HTTP client like `httpx` to query the Loki API.
- Similar to the Prometheus integration, the `tenant_id` from the JWT must be injected into every LogQL query to ensure data isolation.
- The Loki API endpoint URL should be configurable via environment variables.

### Testing
- Create integration tests for the `/api/v1/logs/query` endpoint.
- The tests should mock the Loki API.
- Test scenarios:
    - A valid LogQL query is correctly proxied with the `tenant_id` label.
    - A query from a user in one tenant does not return logs from another.
    - Malformed queries are handled gracefully.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-19 | 1.1 | Enriched with technical details. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 4. | Sarah (PO) |

## Dev Agent Record
*This section is for the development agent.*

## QA Results
*This section is for the QA agent.*
