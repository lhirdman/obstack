# Story 9.5: Standardize Test Results as a CI/CD Artifact

## Status
- Approved

## Story
- **As a** development team,
- **I want** to export test run results as a JSON artifact and have the CI/CD pipeline upload it to persistent storage,
- **so that** we can perform historical analysis without compromising the ephemeral nature of the test environment.

## Acceptance Criteria
1.  A new script (`export-results.py`) is created in the `testing/scripts/` directory.
2.  The script can connect to the local `test-results-db`, query all data from the test run, and serialize it into a single, structured JSON file (e.g., `/app/reports/test-run-results.json`).
3.  The main test execution script (`run-all-tests.sh`) is modified to execute the `export-results.py` script as its final step.
4.  The CI/CD pipeline configuration (e.g., `.github/workflows/`) is updated to include a new step that archives the `test-run-results.json` artifact to a persistent object store (MinIO/S3) after the test execution step completes.
5.  The documentation in `testing/README.md` is updated to describe this new artifact export process.

## Tasks / Subtasks
- [ ] Task 1: Create `export-results.py` script to query and serialize test data to JSON.
- [ ] Task 2: Integrate the export script into `run-all-tests.sh`.
- [ ] Task 3: Update the CI/CD workflow to upload the JSON artifact to the object store.
- [ ] Task 4: Update `testing/README.md` with details on the new process.

## Dev Notes
- This story implements the decision formally captured in **ADR-001: Test Results Persistence Strategy**. The ADR should be consulted for full context.
- The goal is to completely decouple the test environment from the persistent storage. The test environment should have no knowledge of or credentials for the S3 bucket.
- The JSON export should be a well-structured, denormalized document containing all relevant information for a single test run (suites, cases, steps, timings, status, etc.).
- **Error Handling:** The main CI/CD job should fail if the test results artifact cannot be successfully generated or uploaded. This ensures the integrity of our historical test data.

### Testing
- **Local Verification:** Run the test environment locally using the `docker compose` commands. After the test run completes, verify that the `test-run-results.json` file is created in the `testing/reports` directory and that its content is well-formed.
- **CI/CD Verification:** Create a test branch and push a commit to trigger the updated CI/CD workflow. Verify that the new "Upload Test Artifact" step executes and succeeds.
- **Artifact Validation:** Manually download the `test-run-results.json` file from the S3/MinIO bucket and inspect it to confirm its structure and content are correct and match the results of the test run.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-22 | 1.0 | Initial draft created from ADR-001. | Sarah (PO) |
