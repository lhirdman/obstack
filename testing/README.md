# ObservaStack Test Environment

This directory contains the complete test environment setup for ObservaStack, providing an isolated, ephemeral testing stack that mirrors the production environment.

## Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 8GB+ RAM available
- 20GB+ disk space

### Deploy Test Environment

```bash
# Start the full test stack
docker compose -f docker-compose.test.yml up -d --build

# Check service health
curl http://localhost:8081/health

# Run all tests
docker compose -f docker-compose.test.yml --profile test-execution up test-runner
```

## Architecture

The test environment extends the main ObservaStack application with specialized test services:

```
┌─────────────────────────────────────────────────────────────┐
│                    Test Network (172.20.0.0/16)            │
├─────────────────────────────────────────────────────────────┤
│  Core Application Services                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Frontend   │  │   Backend   │  │ PostgreSQL  │        │
│  │   :3000     │  │    :8000    │  │   :5432     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  Test-Specific Services                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │Test Runner  │  │Test Results │  │Health       │        │
│  │             │  │Database     │  │Monitor      │        │
│  │             │  │   :5433     │  │   :8080     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

## Services

### Core Application Services

- **Frontend** (`frontend:3000`): React application in test mode
- **Backend** (`backend:8000`): FastAPI application with test configurations
- **PostgreSQL** (`postgres:5432`): Main application database

### Test Services

- **Test Runner**: Executes all test suites (unit, integration, E2E, accessibility)
- **Test Results Database** (`test-results-db:5433`): Stores test outcomes and reports
- **Health Monitor** (`health-monitor:8080`): Monitors service health and provides status API

## Standard Commands

### Environment Lifecycle

```bash
# Start environment (build if needed)
docker compose -f docker-compose.test.yml up -d --build

# Check all services are healthy
docker compose -f docker-compose.test.yml ps
curl http://localhost:8081/health

# Stop environment
docker compose -f docker-compose.test.yml down

# Complete cleanup (removes volumes)
docker compose -f docker-compose.test.yml down -v
```

### Test Execution

```bash
# Run all tests
docker compose -f docker-compose.test.yml --profile test-execution up test-runner

# Run specific test types
docker compose -f docker-compose.test.yml exec test-runner pytest /app/backend-tests/unit/
docker compose -f docker-compose.test.yml exec test-runner npm run test:e2e
docker compose -f docker-compose.test.yml exec test-runner npx playwright test tests/accessibility/

# View test reports
docker compose -f docker-compose.test.yml exec test-runner ls -la /app/reports/
```

### Development Workflow

```bash
# Start environment for development
docker compose -f docker-compose.test.yml up -d

# Watch logs during development
docker compose -f docker-compose.test.yml logs -f

# Restart specific service after changes
docker compose -f docker-compose.test.yml restart backend
docker compose -f docker-compose.test.yml restart frontend

# Rebuild and restart service (useful after code changes)
docker compose -f docker-compose.test.yml up -d --build --no-deps --force-recreate backend
docker compose -f docker-compose.test.yml up -d --build --no-deps --force-recreate frontend

# Execute interactive shell in test runner
docker compose -f docker-compose.test.yml exec test-runner bash
```

### Monitoring and Debugging

```bash
# Check service health
curl http://localhost:8081/health | jq '.'

# View service logs
docker compose -f docker-compose.test.yml logs backend
docker compose -f docker-compose.test.yml logs health-monitor

# Access databases
# Main application database
docker compose -f docker-compose.test.yml exec postgres psql -U observastack -d observastack

# Keycloak authentication database
docker compose -f docker-compose.test.yml exec postgres psql -U keycloak -d keycloak

# Test results database
docker compose -f docker-compose.test.yml exec test-results-db psql -U test_user -d test_results

# Copy test reports to host
docker compose -f docker-compose.test.yml cp test-runner:/app/reports ./local-reports

# Test database setup
chmod +x scripts/test-db-setup.sh
./scripts/test-db-setup.sh
```

### Database Setup

The test environment automatically initializes multiple databases:

- **observastack**: Main application database with `observastack` user
- **keycloak**: Authentication database with `keycloak` user
- **test_results**: Test results database with `test_user`

The database initialization script ([`scripts/init-db.sql`](scripts/init-db.sql)) runs automatically when PostgreSQL starts and creates the required databases, users, and permissions.

To verify the database setup:
```bash
# Make the test script executable (first time only)
chmod +x scripts/test-db-setup.sh

# Run database setup verification
./scripts/test-db-setup.sh
```

## Configuration

### Environment Variables

Key configuration options:

| Variable | Service | Description | Default |
|----------|---------|-------------|---------|
| `NODE_ENV` | frontend | Node environment | `test` |
| `ENVIRONMENT` | backend | Application environment | `test` |
| `SERVICES_TO_MONITOR` | health-monitor | Comma-separated list of services to monitor | Auto-configured |
| `CHECK_INTERVAL` | health-monitor | Health check interval in seconds | `30` |

### Docker Profiles

Control which services run using profiles:

```bash
# Default: Core services + test infrastructure
docker compose -f docker-compose.test.yml up -d

# Include test execution
docker compose -f docker-compose.test.yml --profile test-execution up -d

# Include load testing tools
docker compose -f docker-compose.test.yml --profile load-testing up -d
```

### Network Configuration

All services run in an isolated network:
- **Network**: `observastack-test-network`
- **Subnet**: `172.20.0.0/16`
- **Driver**: `bridge`

## File Structure

```
testing/
├── docker-compose.test.yml          # Main test environment configuration
├── Dockerfile.test-runner           # Test runner container definition
├── Dockerfile.health-monitor        # Health monitor container definition
├── requirements.test.txt            # Python dependencies for test runner
├── requirements.health-monitor.txt  # Python dependencies for health monitor
├── package.test.json               # Node.js dependencies for test runner
├── scripts/                        # Test execution and database scripts
│   ├── run-all-tests.sh            # Main test execution script
│   ├── wait-for-services.sh        # Service readiness checker
│   ├── generate-report.py          # Test report generator
│   ├── init-db.sql                 # Database initialization script
│   └── test-db-setup.sh            # Database setup verification script
├── health-monitor/                 # Health monitor application
│   └── main.py                     # Health monitor service
└── README.md                       # This file
```

## Ephemeral Environment Principle

The test environment follows the **ephemeral, always-current** principle:

### Ephemeral Nature
- **Stateless**: No persistent state between test runs
- **Disposable**: Can be destroyed and recreated at any time
- **Isolated**: Completely separate from development and production environments
- **Clean Slate**: Each deployment starts with a fresh, known state

### Always-Current
- **Latest Code**: Always built from the current codebase
- **Fresh Dependencies**: Dependencies are pulled fresh on each build
- **Current Configuration**: Uses the latest configuration and environment settings
- **Up-to-date Tests**: Runs the most recent version of all test suites

### Benefits
- **Consistent Results**: Eliminates "works on my machine" issues
- **Reliable Testing**: No contamination from previous test runs
- **Easy Debugging**: Known starting state makes issues easier to reproduce
- **CI/CD Ready**: Perfect for automated testing pipelines

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Environment
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Start Test Environment
        run: |
          cd testing
          docker compose -f docker-compose.test.yml up -d --build
          
      - name: Wait for Services
        run: |
          cd testing
          timeout 300 bash -c 'until curl -f http://localhost:8081/health; do sleep 5; done'
          
      - name: Run Tests
        run: |
          cd testing
          docker compose -f docker-compose.test.yml --profile test-execution up --abort-on-container-exit test-runner
          
      - name: Collect Results
        if: always()
        run: |
          cd testing
          docker compose -f docker-compose.test.yml cp test-runner:/app/reports ./test-reports
          
      - name: Upload Test Results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: testing/test-reports/
          
      - name: Cleanup
        if: always()
        run: |
          cd testing
          docker compose -f docker-compose.test.yml down -v
```

## Troubleshooting

### Common Issues

**Services not starting:**
```bash
docker compose -f docker-compose.test.yml ps
docker compose -f docker-compose.test.yml logs
```

**Network connectivity issues:**
```bash
docker compose -f docker-compose.test.yml exec frontend ping backend
docker network ls | grep test
```

**Test failures:**
```bash
docker compose -f docker-compose.test.yml logs test-runner
docker compose -f docker-compose.test.yml exec test-runner cat /app/reports/test-report.html
```

**Performance issues:**
- Increase Docker memory allocation (8GB+ recommended)
- Use SSD storage for Docker volumes
- Close unnecessary applications to free up resources

### Getting Help

- Check the [Test Environment Documentation](../docs/docs/developer-guide/test-environment.md)
- Review the [Testing Strategy](../docs/architecture/testing-strategy.md)
- Open an issue in the project repository

## Contributing

When modifying the test environment:

1. **Test Changes**: Verify your changes work with a full environment rebuild
2. **Update Documentation**: Update this README and the developer guide
3. **Version Dependencies**: Pin dependency versions for reproducibility
4. **Test CI Integration**: Ensure changes work in CI/CD pipelines

For more information, see the [Contributing Guide](../docs/docs/developer-guide/contributing.md).