# Testing

ObservaStack follows a comprehensive testing strategy to ensure reliability, performance, and maintainability. This guide covers our testing approaches, tools, and best practices.

## Testing Philosophy

Our testing strategy is built on these principles:

- **Test Pyramid**: More unit tests, fewer integration tests, minimal E2E tests
- **Test-Driven Development**: Write tests before or alongside code
- **Continuous Testing**: Automated testing in CI/CD pipeline
- **Quality Gates**: Tests must pass before code can be merged

## Testing Stack

### Frontend Testing

- **Unit Tests**: Vitest + React Testing Library
- **Component Tests**: Storybook + Chromatic
- **E2E Tests**: Playwright
- **Visual Regression**: Chromatic
- **Performance Tests**: Lighthouse CI

### Backend Testing

- **Unit Tests**: pytest + pytest-asyncio
- **Integration Tests**: pytest with test database
- **API Tests**: httpx + pytest
- **Load Tests**: Locust
- **Contract Tests**: Pact

## Unit Testing

### Frontend Unit Tests

#### Testing Components

```typescript
// SearchInput.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { SearchInput } from './SearchInput';

describe('SearchInput', () => {
  it('calls onSearch when form is submitted', () => {
    const mockOnSearch = vi.fn();
    render(<SearchInput onSearch={mockOnSearch} />);
    
    const input = screen.getByPlaceholderText('Search...');
    const button = screen.getByRole('button', { name: /search/i });
    
    fireEvent.change(input, { target: { value: 'test query' } });
    fireEvent.click(button);
    
    expect(mockOnSearch).toHaveBeenCalledWith('test query');
  });

  it('disables search button when input is empty', () => {
    render(<SearchInput onSearch={vi.fn()} />);
    
    const button = screen.getByRole('button', { name: /search/i });
    expect(button).toBeDisabled();
  });
});
```

#### Testing Custom Hooks

```typescript
// useSearch.test.ts
import { renderHook, act } from '@testing-library/react';
import { vi } from 'vitest';
import { useSearch } from './useSearch';
import * as searchService from '../services/searchService';

vi.mock('../services/searchService');

describe('useSearch', () => {
  it('performs search and updates state', async () => {
    const mockResults = [{ id: '1', message: 'test' }];
    vi.mocked(searchService.search).mockResolvedValue(mockResults);
    
    const { result } = renderHook(() => useSearch());
    
    await act(async () => {
      await result.current.search({ freeText: 'test', type: 'logs' });
    });
    
    expect(result.current.results).toEqual(mockResults);
    expect(result.current.loading).toBe(false);
  });

  it('handles search errors', async () => {
    const error = new Error('Search failed');
    vi.mocked(searchService.search).mockRejectedValue(error);
    
    const { result } = renderHook(() => useSearch());
    
    await act(async () => {
      await result.current.search({ freeText: 'test', type: 'logs' });
    });
    
    expect(result.current.error).toBe(error);
    expect(result.current.loading).toBe(false);
  });
});
```

### Backend Unit Tests

#### Testing Services

```python
# test_search_service.py
import pytest
from unittest.mock import AsyncMock, Mock
from app.services.search_service import SearchService
from app.models.search import SearchQuery, TimeRange
from app.exceptions import ValidationError

@pytest.fixture
def mock_loki_client():
    client = AsyncMock()
    client.query.return_value = [
        {"id": "1", "message": "test log", "timestamp": "2025-08-16T10:00:00Z"}
    ]
    return client

@pytest.fixture
def search_service(mock_loki_client):
    return SearchService(loki_client=mock_loki_client)

@pytest.mark.asyncio
async def test_search_logs_success(search_service, mock_loki_client):
    query = SearchQuery(
        free_text="error",
        type="logs",
        time_range=TimeRange(
            start="2025-08-16T00:00:00Z",
            end="2025-08-16T23:59:59Z"
        )
    )
    
    results = await search_service.search(query, "tenant-123")
    
    assert len(results.items) == 1
    assert results.items[0]["message"] == "test log"
    mock_loki_client.query.assert_called_once()

@pytest.mark.asyncio
async def test_search_empty_query_raises_error(search_service):
    query = SearchQuery(
        free_text="",
        type="logs",
        time_range=TimeRange(
            start="2025-08-16T00:00:00Z",
            end="2025-08-16T23:59:59Z"
        )
    )
    
    with pytest.raises(ValidationError, match="Search query cannot be empty"):
        await search_service.search(query, "tenant-123")
```

#### Testing API Endpoints

```python
# test_search_endpoints.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_search_endpoint_success():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/search",
            json={
                "freeText": "error",
                "type": "logs",
                "timeRange": {
                    "start": "2025-08-16T00:00:00Z",
                    "end": "2025-08-16T23:59:59Z"
                }
            },
            headers={"Authorization": "Bearer valid-token"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "stats" in data

@pytest.mark.asyncio
async def test_search_endpoint_unauthorized():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/search",
            json={"freeText": "error", "type": "logs"}
        )
    
    assert response.status_code == 401
```

## Integration Testing

### Database Integration Tests

```python
# test_database_integration.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.db.base import Base
from app.models.user import User
from app.services.user_service import UserService

@pytest.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(engine) as session:
        yield session
    
    await engine.dispose()

@pytest.mark.asyncio
async def test_create_user(test_db):
    user_service = UserService(test_db)
    
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "tenant_id": "test-tenant"
    }
    
    user = await user_service.create_user(user_data)
    
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.tenant_id == "test-tenant"
```

### External Service Integration

```python
# test_prometheus_integration.py
import pytest
from app.services.prometheus_client import PrometheusClient
from app.exceptions import ExternalServiceError

@pytest.mark.asyncio
async def test_prometheus_query_success():
    client = PrometheusClient("http://localhost:9090")
    
    # This test requires a running Prometheus instance
    try:
        result = await client.query("up")
        assert "data" in result
        assert "result" in result["data"]
    except ExternalServiceError:
        pytest.skip("Prometheus not available")

@pytest.mark.asyncio
async def test_prometheus_query_invalid():
    client = PrometheusClient("http://localhost:9090")
    
    with pytest.raises(ExternalServiceError):
        await client.query("invalid_metric_name{")
```

## End-to-End Testing

### Playwright E2E Tests

```typescript
// search.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Search functionality', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('[data-testid="username"]', 'admin');
    await page.fill('[data-testid="password"]', 'admin');
    await page.click('[data-testid="login-button"]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('should perform basic search', async ({ page }) => {
    await page.goto('/search');
    
    // Enter search query
    await page.fill('[data-testid="search-input"]', 'error');
    await page.selectOption('[data-testid="search-type"]', 'logs');
    await page.click('[data-testid="search-button"]');
    
    // Wait for results
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
    await expect(page.locator('[data-testid="result-item"]')).toHaveCount.greaterThan(0);
  });

  test('should filter search results', async ({ page }) => {
    await page.goto('/search');
    
    // Perform initial search
    await page.fill('[data-testid="search-input"]', 'error');
    await page.click('[data-testid="search-button"]');
    
    // Apply filters
    await page.click('[data-testid="filter-service"]');
    await page.click('[data-testid="service-web-app"]');
    
    // Verify filtered results
    const results = page.locator('[data-testid="result-item"]');
    await expect(results).toHaveCount.greaterThan(0);
    
    // Check that all results are from web-app service
    const serviceLabels = results.locator('[data-testid="service-label"]');
    await expect(serviceLabels.first()).toHaveText('web-app');
  });

  test('should navigate to log details', async ({ page }) => {
    await page.goto('/search');
    
    await page.fill('[data-testid="search-input"]', 'error');
    await page.click('[data-testid="search-button"]');
    
    // Click on first result
    await page.click('[data-testid="result-item"]').first();
    
    // Should navigate to log details page
    await expect(page).toHaveURL(/\/logs\/.*$/);
    await expect(page.locator('[data-testid="log-details"]')).toBeVisible();
  });
});
```

### API E2E Tests

```typescript
// api.spec.ts
import { test, expect } from '@playwright/test';

test.describe('API endpoints', () => {
  let authToken: string;

  test.beforeAll(async ({ request }) => {
    // Get authentication token
    const response = await request.post('/api/v1/auth/login', {
      data: {
        username: 'admin',
        password: 'admin'
      }
    });
    
    const data = await response.json();
    authToken = data.access_token;
  });

  test('should search logs via API', async ({ request }) => {
    const response = await request.post('/api/v1/search', {
      headers: {
        'Authorization': `Bearer ${authToken}`
      },
      data: {
        freeText: 'error',
        type: 'logs',
        timeRange: {
          start: '2025-08-16T00:00:00Z',
          end: '2025-08-16T23:59:59Z'
        }
      }
    });

    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('items');
    expect(data).toHaveProperty('stats');
    expect(Array.isArray(data.items)).toBe(true);
  });

  test('should return 401 for unauthorized requests', async ({ request }) => {
    const response = await request.post('/api/v1/search', {
      data: {
        freeText: 'error',
        type: 'logs'
      }
    });

    expect(response.status()).toBe(401);
  });
});
```

## Performance Testing

### Frontend Performance Tests

```typescript
// performance.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Performance tests', () => {
  test('search page should load within 2 seconds', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('/search');
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    expect(loadTime).toBeLessThan(2000);
  });

  test('search results should render within 1 second', async ({ page }) => {
    await page.goto('/search');
    
    const startTime = Date.now();
    await page.fill('[data-testid="search-input"]', 'error');
    await page.click('[data-testid="search-button"]');
    await page.waitForSelector('[data-testid="search-results"]');
    
    const searchTime = Date.now() - startTime;
    expect(searchTime).toBeLessThan(1000);
  });
});
```

### Backend Load Tests

```python
# locustfile.py
from locust import HttpUser, task, between

class ObservaStackUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login and get token
        response = self.client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def search_logs(self):
        self.client.post("/api/v1/search", 
            headers=self.headers,
            json={
                "freeText": "error",
                "type": "logs",
                "timeRange": {
                    "start": "2025-08-16T00:00:00Z",
                    "end": "2025-08-16T23:59:59Z"
                }
            }
        )
    
    @task(1)
    def get_alerts(self):
        self.client.get("/api/v1/alerts", headers=self.headers)
    
    @task(1)
    def get_dashboards(self):
        self.client.get("/api/v1/dashboards", headers=self.headers)
```

## Test Configuration

### Frontend Test Setup

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
    coverage: {
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*'
      ]
    }
  }
});
```

```typescript
// src/test/setup.ts
import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn(() => ({
  observe: vi.fn(),
  disconnect: vi.fn(),
  unobserve: vi.fn(),
}));

// Mock ResizeObserver
global.ResizeObserver = vi.fn(() => ({
  observe: vi.fn(),
  disconnect: vi.fn(),
  unobserve: vi.fn(),
}));
```

### Backend Test Configuration

```python
# conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from app.core.config import settings

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_settings():
    settings.TESTING = True
    settings.DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    return settings

@pytest.fixture
def auth_headers():
    # Mock JWT token for testing
    token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    return {"Authorization": f"Bearer {token}"}
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 18
          cache: npm
          cache-dependency-path: observastack-app/frontend/package-lock.json
      
      - name: Install dependencies
        run: |
          cd observastack-app/frontend
          npm ci
      
      - name: Run unit tests
        run: |
          cd observastack-app/frontend
          npm test -- --coverage
      
      - name: Run E2E tests
        run: |
          cd observastack-app/frontend
          npm run test:e2e
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./observastack-app/frontend/coverage/lcov.info

  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          cd observastack-app/bff
          pip install -r requirements.txt
          pip install pytest-cov
      
      - name: Run tests
        run: |
          cd observastack-app/bff
          pytest --cov=app --cov-report=xml
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/test
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./observastack-app/bff/coverage.xml
```

## Test Data Management

### Test Fixtures

```python
# fixtures.py
import pytest
from app.models.user import User
from app.models.tenant import Tenant

@pytest.fixture
def sample_user():
    return User(
        id="user-123",
        username="testuser",
        email="test@example.com",
        tenant_id="tenant-123"
    )

@pytest.fixture
def sample_tenant():
    return Tenant(
        id="tenant-123",
        name="Test Tenant",
        domain="test.com"
    )

@pytest.fixture
def sample_search_results():
    return [
        {
            "id": "log-1",
            "timestamp": "2025-08-16T10:00:00Z",
            "message": "Error processing request",
            "level": "error",
            "service": "web-app"
        },
        {
            "id": "log-2",
            "timestamp": "2025-08-16T10:01:00Z",
            "message": "Request completed successfully",
            "level": "info",
            "service": "web-app"
        }
    ]
```

### Mock Data Factories

```typescript
// test-factories.ts
import { faker } from '@faker-js/faker';

export const createMockUser = (overrides = {}) => ({
  id: faker.string.uuid(),
  username: faker.internet.userName(),
  email: faker.internet.email(),
  tenantId: faker.string.uuid(),
  ...overrides
});

export const createMockSearchResult = (overrides = {}) => ({
  id: faker.string.uuid(),
  timestamp: faker.date.recent().toISOString(),
  message: faker.lorem.sentence(),
  level: faker.helpers.arrayElement(['info', 'warning', 'error']),
  service: faker.helpers.arrayElement(['web-app', 'api-gateway', 'database']),
  ...overrides
});

export const createMockSearchQuery = (overrides = {}) => ({
  freeText: faker.lorem.word(),
  type: 'logs',
  timeRange: {
    start: faker.date.past().toISOString(),
    end: faker.date.recent().toISOString()
  },
  ...overrides
});
```

## Best Practices

### Test Organization

- **Group related tests** in describe blocks
- **Use descriptive test names** that explain the scenario
- **Follow AAA pattern**: Arrange, Act, Assert
- **Keep tests independent** and isolated

### Test Maintenance

- **Update tests** when code changes
- **Remove obsolete tests** regularly
- **Refactor test code** like production code
- **Monitor test performance** and optimize slow tests

### Coverage Goals

- **Unit Tests**: 80%+ code coverage
- **Integration Tests**: Cover critical paths
- **E2E Tests**: Cover user journeys
- **Performance Tests**: Cover key scenarios

## Debugging Tests

### Frontend Test Debugging

```typescript
// Debug failing tests
import { screen, debug } from '@testing-library/react';

test('debug example', () => {
  render(<SearchResults results={[]} loading={false} />);
  
  // Print current DOM state
  debug();
  
  // Print specific element
  debug(screen.getByTestId('search-results'));
});
```

### Backend Test Debugging

```python
# Debug with pytest
pytest -v -s test_search_service.py::test_search_logs_success

# Debug with pdb
import pdb; pdb.set_trace()

# Debug with logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

- [Learn about the architecture](architecture.md)
- [Set up your development environment](contributing.md)
- [Explore the API reference](api-reference.md)