# Story 5.1: Backend Unified Search Service

## Status
- Approved

## Story
- **As a** Backend Developer,
- **I want** to create a unified search service that queries Loki, Prometheus, and Tempo simultaneously,
- **so that** I can provide a single entry point for all user search queries.

## Acceptance Criteria
1.  A new API endpoint is created (e.g., `/api/v1/search/unified`).
2.  The endpoint accepts a free-text query and a time range.
3.  The backend service dispatches parallel, tenant-aware queries to the Loki, Prometheus, and Tempo services.
4.  The service aggregates the results from all three sources into a single, structured JSON response, clearly identifying the source of each result.
5.  The new endpoint is fully documented in Redocly.

## Tasks / Subtasks
- [ ] Task 1: Create the new `/api/v1/search/unified` endpoint. (AC: #1, #2)
- [ ] Task 2: Implement logic to dispatch parallel, tenant-aware queries to Loki, Prometheus, and Tempo. (AC: #3)
- [ ] Task 3: Aggregate results from all sources into a single, structured response. (AC: #4)
- [ ] Task 4: Document the new endpoint in Redocly. (AC: #5)

## Dev Notes
- The new unified search service should be located in `apps/backend/app/services/unified_search_service.py`.
- Use Python's `asyncio` to run the queries to Loki, Prometheus, and Tempo in parallel for better performance.
- The response model should be clearly defined using Pydantic to ensure a consistent structure for the frontend.
- The free-text query will need to be translated into the appropriate query language for each backend (LogQL, PromQL, etc.). This may involve simple heuristics for now.

### Testing
- Integration tests for the `/api/v1/search/unified` endpoint.
- Mock the Loki, Prometheus, and Tempo services.
- Test that the service correctly aggregates results from all three sources.
- Test the tenant isolation to ensure a user cannot see search results from another tenant.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-19 | 1.1 | Enriched with technical details. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 5. | Sarah (PO) |

## Dev Agent Record
*This section is for the development agent.*

## QA Results
*This section is for the QA agent.*
