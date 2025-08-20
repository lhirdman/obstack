# Story 5.2: Frontend Unified Search Bar and Results UI

## Status
- Approved

## Story
- **As a** DevOps engineer,
- **I want** to use a single search bar on the main dashboard to query all my observability data at once,
- **so that** I can quickly find relevant information without knowing which tool to check first.

## Acceptance Criteria
1.  A prominent, unified search bar is added to the main dashboard or navigation header.
2.  When a user executes a search, the UI calls the new unified search endpoint.
3.  A new "Search Results" view is created that can display a heterogeneous list of results (logs, metrics, traces).
4.  Each result in the list is clearly marked with its type (e.g., with an icon and text) and links to the appropriate detailed view (e.g., the Logs view).
5.  The feature is documented in the Docusaurus user guide.

## Tasks / Subtasks
- [ ] Task 1: Add a prominent, unified search bar to the main dashboard/navigation header. (AC: #1)
- [ ] Task 2: Implement the UI logic to call the unified search endpoint. (AC: #2)
- [ ] Task 3: Create a "Search Results" view to display heterogeneous results. (AC: #3)
- [ ] Task 4: Ensure each result is clearly marked and links to its detailed view. (AC: #4)
- [ ] Task 5: Document the unified search feature in the Docusaurus user guide. (AC: #5)

## Dev Notes
- The unified search bar should be a reusable component placed in the main application layout.
- The "Search Results" page should be a new route and page component.
- Create distinct UI components for rendering log, metric, and trace search results within the results list.
- Use **TanStack Query** to handle the API call to the `/api/v1/search/unified` endpoint.

### Testing
- Component tests for the search bar and the different types of result components.
- E2E tests to cover the full user flow:
    - Typing a query into the search bar.
    - Navigating to the search results page.
    - Verifying that results of different types are displayed correctly.
    - Clicking a result and verifying the navigation to the correct detailed view.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-19 | 1.1 | Enriched with technical details. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 5. | Sarah (PO) |

## Dev Agent Record
*This section is for the development agent.*

## QA Results
*This section is for the QA agent.*
