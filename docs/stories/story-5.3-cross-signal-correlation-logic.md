# Story 5.3: Cross-Signal Correlation Logic

## Status
- Approved

## Story
- **As a** developer debugging an issue,
- **I want** to be able to jump from a specific trace to the logs and metrics related to it,
- **so that** I can correlate different signals to find the root cause of a problem faster.

## Acceptance Criteria
1.  When viewing a trace in the "Traces" view, the UI displays a "View related logs" button if a `trace_id` is present in the span's metadata.
2.  Clicking this button navigates the user to the "Logs" view with a pre-filled query (e.g., `{tenant_id="...", trace_id="..."}`).
3.  Similarly, when viewing a log that contains a `trace_id`, the UI provides a direct link to view that trace in the "Traces" view.
4.  Backend services are enhanced to efficiently query for related signals (e.g., an endpoint to find logs for a given trace ID).
5.  This correlation workflow is documented with a guide in Docusaurus.

## Tasks / Subtasks
- [ ] Task 1: In the "Traces" view, display a "View related logs" button when a `trace_id` is available. (AC: #1)
- [ ] Task 2: Implement the navigation to the "Logs" view with a pre-filled query. (AC: #2)
- [ ] Task 3: In the "Logs" view, provide a direct link to a trace if a `trace_id` is present. (AC: #3)
- [ ] Task 4: Enhance backend services to efficiently query for related signals by `trace_id`. (AC: #4)
- [ ] Task 5: Document the cross-signal correlation workflow in Docusaurus. (AC: #5)

## Dev Notes
- This story involves enhancements to both the "Traces" and "Logs" views on the frontend.
- The backend will need a new endpoint, such as `/api/v1/logs/by_trace/{trace_id}`, to support this feature efficiently.
- The frontend should use URL query parameters to pass the pre-filled query between the views.

### Testing
- E2E tests are the best way to validate this cross-navigation feature.
- The test should:
    1. Navigate to a trace view.
    2. Click the "View related logs" button.
    3. Verify that the user is on the Logs view and the query input contains the correct `trace_id`.
    4. Navigate to a log line with a `trace_id`.
    5. Click the link to the trace.
    6. Verify that the user is on the Traces view for the correct trace.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-19 | 1.1 | Enriched with technical details. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 5. | Sarah (PO) |

## Dev Agent Record
*This section is for the development agent.*

## QA Results
*This section is for the QA agent.*
