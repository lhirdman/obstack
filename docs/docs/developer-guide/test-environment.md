---
title: Test Environment
description: Guide to deploying and using the ObservaStack test environment
---

# Test Environment Deployment

The ObservaStack test environment provides a complete, isolated testing stack that includes the full application plus specialized test services. This guide covers deployment, usage, and management of the test environment.

## Overview

The test environment extends the main ObservaStack application with additional services specifically designed for testing:

- **Test Runner**: Executes E2E, integration, and unit tests
- **Test Results Database**: Stores test outcomes and reports
- **Health Monitor**: Monitors the health of all test stack services
- **Isolated Network**: Dedicated Docker network for test isolation

## Prerequisites

Before deploying the test environment, ensure you have:

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 8GB RAM available for containers
- At least 20GB disk space
- Network access for downloading container images

## Quick Start

### 1. Deploy the Test Environment

From the project root directory:

```bash
# Navigate to the testing directory
cd testing/

# Start the full test stack
docker compose -f docker-compose.test.yml up -d

# Verify all services are running
docker compose -f docker-compose.test.yml ps
```

### 2. Check Service Health

The health monitor provides real-time status of all services:

```bash
# Check overall health
curl http://localhost:8081/health

# Check specific service health
curl http://localhost:8081/health/frontend
curl http://localhost:8081/health/backend
```

### 3. Run Tests

Execute the complete test suite:

```bash
# Run all tests using the test-execution profile
docker compose -f docker-compose.test.yml --profile test-execution up test-runner

# View test reports
docker compose -f docker-compose.test.yml exec test-runner ls -la /app/reports/
```

## Service Architecture

### Core Application Services

The test environment includes all main application services with test-specific configurations:

- **Frontend** (`frontend:3000`): React application in test mode
- **Backend** (`backend:8000`): FastAPI application with test database connections
- **PostgreSQL** (`postgres:5432`): Main application database

### Test-Specific Services

#### Test Results Database (`test-results-db:5432`)

A dedicated PostgreSQL instance for storing test outcomes:

```yaml
Environment Variables:
- POSTGRES_DB=test_results
- POSTGRES_USER=test_user
- POSTGRES_PASSWORD=test_password
```

#### Test Runner (`test-runner`)

Containerized test execution environment that runs:

- Backend unit tests (pytest)
- Backend integration tests (pytest)
- Frontend unit tests (npm test)
- End-to-end tests (Playwright)
- Accessibility tests (@axe-core/playwright)

#### Health Monitor (`health-monitor:8080`)

Provides centralized health monitoring with endpoints:

- `GET /health` - Overall system health
- `GET /health/{service_name}` - Individual service health

## Network Configuration

All services run in an isolated Docker network:

```yaml
networks:
  test-network:
    name: observastack-test-network
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

This ensures complete isolation from other Docker environments and prevents port conflicts.

## Usage Patterns

### Development Testing

For ongoing development work:

```bash
# Start the environment
docker compose -f docker-compose.test.yml up -d

# Run specific test suites
docker compose -f docker-compose.test.yml exec test-runner pytest /app/backend-tests/unit/
docker compose -f docker-compose.test.yml exec test-runner npm run test:e2e

# View logs
docker compose -f docker-compose.test.yml logs -f test-runner
```

### CI/CD Integration

For automated testing in CI pipelines:

```bash
# Build and start services
docker compose -f docker-compose.test.yml up -d --build

# Wait for services to be ready
docker compose -f docker-compose.test.yml exec test-runner ./scripts/wait-for-services.sh

# Run all tests
docker compose -f docker-compose.test.yml --profile test-execution up --abort-on-container-exit test-runner

# Collect results
docker compose -f docker-compose.test.yml cp test-runner:/app/reports ./test-reports

# Cleanup
docker compose -f docker-compose.test.yml down -v
```

### Load Testing

The test environment supports load testing scenarios:

```bash
# Start with load testing profile
docker compose -f docker-compose.test.yml --profile load-testing up -d

# Execute load tests
docker compose -f docker-compose.test.yml exec test-runner locust -f /app/load-tests/locustfile.py
```

## Configuration

### Environment Variables

Key environment variables for test configuration:

| Variable | Service | Description | Default |
|----------|---------|-------------|---------|
| `NODE_ENV` | frontend | Node environment | `test` |
| `ENVIRONMENT` | backend | Application environment | `test` |
| `TEST_DATABASE_URL` | backend | Test results database connection | Auto-configured |
| `SERVICES_TO_MONITOR` | health-monitor | Services to monitor | Auto-configured |
| `CHECK_INTERVAL` | health-monitor | Health check interval (seconds) | `30` |

### Volume Mounts

The test environment uses several volumes:

- `test_results_data`: Test database persistence
- `test_reports`: Test result reports and artifacts
- Host mounts for live test development

### Profiles

Docker Compose profiles control service groups:

- **Default**: Core application services + test infrastructure
- **test-execution**: Includes test runner for active testing
- **load-testing**: Includes load testing tools

## Monitoring and Debugging

### Service Logs

View logs for specific services:

```bash
# All services
docker compose -f docker-compose.test.yml logs

# Specific service
docker compose -f docker-compose.test.yml logs -f health-monitor
docker compose -f docker-compose.test.yml logs -f test-runner
```

### Health Monitoring

The health monitor provides detailed service status:

```bash
# JSON health status
curl -s http://localhost:8080/health | jq '.'

# Monitor health continuously
watch -n 5 'curl -s http://localhost:8080/health | jq ".status"'
```

### Database Access

Connect to test databases for debugging:

```bash
# Main application database
docker compose -f docker-compose.test.yml exec postgres psql -U observastack -d observastack

# Test results database
docker compose -f docker-compose.test.yml exec test-results-db psql -U test_user -d test_results
```

## Troubleshooting

### Common Issues

#### Services Not Starting

```bash
# Check service status
docker compose -f docker-compose.test.yml ps

# View startup logs
docker compose -f docker-compose.test.yml logs

# Restart specific service
docker compose -f docker-compose.test.yml restart backend
```

#### Network Connectivity Issues

```bash
# Test network connectivity
docker compose -f docker-compose.test.yml exec frontend ping backend
docker compose -f docker-compose.test.yml exec test-runner curl http://backend:8000/health
```

#### Test Failures

```bash
# View detailed test logs
docker compose -f docker-compose.test.yml logs test-runner

# Access test reports
docker compose -f docker-compose.test.yml exec test-runner ls -la /app/reports/

# Copy reports to host
docker compose -f docker-compose.test.yml cp test-runner:/app/reports ./local-reports
```

### Performance Issues

If the test environment is slow:

1. **Increase Docker resources**: Allocate more CPU and memory to Docker
2. **Use SSD storage**: Ensure Docker is using SSD storage for volumes
3. **Optimize test parallelization**: Adjust test runner concurrency settings

### Cleanup

Remove the test environment completely:

```bash
# Stop and remove containers
docker compose -f docker-compose.test.yml down

# Remove volumes (WARNING: This deletes all test data)
docker compose -f docker-compose.test.yml down -v

# Remove images
docker compose -f docker-compose.test.yml down --rmi all
```

## Integration with CI/CD

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
          docker compose -f docker-compose.test.yml exec -T test-runner ./scripts/wait-for-services.sh
          
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

## Next Steps

- [Learn about testing strategy](../architecture/testing-strategy.md)
- [Explore the main application architecture](../architecture/high-level-architecture.md)
- [Set up your development environment](contributing.md)