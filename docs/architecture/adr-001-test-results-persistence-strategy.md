# ADR-001: Test Results Persistence Strategy

**Status:** Accepted

**Date:** 2025-08-22

## Context

The project requires a robust, scalable test environment as defined in Epic 9. While the initial implementation provides a fully ephemeral environment (including a transient database for test results), there is a clear, long-term need to analyze test results over time. This requires a mechanism to persist test run data without compromising the integrity and isolation of the ephemeral test environment.

The key challenge is to balance the need for historical test data (for trend analysis, flakiness detection, etc.) with the core architectural principle of maintaining a simple, stateless, and perfectly reproducible test environment for CI/CD runs.

## Decision Drivers

*   **Test Isolation:** Each test run must occur in a pristine environment, with no possibility of data from previous runs influencing the outcome.
*   **Historical Analysis:** The ability to store, query, and analyze test results from all runs (CI and local) over time is a critical long-term requirement for quality assurance.
*   **Security:** The test environment should not require long-term credentials to external systems, minimizing the attack surface.
*   **Simplicity & Portability:** The core test environment should remain simple to run locally for developers and be highly portable.
*   **Decoupling:** The test execution environment should be decoupled from the test analysis and storage infrastructure.

## Considered Options

### Option 1: Fully Persistent Test Results Database

*   The `test-results-db` is removed from the Docker Compose setup and managed as a separate, long-running piece of infrastructure (e.g., a dedicated cloud database).
*   **Pros:** Centralized, simple to query with standard SQL tools.
*   **Cons:** Breaks the fully ephemeral nature of the test environment, introduces a hard dependency on an external service, requires the test environment to have persistent credentials, and creates a risk of state from one test run interfering with another.

### Option 2: Ephemeral DB with In-Process Export Service

*   The test environment remains fully ephemeral. A new service (`results-exporter`) is added to the Docker Compose file. After tests complete, this service queries the local `test-results-db`, serializes the data, and uploads it to a persistent object store (e.g., S3/MinIO).
*   **Pros:** Preserves test isolation.
*   **Cons:** Increases the complexity of the Docker Compose environment and requires the test environment to be configured with credentials for the object store.

### Option 3: Ephemeral DB with CI/CD-Managed Artifact Export (The Chosen Option)

*   The test environment's sole responsibility is to run tests and generate a results file within its local filesystem (e.g., `/app/reports/test-run-results.json`).
*   The CI/CD pipeline is responsible for orchestrating the process:
    1.  Start the ephemeral test environment.
    2.  Execute the tests.
    3.  After the environment shuts down, treat the generated results file as a build artifact.
    4.  A subsequent, separate step in the CI/CD pipeline uploads this artifact to a persistent object store.
*   **Pros:**
    *   **Perfect Separation of Concerns:** The test environment is a pure "black box" with no knowledge of the outside world. The CI/CD pipeline handles all orchestration and external communication.
    *   **Enhanced Security:** The test environment itself needs zero cloud credentials, drastically reducing the security risk.
    *   **Maximum Portability:** Developers can run the exact same process locally to generate the same results file for inspection.
*   **Cons:** Requires slightly more complex CI/CD pipeline configuration.

## Decision

We have decided to adopt **Option 3: Ephemeral DB with CI/CD-Managed Artifact Export**.

This approach provides the best balance of all our decision drivers. It maintains the architectural purity and isolation of the ephemeral test environment while leveraging the CI/CD system for its core strength: orchestrating workflows and managing artifacts. This pattern is the most secure, decoupled, and portable solution.

## Consequences

*   A new story will be created for a future sprint to implement this pattern. The acceptance criteria will include:
    1.  Creating a script to dump the contents of the local `test-results-db` to a standardized JSON file in the `/app/reports` directory.
    2.  Integrating this script into the end of the `run-all-tests.sh` entrypoint.
    3.  Updating the CI/CD pipeline to add a step that archives this JSON file to the project's designated MinIO/S3 bucket after each successful test run.
*   The core `docker-compose.test.yml` will remain simple and focused on its primary task of running the test suite.
*   The long-term test analysis strategy will be based on processing these JSON artifacts from the object store, not on querying a live relational database.
