# Story 4.2: Frontend UI for Log Search and Visualization

## Status
- Approved

## Story
- **As a** developer,
- **I want** to search and filter logs using a powerful query interface,
- **so that** I can quickly find the information I need to debug issues.

## Acceptance Criteria
1.  A new "Logs" view is created in the frontend application.
2.  The UI includes a LogQL input field and label/facet filters that send requests to the backend's log endpoint.
3.  The UI displays log lines in a clear, readable format, with color-coding for different log levels.
4.  The view includes the global time-range selector and supports "live-tailing" of logs.
5.  The Logs view is documented in the Docusaurus user guide.

## Tasks / Subtasks
- [ ] Task 1: Create the new "Logs" view in the frontend application. (AC: #1)
- [ ] Task 2: Implement a LogQL input field and label/facet filters. (AC: #2)
- [ ] Task 3: Display log lines with clear formatting and color-coding. (AC: #3)
- [ ] Task 4: Integrate the global time-range selector and live-tailing functionality. (AC: #4)
- [ ] Task 5: Document the new Logs view in the Docusaurus user guide. (AC: #5)

## Dev Notes
- The new "Logs" view should be a new page component in `apps/frontend/src/pages/LogsPage.tsx`.
- The LogQL input field should have syntax highlighting. Consider using a library like `CodeMirror`.
- Live-tailing can be implemented using a WebSocket connection or by polling the API endpoint every few seconds.
- Use **TanStack Query** for managing the log data fetching and caching.

### Testing
- Component tests for the log display and filtering UI.
- E2E tests should cover:
    - Entering a LogQL query and verifying the correct logs are displayed.
    - Using the time-range selector to filter logs.
    - Verifying that the live-tailing feature displays new logs as they arrive.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-19 | 1.1 | Enriched with technical details. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 4. | Sarah (PO) |

## Dev Agent Record
*This section is for the development agent.*

## QA Results
*This section is for the QA agent.*
