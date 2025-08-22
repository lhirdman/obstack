# ObservaStack Test Environment

This directory contains the complete test environment setup for ObservaStack, including optimized Dockerfiles, test orchestration, synthetic data generation, and comprehensive testing capabilities.

## Overview

The test environment provides:

- **Complete Application Stack**: Full ObservaStack deployment with React frontend and FastAPI backend
- **Test Orchestration**: Automated test execution and result collection
- **Synthetic Data Generation**: Realistic logs, metrics, and traces for testing
- **Load Testing**: Performance validation under various traffic conditions
- **Chaos Engineering**: Resilience testing with failure injection
- **Health Monitoring**: Continuous monitoring of test environment health

## Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 8GB RAM available for containers
- At least 20GB disk space

### Basic Test Environment

Start the complete test environment:

```bash
# Start the full observability stack with test services
docker compose -f docker-compose.yml -f docker-compose.test.yml up -d

# Wait for services to be ready (this may take 2-3 minutes)
docker compose -f docker-compose.test.yml exec test-runner python test_runner.py health-check

# Access the applications
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Grafana: http://localhost:3001
# Test Dashboard: http://localhost:5432 (PostgreSQL admin tools)
```

### Run All Tests

Execute the complete test suite:

```bash
# Run all tests (unit, integration, E2E)
docker compose -f docker-compose.test.yml run --rm test-runner python test_runner.py run-all-tests

# View test results
docker compose -f docker-compose.test.yml logs test-runner
```

## Service Architecture

### Application Services

#### Frontend (Development Mode)
- **Container**: `observastack-frontend-test`
- **Port**: 3000 (app), 5678 (debugger)
- **Features**: Hot reload, debugging support, test execution
- **Health Check**: `http://localhost:3000/health`

#### Backend (Development Mode)
- **Container**: `observastack-bff-test`
- **Port**: 8000 (app), 5679 (debugger)
- **Features**: Auto-reload, debugging, test dependencies
- **Health Check**: `http://localhost:8000/health`

### Testing Infrastructure

#### Test Runner
- **Container**: `observastack-test-runner`
- **Purpose**: Orchestrates test execution and collects results
- **Database**: PostgreSQL for test result storage
- **Features**: Parallel execution, result aggregation, CI/CD integration

#### Test Database
- **Container**: `observastack-test-db`
- **Port**: 5433
- **Database**: `observastack_test`
- **Schema**: Test executions, results, metrics, benchmarks

#### Synthetic Data Generator
- **Container**: `observastack-synthetic-data`
- **Purpose**: Generates realistic test data
- **Features**: Multi-tenant data, configurable patterns, error injection

#### Load Tester
- **Container**: `observastack-load-tester`
- **Tool**: Grafana k6
- **Features**: Configurable load patterns, performance metrics

## Docker Profiles

The test environment uses Docker Compose profiles to control which services run:

```bash
# Default: Application stack only
docker compose -f docker-compose.test.yml up -d

# With test execution
docker compose -f docker-compose.test.yml --profile test-execution up -d

# With synthetic data generation
docker compose -f docker-compose.test.yml --profile data-generation up -d

# With load testing
docker compose -f docker-compose.test.yml --profile load-testing up -d

# With chaos engineering
docker compose -f docker-compose.test.yml --profile chaos-testing up -d

# All profiles
docker compose -f docker-compose.test.yml --profile test-execution --profile data-generation --profile load-testing up -d
```

## Dockerfile Optimizations

### Multi-Stage Builds

Both frontend and backend Dockerfiles use multi-stage builds:

- **Base Stage**: Common dependencies and system packages
- **Development Stage**: Full development environment with debugging
- **Test Stage**: Runs all tests and quality checks
- **Production Stage**: Optimized runtime environment

### Frontend Dockerfile Features

- **Node.js 22.12**: Latest LTS with performance improvements
- **Vite Development Server**: Fast HMR and development experience
- **Playwright Integration**: E2E testing with browser automation
- **Security**: Non-root user, security headers, health checks
- **Debugging**: Remote debugging support on port 5678

### Backend Dockerfile Features

- **Python 3.12**: Latest stable Python with performance improvements
- **Development Tools**: debugpy, ipdb, rich for enhanced debugging
- **Test Dependencies**: pytest, coverage, quality tools
- **Security**: Non-root user, minimal attack surface
- **Health Checks**: Application and dependency health monitoring

## Test Execution

### Test Types

1. **Unit Tests**
   - Frontend: Vitest with React Testing Library
   - Backend: pytest with coverage reporting
   - Execution: Parallel test execution with detailed reporting

2. **Integration Tests**
   - API contract testing
   - Database integration tests
   - Service-to-service communication tests

3. **End-to-End Tests**
   - Playwright browser automation
   - Complete user workflows
   - Cross-browser compatibility

4. **Load Tests**
   - k6 performance testing
   - Configurable load patterns
   - Performance regression detection

5. **Security Tests**
   - Container vulnerability scanning
   - Dependency security analysis
   - Authentication and authorization testing

### Test Data Management

#### Synthetic Data Generation

The synthetic data generator creates realistic test data:

```bash
# Start data generation
docker compose -f docker-compose.test.yml --profile data-generation up -d synthetic-data-generator

# Generate single batch for testing
docker compose -f docker-compose.test.yml run --rm synthetic-data-generator python synthetic_data_generator.py test

# Monitor generation stats
docker compose -f docker-compose.test.yml logs -f synthetic-data-generator
```

#### Data Configuration

- **Tenants**: Configurable number of test tenants (default: 3)
- **Services**: Realistic service names and interactions
- **Error Rate**: Configurable error injection (default: 5%)
- **Volume**: Adjustable data generation frequency

### Performance Testing

#### Load Test Execution

```bash
# Run standard load test
docker compose -f docker-compose.test.yml --profile load-testing run --rm load-tester

# Custom load test with parameters
docker compose -f docker-compose.test.yml run --rm load-tester run /scripts/load-test.js \
  --vus 50 \
  --duration 10m \
  --env TARGET_URL=http://frontend-test:3000
```

#### Performance Metrics

- **Response Time**: P50, P95, P99 percentiles
- **Throughput**: Requests per second
- **Error Rate**: Failed request percentage
- **Resource Usage**: CPU, memory, network utilization

### Chaos Engineering

#### Failure Injection

```bash
# Start chaos engineering
docker compose -f docker-compose.test.yml --profile chaos-testing up -d chaos-monkey

# Monitor chaos events
docker compose -f docker-compose.test.yml logs -f chaos-monkey
```

#### Chaos Scenarios

- **Service Failures**: Random container restarts
- **Network Issues**: Latency and packet loss injection
- **Resource Exhaustion**: CPU and memory stress testing

## Monitoring and Observability

### Test Metrics

The test environment collects comprehensive metrics:

- **Test Execution Metrics**: Success rates, duration, coverage
- **Performance Metrics**: Response times, throughput, resource usage
- **Error Metrics**: Failure rates, error patterns, recovery times

### Health Monitoring

All services include health checks:

```bash
# Check overall health
docker compose -f docker-compose.test.yml ps

# Detailed health status
docker compose -f docker-compose.test.yml exec test-runner python test_runner.py health-check

# Service-specific health
curl http://localhost:3000/health  # Frontend
curl http://localhost:8000/health  # Backend
```

### Log Aggregation

Logs are collected and structured for analysis:

```bash
# View all logs
docker compose -f docker-compose.test.yml logs

# Service-specific logs
docker compose -f docker-compose.test.yml logs frontend-test
docker compose -f docker-compose.test.yml logs bff-test

# Follow logs in real-time
docker compose -f docker-compose.test.yml logs -f test-runner
```

## CI/CD Integration

### Pipeline Integration

The test environment integrates with CI/CD pipelines:

```yaml
# Example GitHub Actions integration
- name: Run ObservaStack Tests
  run: |
    docker compose -f docker/docker-compose.test.yml up -d
    docker compose -f docker/docker-compose.test.yml run --rm test-runner
    docker compose -f docker/docker-compose.test.yml down
```

### Test Artifacts

Test results are stored in volumes and can be extracted:

```bash
# Copy test results
docker cp observastack-test-runner:/test-results ./test-results

# View test database
docker compose -f docker-compose.test.yml exec test-db psql -U test_user -d observastack_test
```

## Troubleshooting

### Common Issues

1. **Services Not Starting**
   ```bash
   # Check resource usage
   docker system df
   docker system prune
   
   # Increase Docker memory limit to 8GB+
   ```

2. **Test Failures**
   ```bash
   # Check service health
   docker compose -f docker-compose.test.yml exec test-runner python test_runner.py health-check
   
   # View detailed logs
   docker compose -f docker-compose.test.yml logs test-runner
   ```

3. **Performance Issues**
   ```bash
   # Monitor resource usage
   docker stats
   
   # Check test database performance
   docker compose -f docker-compose.test.yml exec test-db pg_stat_activity
   ```

### Debug Mode

Enable debug mode for detailed troubleshooting:

```bash
# Start with debug logging
ENVIRONMENT=debug docker compose -f docker-compose.test.yml up -d

# Connect to debugger
# Frontend: localhost:5678
# Backend: localhost:5679
```

## Configuration

### Environment Variables

Key configuration options:

```bash
# Test execution
TEST_DB_URL=postgresql://test_user:test_password@test-db:5432/observastack_test
FRONTEND_URL=http://frontend-test:3000
BFF_URL=http://bff-test:8000

# Data generation
DATA_GENERATION_INTERVAL=30
TENANT_COUNT=3
ERROR_RATE=0.05

# Load testing
K6_VUS=10
K6_DURATION=5m
```

### Customization

Customize the test environment by:

1. **Modifying Docker Compose**: Add new services or change configurations
2. **Updating Test Scripts**: Modify test cases and scenarios
3. **Configuring Data Generation**: Adjust synthetic data patterns
4. **Setting Performance Thresholds**: Update performance benchmarks

## Security Considerations

### Test Environment Security

- **Isolated Networks**: Test services run in isolated Docker networks
- **Non-Root Users**: All containers run as non-root users
- **Minimal Images**: Production images use minimal base images
- **Secret Management**: Test credentials are isolated from production

### Security Testing

The test environment includes security validation:

- **Vulnerability Scanning**: Container and dependency scanning
- **Authentication Testing**: JWT token validation and RBAC testing
- **Tenant Isolation**: Multi-tenant security boundary validation

## Performance Benchmarks

### Expected Performance

Baseline performance expectations:

- **Frontend Load Time**: < 2 seconds
- **API Response Time**: < 500ms (P95)
- **Search Latency**: < 300ms
- **Error Rate**: < 5%
- **Throughput**: > 100 RPS per service

### Performance Monitoring

Monitor performance trends:

```sql
-- Query test database for performance trends
SELECT 
  test_name,
  metric_name,
  AVG(metric_value) as avg_value,
  MAX(metric_value) as max_value,
  COUNT(*) as sample_count
FROM test_metrics 
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY test_name, metric_name
ORDER BY test_name, metric_name;
```

## Contributing

### Adding New Tests

1. **Unit Tests**: Add to respective test directories
2. **Integration Tests**: Update test runner configuration
3. **Load Tests**: Add new k6 scripts to `load-tests/`
4. **Synthetic Data**: Extend data generator patterns

### Test Environment Updates

1. **Docker Images**: Update Dockerfiles with new dependencies
2. **Compose Configuration**: Add new services or profiles
3. **Database Schema**: Update test database initialization
4. **Documentation**: Update this README with changes

For more information, see the main [ObservaStack documentation](../docs/README.md).