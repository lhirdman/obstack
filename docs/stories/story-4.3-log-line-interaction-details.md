# Story 4.3: Log Line Interaction and Details

## Status
- Approved

## Story
- **As a** developer,
- **I want** to expand log lines to see detailed metadata,
- **so that** I can get the full context for a specific log event.

## Acceptance Criteria
1.  Each log line in the UI is expandable.
2.  When expanded, the UI displays all labels and parsed fields associated with the log line.
3.  Users can easily add labels or fields from the detail view to the current query to refine their search.
4.  The UI provides an easy way to copy the full log message and its metadata.

## Tasks / Subtasks
- [ ] Task 1: Make each log line in the UI expandable. (AC: #1)
- [ ] Task 2: When expanded, display all associated labels and parsed fields. (AC: #2)
- [ ] Task 3: Implement functionality to add labels/fields from the detail view to the current query. (AC: #3)
- [ ] Task 4: Provide a UI element to easily copy the log message and metadata. (AC: #4)

## Dev Notes
- **Dependency:** This story builds on **Story 4.2**.
- This feature will be an enhancement to the "Logs" view component.
- The expanded view should display the log's labels and fields in a structured format, like a table or a definition list.
- The "add to query" functionality should intelligently append the selected label/field to the existing LogQL query in the input field.

### Testing
- Component tests for the expandable log line feature.
- Test that clicking a log line reveals the detailed metadata.
- Test the "add to query" functionality to ensure it correctly modifies the query string.
- Test the copy functionality.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-19 | 1.1 | Enriched with technical details. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 4. | Sarah (PO) |

## Dev Agent Record
*This section is for the development agent.*

## QA Results
*This section is for the QA agent.*
