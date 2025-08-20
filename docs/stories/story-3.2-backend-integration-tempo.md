# Story 3.2: Backend Integration with Tempo

## Status
- Approved

## Story
- **As a** Backend Developer,
- **I want** the backend to query a Tempo instance for trace data,
- **so that** we can securely serve distributed traces to the frontend.

## Acceptance Criteria
1.  The backend provides a service that can connect to and query the Tempo API.
2.  All Tempo queries are secured by tenant context.
3.  A new API endpoint is created (e.g., `/api/v1/traces/{trace_id}`) that retrieves a specific trace from Tempo.
4.  The endpoint is protected and requires a valid JWT.
5.  The new endpoint is documented in the API reference (Redocly).

## Tasks / Subtasks
- [ ] Task 1: Develop a backend service to connect and query the Tempo API. (AC: #1)
- [ ] Task 2: Ensure all Tempo queries are secured by tenant context. (AC: #2)
- [ ] Task 3: Create the `/api/v1/traces/{trace_id}` endpoint to retrieve a specific trace. (AC: #3)
- [ ] Task 4: Secure the new endpoint, requiring a valid JWT. (AC: #4)
- [ ] Task 5: Document the new endpoint in the Redocly API reference. (AC: #5)

## Dev Notes
- The new Tempo service should be located in `apps/backend/app/services/tempo_service.py`.
- Use a standard HTTP client like `httpx` to query the Tempo API.
- Tenant isolation for traces is critical. The `tenant_id` from the JWT must be used to ensure that the trace being queried belongs to the correct tenant. This may involve checking tags on the trace data itself.
- The Tempo API endpoint URL should be configurable via environment variables.

### Testing
- Create integration tests for the `/api/v1/traces/{trace_id}` endpoint.
- The tests should mock the Tempo API.
- Test scenarios:
    - A valid trace ID returns the correct trace data.
    - A user from Tenant A is denied access when requesting a trace belonging to Tenant B.
    - An invalid trace ID returns a 404 error.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-19 | 1.1 | Enriched with technical details. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 3. | Sarah (PO) |

## Dev Agent Record
*This section is for the development agent.*

## QA Results
*This section is for the QA agent.*
