# Story 6.1: Backend Alert Ingestion

## Status
- Approved

## Story
- **As a** Backend Developer,
- **I want** to create a webhook endpoint that can receive alerts from Prometheus Alertmanager,
- **so that** we can ingest alerts into the Obstack platform.

## Acceptance Criteria
1.  A new API endpoint is created (e.g., `/api/v1/alerts/webhook/alertmanager`) that accepts POST requests with the Alertmanager webhook format.
2.  The backend service parses the incoming alert data and stores it in a structured format in the PostgreSQL `alerts` table.
3.  All incoming alerts are automatically tagged with the correct `tenant_id` based on a unique identifier in the webhook URL or payload.
4.  The endpoint handles alert grouping and deduplication.
5.  The webhook is documented in the API reference (Redocly) and the Docusaurus developer guide.

## Tasks / Subtasks
- [ ] Task 1: Create the `/api/v1/alerts/webhook/alertmanager` endpoint. (AC: #1)
- [ ] Task 2: Implement parsing and storing of Alertmanager data into the `alerts` table. (AC: #2)
- [ ] Task 3: Ensure incoming alerts are automatically tagged with the correct `tenant_id`. (AC: #3)
- [ ] Task 4: Implement alert grouping and deduplication logic. (AC: #4)
- [ ] Task 5: Document the webhook in Redocly and the Docusaurus developer guide. (AC: #5)

## Dev Notes
- A new Pydantic model will be needed in `apps/backend/app/models/` to represent the Alertmanager webhook payload.
- A new `alerts` table schema will need to be created via an Alembic migration. It should include columns for status, severity, summary, source, and a JSONB column for the full payload.
- The `tenant_id` could be passed as a query parameter in the webhook URL for simplicity (e.g., `/api/v1/alerts/webhook/alertmanager?tenant_id=...`).

### Testing
- Integration tests for the webhook endpoint are essential.
- The tests should send sample Alertmanager payloads to the endpoint and verify that the alerts are correctly created in the database.
- Test the deduplication logic to ensure that repeated alerts for the same issue do not create new database entries but update the existing one.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-19 | 1.1 | Enriched with technical details. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 6. | Sarah (PO) |

## Dev Agent Record
*This section is for the development agent.*

## QA Results
*This section is for the QA agent.*
