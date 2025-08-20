# Story 3.3: Frontend UI for Metrics Visualization

## Status
- Approved

## Story
- **As a** DevOps engineer,
- **I want** to visualize metrics from my services in the Obstack UI,
- **so that** I can monitor the health and performance of my applications.

## Acceptance Criteria
1.  A new "Metrics" view is created in the frontend application.
2.  The UI includes a query builder or raw PromQL input field that sends requests to the backend's metrics endpoint.
3.  The UI uses a charting library (e.g., embedding Grafana panels or using a library like Apache ECharts) to render the time-series data returned by the API.
4.  The view includes the global time-range selector.
5.  A user guide for the Metrics view is added to the Docusaurus site.

## Tasks / Subtasks
- [ ] Task 1: Create the new "Metrics" view in the frontend application. (AC: #1)
- [ ] Task 2: Implement a query builder/input field for sending requests to the backend. (AC: #2)
- [ ] Task 3: Integrate a charting library to render time-series data. (AC: #3)
- [ ] Task 4: Ensure the global time-range selector is included in the view. (AC: #4)
- [ ] Task 5: Add a user guide for the new Metrics view to the Docusaurus site. (AC: #5)

## Dev Notes
- The new "Metrics" view should be a new page component in `apps/frontend/src/pages/MetricsPage.tsx`.
- Use **TanStack Query** to fetch data from the `/api/v1/metrics/query` endpoint.
- For the charting library, **Apache ECharts** is the recommended choice as per the architecture. Create a reusable chart component.
- The global time-range selector should be a shared component that can be used across different views.

### Testing
- Create component tests for the new Metrics view using **Vitest** and **React Testing Library**.
- Mock the backend API to test the chart rendering with sample time-series data.
- E2E tests using **Playwright** should cover the user flow of entering a query, executing it, and seeing a chart render on the page.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-19 | 1.1 | Enriched with technical details. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 3. | Sarah (PO) |

## Dev Agent Record
*This section is for the development agent.*

## QA Results
*This section is for the QA agent.*
