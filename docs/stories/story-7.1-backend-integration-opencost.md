# Story 7.1: Backend Integration with OpenCost

## Status
- Approved

## Story
- **As a** Backend Developer,
- **I want** the backend to query the OpenCost API for Kubernetes cost data,
- **so that** we can expose cost allocation metrics to the frontend.

## Acceptance Criteria
1.  A new backend service is created to communicate with the OpenCost API.
2.  The service can query for cost data and aggregate it by namespace, workload, and other labels.
3.  All queries to OpenCost are tenant-aware.
4.  A new API endpoint is created (e.g., `/api/v1/costs/current`) to serve basic, current cost data.
5.  The new endpoint is protected, tenant-isolated, and documented in Redocly.

## Tasks / Subtasks
- [ ] Task 1: Create a new backend service to communicate with the OpenCost API. (AC: #1)
- [ ] Task 2: Implement cost data querying and aggregation by namespace, workload, etc. (AC: #2)
- [ ] Task 3: Ensure all queries to OpenCost are tenant-aware. (AC: #3)
- [ ] Task 4: Create the `/api/v1/costs/current` endpoint. (AC: #4)
- [ ] Task 5: Secure the endpoint and document it in Redocly. (AC: #5)

## Dev Notes
- The new OpenCost service should be located in `apps/backend/app/services/opencost_service.py`.
- Tenant awareness will be achieved by mapping the `tenant_id` to specific Kubernetes namespaces. This mapping will need to be stored in the database.
- The OpenCost API endpoint should be configurable via environment variables.

### Testing
- Integration tests for the OpenCost service and the new API endpoint.
- Mock the OpenCost API to return sample cost data.
- Test the tenant-to-namespace mapping to ensure that the cost data is correctly filtered.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-19 | 1.1 | Enriched with technical details. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 7. | Sarah (PO) |

## Dev Agent Record
*This section is for the development agent.*

## QA Results
*This section is for the QA agent.*
