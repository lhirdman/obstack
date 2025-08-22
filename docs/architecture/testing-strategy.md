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

## Continuous Testing Workflow

Testing is an integral part of our CI/CD pipeline to provide rapid feedback.
-   **On Every Commit:** All unit and integration tests will be automatically executed.
-   **On Pull Request to `main`:** The full test suite (Unit, Integration, E2E, Accessibility) will run.
-   **Post-Deployment:** E2E and accessibility tests will run against the staging environment to verify deployment health.
