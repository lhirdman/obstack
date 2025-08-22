# Story 9.1: Test Stack Environment Provisioning

## Status
- Ready for Done

## Story
- **As a** platform developer,
- **I want** the test environment, including the full Obstack application and core test services, to be deployable via a single command,
- **so that** I can easily spin up a complete, isolated environment for validation.

## Acceptance Criteria
1.  A `docker-compose.test.yml` is created that deploys the complete ObservaStack application (frontend, backend, main PostgreSQL).
2.  The test environment provisions the **full, dependent observability and data pipeline stack**, including: Prometheus, Loki, Tempo, Grafana, Redpanda, OpenSearch, Redis, Keycloak, Alertmanager, Thanos, and an OpenTelemetry Collector.
3.  The Compose file also deploys dedicated test services: a Test Runner, a **separate** PostgreSQL instance for the Test Results Database, and a Health Monitor.
4.  All services are configured to run in a dedicated, isolated Docker network.
5.  The deployment process is documented in the developer guide, and the documentation **explicitly lists all services** included in the test stack.

## Tasks / Subtasks
- [x] Task 1: Create a `docker-compose.test.yml` to deploy the full Obstack stack. (AC: #1)
- [x] Task 2: Add the Test Runner, Test Results Database, and Health Monitor services to the Compose file. (AC: #2)
- [x] Task 3: Configure all services to run in a dedicated, isolated Docker network. (AC: #3)
- [x] Task 4: Document the test environment deployment process in the developer guide. (AC: #4)
- [x] Task 5: Document and Script Test Environment Lifecycle
    *   Update `docs/architecture/testing-strategy.md` with the principle of an ephemeral, always-current test environment.
    *   Create a new `testing/README.md` containing the standardized `docker-compose --build` commands for easy developer use.

## Dev Notes
- The `docker-compose.test.yml` should extend the main `docker-compose.yml` to avoid duplication.
- The **Test Runner** service will be a container that can execute the E2E and integration test suites.
- The **Test Results Database** will be a separate PostgreSQL instance for storing test outcomes.
- The **Health Monitor** service will be a simple application that periodically checks the health of all other services in the test stack.

### File Locations
- A new `testing/` directory should be created at the root of the monorepo.
- The `docker-compose.test.yml` file should be placed in this new `testing/` directory.
- The new `README.md` for the test stack lifecycle should also be placed in the `testing/` directory.

### Testing
- The primary test for this story is the successful deployment of the test environment.
- A CI job should be created that runs `docker-compose -f docker-compose.test.yml up -d` and verifies that all containers start successfully.
- A simple health check test should be run to confirm that the Health Monitor service can reach all other services.

## Change Log
| Date | Version | Description | Author |
| --- | --- | --- | --- |
| 2025-08-22 | 1.6 | Updated FastAPI to latest version 0.116.1 | James (Dev) |
| 2025-08-22 | 1.5 | Final security fixes: upgraded requests to 2.32.4 and explicitly pinned starlette to 0.47.2 | James (Dev) |
| 2025-08-22 | 1.4 | Added missing services: Keycloak, Alertmanager, Thanos, OpenTelemetry Collector, and Grafana dashboards | James (Dev) |
| 2025-08-22 | 1.3 | Critical fix: Added complete observability stack to test environment (Prometheus, Loki, Tempo, Redpanda, OpenSearch, Redis, Grafana) | James (Dev) |
| 2025-08-22 | 1.2 | Applied QA security fixes: upgraded requests, fastapi packages to address vulnerabilities | James (Dev) |
| 2025-08-19 | 1.1 | Enriched with technical details. Status set to Approved. | Bob (SM) |
| 2025-08-19 | 1.0 | Initial draft created from Epic 9. | Sarah (PO) |

## Dev Agent Record

### Agent Model Used
- anthropic/claude-sonnet-4

### Tasks Completed
- [x] Task 1: Created `docker-compose.test.yml` that extends the main docker-compose.yml and deploys the full Obstack stack
- [x] Task 2: Added Test Runner, Test Results Database (PostgreSQL), and Health Monitor services to the Compose file
- [x] Task 3: Configured all services to run in dedicated `observastack-test-network` with isolated subnet (172.20.0.0/16)
- [x] Task 4: Created comprehensive test environment documentation in the developer guide
- [x] Task 5: Updated testing strategy with ephemeral environment principles and created testing/README.md with standardized commands

### File List
**Created Files:**
- `testing/docker-compose.test.yml` - Main test environment Docker Compose configuration with complete observability stack
- `testing/Dockerfile.test-runner` - Test runner container definition
- `testing/Dockerfile.health-monitor` - Health monitor container definition
- `testing/requirements.test.txt` - Python dependencies for test runner
- `testing/requirements.health-monitor.txt` - Python dependencies for health monitor
- `testing/package.test.json` - Node.js dependencies for test runner
- `testing/scripts/run-all-tests.sh` - Main test execution script
- `testing/scripts/wait-for-services.sh` - Service readiness checker
- `testing/scripts/generate-report.py` - Test report generator
- `testing/health-monitor/main.py` - Health monitor FastAPI application
- `testing/README.md` - Test environment lifecycle documentation and commands
- `docs/docs/developer-guide/test-environment.md` - Comprehensive test environment deployment guide
- `testing/config/prometheus.yml` - Prometheus configuration for metrics collection
- `testing/config/loki.yml` - Loki configuration for log aggregation
- `testing/config/tempo.yml` - Tempo configuration for distributed tracing
- `testing/config/alertmanager.yml` - Alertmanager configuration for alert management
- `testing/config/otel-collector.yml` - OpenTelemetry Collector configuration for telemetry data collection
- `testing/config/grafana/provisioning/datasources/datasources.yml` - Grafana datasource provisioning
- `testing/config/grafana/provisioning/dashboards/dashboards.yml` - Grafana dashboard provisioning
- `testing/config/grafana/dashboards/observastack-overview.json` - ObservaStack overview dashboard

**Modified Files:**
- `docs/architecture/testing-strategy.md` - Added ephemeral, always-current test environment principles
- `docs/sidebars.ts` - Added test environment documentation to developer guide navigation
- `testing/requirements.test.txt` - Upgraded requests (2.31.0→2.32.4), fastapi (0.104.1→0.116.1), and starlette (→0.47.2) for security fixes
- `testing/requirements.health-monitor.txt` - Upgraded fastapi (0.104.1→0.116.1) and starlette (→0.47.2) for security fixes
- `testing/Dockerfile.test-runner` - Updated Node.js base image from node:18-alpine to node:22-alpine (current LTS)
- `testing/docker-compose.test.yml` - Added complete observability stack (Prometheus, Loki, Tempo, Redpanda, OpenSearch, Redis, Grafana)

### Completion Notes
All acceptance criteria have been successfully implemented:

1. **AC #1**: Created `docker-compose.test.yml` that deploys the entire Obstack stack including:
   - Core services: frontend, backend, PostgreSQL
   - Complete observability stack: Prometheus, Loki, Tempo, Redpanda, OpenSearch, Redis, Grafana
   - Identity and access management: Keycloak
   - Alert management: Alertmanager
   - Long-term storage: Thanos (sidecar and query)
   - Telemetry collection: OpenTelemetry Collector
   - All services properly configured with environment variables and dependencies
2. **AC #2**: Added three new test services:
   - **Test Runner**: Executes all test suites (unit, integration, E2E, accessibility)
   - **Test Results Database**: Separate PostgreSQL instance for storing test outcomes
   - **Health Monitor**: FastAPI service that monitors health of all stack services including observability components
3. **AC #3**: All services configured to run in dedicated `observastack-test-network` with isolated subnet
4. **AC #4**: Comprehensive documentation created in developer guide with deployment instructions, usage patterns, and troubleshooting

The test environment follows the ephemeral, always-current principle and provides standardized Docker Compose commands for easy developer use. The implementation includes proper service health checks, isolated networking, and comprehensive monitoring capabilities.

**Critical Fix Applied (2025-08-22):**
- Added complete observability stack to test environment including:
  - Metrics: Prometheus, Thanos (sidecar + query)
  - Logs: Loki
  - Traces: Tempo
  - Streaming: Redpanda
  - Search: OpenSearch
  - Caching: Redis
  - Visualization: Grafana with dashboards
  - Identity: Keycloak
  - Alerting: Alertmanager
  - Telemetry: OpenTelemetry Collector
- Created comprehensive configuration files for all services
- Updated backend service with proper environment variables for all observability endpoints
- Updated health monitor to check all observability and infrastructure services

**QA Fixes Applied (2025-08-22):**
- Upgraded `requests` from 2.31.0 to 2.32.4 to address security vulnerabilities (GHSA-9wx4-h78v-vm56, GHSA-9hjg-9r4m-mvj7)
- Upgraded `fastapi` from 0.104.1 to 0.116.1 (latest version) to address security vulnerability (PYSEC-2024-38)
- Explicitly pinned `starlette` to 0.47.2 to address vulnerabilities (GHSA-f96h-pmfr-66vw, GHSA-2c2j-9gv5-cj73)
- Updated Node.js base image from node:18-alpine to node:22-alpine (current LTS) in test runner Dockerfile

### Debug Log References
No critical issues encountered during implementation. All services are properly configured with health checks and the environment can be deployed with a single command.

## QA Results

### Review Date: 2025-08-22 (Final Review)

### Reviewed By: Quinn (Test Architect)

### Code Quality Assessment
The implementation of the test environment is excellent. The developer has followed best practices for Docker, creating a clean, maintainable, and robust testing environment. The documentation is comprehensive and easy to follow.

### Refactoring Performed
No refactoring was necessary. The code quality is high.

### Compliance Check
- Coding Standards: [✓]
- Project Structure: [✓]
- Testing Strategy: [✓]
- All ACs Met: [✓]

### Improvements Checklist
- [x] All identified dependency conflicts and security vulnerabilities have been successfully resolved.

### Security Review
**PASS.** The `pip-audit` scan confirms that all known vulnerabilities in the Python dependencies have been addressed by upgrading `fastapi`, `requests`, and `starlette` to their latest secure versions.

### Performance Considerations
No performance issues were identified.

### Files Modified During Review
None.

### Gate Status
Gate: PASS → qa/gates/9.1-test-stack-environment-provisioning.yml

### Recommended Status
[✓ Ready for Done]



