# Story 3.4: Frontend UI for Trace Visualization

## Status
- Approved

## Story
- **As a** developer,
- **I want** to view distributed traces in a waterfall diagram,
- **so that** I can debug performance issues and understand service dependencies.

## Acceptance Criteria
1.  A new "Traces" view is created in the frontend.
2.  The UI allows users to search for traces by ID or other tags.
3.  When a trace is selected, the UI displays a detailed waterfall view of all spans.
4.  Each span in the waterfall is clickable and shows detailed metadata (tags, logs, etc.).
5.  The view is documented in the Docusaurus user guide.

## Tasks / Subtasks
- [ ] Task 1: Create the new "Traces" view in the frontend. (AC: #1)
- [ ] Task 2: Implement UI to search for traces by ID or other tags. (AC: #2)
- [ ] Task 3: Display a detailed waterfall view for selected traces. (AC: #3)
- [ ] Task 4: Make each span in the waterfall clickable to show detailed metadata. (AC: #4)
- [ ] Task 5: Document the new Traces view in the Docusaurus user guide. (AC: #5)

## Dev Notes
- The new "Traces" view should be a new page component in `apps/frontend/src/pages/TracesPage.tsx`.
- A dedicated UI component for rendering the waterfall diagram will be required. Consider using an existing library like `react-trace-viewer` or building a custom component using a charting library.
- The search functionality should query the backend's trace search endpoint (to be created in a future story). For now, searching by trace ID against the `/api/v1/traces/{trace_id}` endpoint is sufficient.
- Use **TanStack Query** for fetching trace data.

### Testing
- Component tests for the waterfall diagram are essential. Test with complex, nested trace data to ensure correct rendering.
- E2E tests should cover the workflow of searching for a trace ID and verifying that the waterfall diagram and span details are displayed correctly.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-19 | 1.1 | Enriched with technical details. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 3. | Sarah (PO) |

## Dev Agent Record
*This section is for the development agent.*

## QA Results
*This section is for the QA agent.*
