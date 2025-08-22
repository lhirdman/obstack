# Testing Strategy

Our testing strategy is designed to ensure application quality, reliability, and performance by catching bugs early and preventing regressions. We will follow the principles of the Testing Pyramid, emphasizing a strong foundation of fast, isolated unit tests, supported by broader integration and end-to-end tests.

## Testing Pyramid

We will adhere to a standard testing pyramid model:
-   **Unit Tests (Base):** The majority of our tests. They are fast, reliable, and verify the smallest pieces of our application in isolation.
-   **Integration Tests (Middle):** These tests will verify the interactions between different components, services, or modules (e.g., an API endpoint connecting to a database).
-   **End-to-End (E2E) Tests (Top):** A smaller number of E2E tests will simulate real user workflows from the browser to the database, ensuring the entire system works together as expected.

## Test Types, Tooling, and Scope

| Test Type | Tooling | Scope & Purpose |
|---|---|---|
| **Unit Tests** | Vitest (Frontend), Pytest (Backend) | Test individual functions, components, or classes in isolation. All external dependencies (e.g., APIs, databases) will be mocked. |
| **Integration Tests** | Pytest, Docker Compose | Test the interaction between backend services, such as an API endpoint and a real test database, to validate data integrity and contracts. |
| **End-to-End (E2E) Tests** | Playwright | Test critical user workflows across the entire application stack (frontend to backend to database) in a production-like environment. |
| **Load & Performance** | k6 / Locust | Assess system performance, scalability, and reliability under heavy load to identify bottlenecks. |
| **Chaos Engineering** | Chaos Mesh | Proactively test system resilience by injecting failures (e.g., network latency, pod failures) into the test environment. |

## Accessibility Testing

To ensure the application is usable by everyone, including people with disabilities, we will integrate accessibility testing into our workflow.

-   **Automated Testing**: We will use the **`@axe-core/playwright`** library to integrate automated accessibility checks into our Playwright E2E test suite. This will run on every pull request and fail the build if any WCAG 2.1 AA violations are detected.
-   **Manual Testing**: As part of the development process for any new UI feature, developers are expected to perform the following manual checks:
    -   **Keyboard Navigation**: Can all interactive elements be reached and operated using only the keyboard? Is the focus order logical?
    -   **Screen Reader**: Does the page read logically with a screen reader (e.g., VoiceOver, NVDA)? Are all images and controls properly labeled?

## Test Environment Strategy

### Ephemeral, Always-Current Test Environment

Our test environment follows the **ephemeral, always-current** principle to ensure reliable, consistent testing:

#### Ephemeral Nature
- **Stateless**: No persistent state between test runs
- **Disposable**: Can be destroyed and recreated at any time
- **Isolated**: Completely separate from development and production environments
- **Clean Slate**: Each deployment starts with a fresh, known state

#### Always-Current
- **Latest Code**: Always built from the current codebase
- **Fresh Dependencies**: Dependencies are pulled fresh on each build
- **Current Configuration**: Uses the latest configuration and environment settings
- **Up-to-date Tests**: Runs the most recent version of all test suites

#### Benefits
- **Consistent Results**: Eliminates "works on my machine" issues
- **Reliable Testing**: No contamination from previous test runs
- **Easy Debugging**: Known starting state makes issues easier to reproduce
- **CI/CD Ready**: Perfect for automated testing pipelines

### Test Environment Deployment

The complete test environment is deployed using Docker Compose and includes:

- **Core Application Services**: Frontend, Backend, PostgreSQL
- **Test-Specific Services**: Test Runner, Test Results Database, Health Monitor
- **Isolated Network**: Dedicated Docker network for complete isolation
- **Standardized Commands**: Consistent `docker-compose --build` commands for easy developer use

For detailed deployment instructions, see the [Test Environment Guide](../docs/developer-guide/test-environment.md).

### Test Results Persistence

To maintain the ephemeral and isolated nature of our test environment, test results are not stored in a long-term database directly from the test run. Instead, the test runner's final step is to export the complete results of the run into a standardized JSON artifact.

This artifact is then handled by the CI/CD pipeline, which uploads it to a persistent object store (MinIO/S3) for long-term storage and historical analysis. This approach decouples test execution from results storage, enhances security, and ensures perfect reproducibility.

For the detailed rationale behind this decision, see **[ADR-001: Test Results Persistence Strategy](./adr-001-test-results-persistence-strategy.md)**.

## Continuous Testing Workflow

Testing is an integral part of our CI/CD pipeline to provide rapid feedback.
-   **On Every Commit:** All unit and integration tests will be automatically executed.
-   **On Pull Request to `main`:** The full test suite (Unit, Integration, E2E, Accessibility) will run in the ephemeral test environment.
-   **Post-Deployment:** E2E and accessibility tests will run against the staging environment to verify deployment health.
-   **Test Environment Lifecycle:** Each test run uses a fresh, ephemeral environment that is created, used, and destroyed automatically.
