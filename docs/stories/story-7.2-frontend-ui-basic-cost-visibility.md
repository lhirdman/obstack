# Story 7.2: Frontend UI for Basic Cost Visibility

## Status
- Approved

## Story
- **As a** platform operator,
- **I want** to see a dashboard showing my current Kubernetes costs broken down by namespace,
- **so that** I can understand where my cloud spend is going.

## Acceptance Criteria
1.  A new "Cost Insights" view is created in the frontend.
2.  The UI displays a dashboard with visualizations (e.g., pie charts, bar charts) of current cost data from the backend.
3.  The dashboard provides a breakdown of costs by namespace and workload type.
4.  The feature is available to all tiers.
5.  The basic dashboard is documented in the Docusaurus user guide.

## Tasks / Subtasks
- [ ] Task 1: Create the new "Cost Insights" view in the frontend. (AC: #1)
- [ ] Task 2: Implement dashboard visualizations for current cost data. (AC: #2)
- [ ] Task 3: Provide cost breakdowns by namespace and workload type. (AC: #3)
- [ ] Task 4: Ensure the feature is available to all tiers. (AC: #4)
- [ ] Task 5: Document the basic dashboard in the Docusaurus user guide. (AC: #5)

## Dev Notes
- The new "Cost Insights" view should be a new page component in `apps/frontend/src/pages/CostInsightsPage.tsx`.
- Use **Apache ECharts** for the visualizations.
- The dashboard should be clean and easy to understand, focusing on the most important cost drivers.
- Use **TanStack Query** to fetch the data from the `/api/v1/costs/current` endpoint.

### Testing
- Component tests for the dashboard and its chart components.
- Mock the backend API to provide sample cost data for different namespaces and workloads.
- E2E tests to verify that the dashboard loads and displays the cost data correctly.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-19 | 1.1 | Enriched with technical details. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 7. | Sarah (PO) |

## Dev Agent Record
*This section is for the development agent.*

## QA Results
*This section is for the QA agent.*
