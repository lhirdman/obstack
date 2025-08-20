# Story 6.2: Alert Management API

## Status
- Approved

## Story
- **As a** Backend Developer,
- **I want** to provide API endpoints for viewing and managing alerts,
- **so that** the frontend can display and interact with alert data.

## Acceptance Criteria
1.  A GET endpoint (`/api/v1/alerts`) is created to list all active alerts for a user's tenant, with support for filtering and sorting.
2.  A POST endpoint (e.g., `/api/v1/alerts/{alert_id}/status`) is created to allow users to change the status of an alert (e.g., to "Acknowledged" or "Resolved").
3.  The API enforces that users can only view or modify alerts belonging to their tenant.
4.  The endpoints are protected and require a valid JWT.
5.  All endpoints are documented in Redocly.

## Tasks / Subtasks
- [ ] Task 1: Create the GET `/api/v1/alerts` endpoint with filtering and sorting. (AC: #1)
- [ ] Task 2: Create the POST `/api/v1/alerts/{alert_id}/status` endpoint to change alert status. (AC: #2)
- [ ] Task 3: Enforce tenant-based access control on all alert endpoints. (AC: #3)
- [ ] Task 4: Secure all endpoints with JWT validation. (AC: #4)
- [ ] Task 5: Document all new endpoints in Redocly. (AC: #5)

## Dev Notes
- The new alert management endpoints should be located in `apps/backend/app/api/v1/alerts.py`.
- The filtering logic for the GET endpoint should support parameters like `status`, `severity`, and a date range.
- The status change endpoint should validate the new status to ensure it's a valid transition (e.g., an alert can't go from "Resolved" back to "Firing").

### Testing
- Integration tests for all new endpoints.
- Test the filtering and sorting functionality of the GET endpoint.
- Test the tenant isolation to ensure a user from Tenant A cannot see or modify alerts from Tenant B.
- Test the status change logic, including invalid status transitions.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-19 | 1.1 | Enriched with technical details. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 6. | Sarah (PO) |

## Dev Agent Record
*This section is for the development agent.*

## QA Results
*This section is for the QA agent.*
