---
Epic: 12
Story: 4
Title: End-to-End Integration and Validation
Status: Draft
---

# Story 12.4: `[SaaS]` End-to-End Integration and Validation

**As a** QA Engineer,
**I want** to test the entire data ingestion pipeline from end to end,
**so that** we can verify that the system is working correctly and securely.

## Acceptance Criteria

1.  A test script is created that uses an OpenTelemetry Collector to send sample logs, metrics, and traces to the public endpoint.
2.  An E2E test logs into the UI as the corresponding tenant.
3.  The test verifies that the sent metrics are queryable in the Metrics view.
4.  The test verifies that the sent traces are viewable in the Traces view.
5.  The test verifies that the sent logs are searchable in both the Logs view (Loki) and via an advanced search feature that queries OpenSearch.

## Dev Notes

### Previous Story Insights
-   This story validates the successful implementation of the entire Epic 12, including the infrastructure from **12.1**, the endpoint from **12.2**, and the consumer from **12.3**. It is the final quality gate for the data ingestion pipeline.

### System Architecture
-   The test will simulate the full **Push-Based Telemetry Ingestion** flow, starting from an external client and ending with data being queried in the UI.
-   This requires a test harness that can act as an external client sending OTLP data.
-   [Source: docs/architecture/high-level-architecture.md#push-based-telemetry-ingestion]

### File Locations
-   The E2E tests will be written using Playwright.
-   New test files should be created in the appropriate directory for E2E tests within the monorepo (e.g., a dedicated `e2e/` package or within the `frontend` app's test structure).
-   The test harness/script for the OTEL Collector can be located in a new `scripts/` or `testing/` directory at the root of the monorepo.
-   [Source: docs/architecture/source-tree.md]

### Testing Requirements
-   This story is purely focused on E2E testing.
-   The test must be fully automated and integrated into the CI/CD pipeline.
-   The test must create a new, temporary tenant for the test run to ensure isolation.
-   The test must clean up after itself, deleting any created resources.
-   The Playwright test will need to interact with the UI to confirm that the data sent by the test harness is visible.
-   [Source: docs/architecture/testing-strategy.md]

## Tasks / Subtasks

1.  **(AC: 1)** **Create Test Data Harness**
    *   Create a script and configuration for an OpenTelemetry Collector that can be run locally or in CI.
    *   The collector should be configured to send a predefined set of logs, metrics, and traces to the public ingestion endpoint.
    *   The script should be able to dynamically target the endpoint and use an auth token for a specific tenant.

2.  **(AC: 2)** **Develop E2E Test Scaffolding**
    *   Create a new Playwright test file for `ingestion-validation.spec.ts`.
    *   Implement `beforeAll` logic to programmatically create a new tenant and get an auth token for the test run.
    *   Implement `afterAll` logic to clean up the created tenant and its data.

3.  **(AC: 2, 3, 4, 5)** **Implement E2E Test Logic**
    *   In the test, execute the test data harness script to send data for the newly created tenant.
    *   Use Playwright to log in to the Obstack UI as a user from the test tenant.
    *   Navigate to the "Metrics" view and create a query that should return the sample metric data. Assert that the data is visible.
    *   Navigate to the "Traces" view, search for the sample trace ID, and assert that the trace waterfall is displayed.
    *   Navigate to the "Logs" view, search for the sample log message, and assert that it is visible (validating the Loki path).
    *   (If an advanced search UI exists) Use the advanced search to find the same log message and assert that it is visible (validating the OpenSearch path).

4.  **CI Integration**
    *   Integrate the new E2E test into the GitHub Actions workflow.
    *   Ensure the test runs on every pull request to the `main` branch.
