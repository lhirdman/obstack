#!/bin/bash
set -e

echo "=== ObservaStack Test Runner ==="
echo "Starting comprehensive test execution..."

# Create reports directory
mkdir -p /app/reports

# Wait for services to be ready
echo "Waiting for services to be ready..."
./scripts/wait-for-services.sh

# Run backend unit tests
echo "Running backend unit tests..."
cd /app/backend-tests
pytest unit/ --junitxml=/app/reports/backend-unit-results.xml --cov=app --cov-report=xml:/app/reports/backend-coverage.xml

# Run backend integration tests
echo "Running backend integration tests..."
pytest integration/ --junitxml=/app/reports/backend-integration-results.xml

# Run frontend unit tests
echo "Running frontend unit tests..."
cd /app/frontend-tests
npm test -- --reporter=junit --outputFile=/app/reports/frontend-unit-results.xml

# Install Playwright browsers
echo "Installing Playwright browsers..."
npx playwright install

# Run E2E tests
echo "Running E2E tests..."
npx playwright test --reporter=junit --output-dir=/app/reports/e2e-results

# Run accessibility tests
echo "Running accessibility tests..."
npx playwright test tests/accessibility/ --reporter=junit --output-dir=/app/reports/accessibility-results

# Generate consolidated report
echo "Generating consolidated test report..."
python /app/scripts/generate-report.py

echo "=== Test execution completed ==="
echo "Reports available in /app/reports/"