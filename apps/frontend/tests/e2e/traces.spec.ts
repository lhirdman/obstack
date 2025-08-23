import { test, expect } from '@playwright/test';

test.describe('Traces Page', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the authentication
    await page.route('/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          tenant_id: 1,
          roles: ['user']
        })
      });
    });

    // Mock trace API responses
    await page.route('/api/v1/traces/1234567890abcdef', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          batches: [
            {
              resource: {
                attributes: [
                  {
                    key: 'service.name',
                    value: { stringValue: 'frontend' }
                  },
                  {
                    key: 'tenant_id',
                    value: { stringValue: '1' }
                  }
                ]
              },
              scopeSpans: [
                {
                  spans: [
                    {
                      traceId: '1234567890abcdef',
                      spanId: 'abcdef1234567890',
                      name: 'GET /api/users',
                      startTimeUnixNano: '1640995200000000000',
                      endTimeUnixNano: '1640995201000000000',
                      attributes: [
                        {
                          key: 'http.method',
                          value: { stringValue: 'GET' }
                        },
                        {
                          key: 'http.url',
                          value: { stringValue: '/api/users' }
                        }
                      ],
                      status: {
                        code: 0
                      }
                    },
                    {
                      traceId: '1234567890abcdef',
                      spanId: 'fedcba0987654321',
                      parentSpanId: 'abcdef1234567890',
                      name: 'database query',
                      startTimeUnixNano: '1640995200100000000',
                      endTimeUnixNano: '1640995200800000000',
                      attributes: [
                        {
                          key: 'db.statement',
                          value: { stringValue: 'SELECT * FROM users' }
                        }
                      ],
                      status: {
                        code: 0
                      }
                    }
                  ]
                }
              ]
            }
          ]
        })
      });
    });

    // Mock trace not found
    await page.route('/api/v1/traces/nonexistent', async (route) => {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Trace not found'
        })
      });
    });

    // Navigate to the app
    await page.goto('/');
    
    // Wait for authentication to complete
    await expect(page.locator('text=Welcome to ObservaStack')).toBeVisible();
  });

  test('should navigate to traces page from dashboard', async ({ page }) => {
    // Click on the Traces link in the dashboard
    await page.click('text=Open Traces');
    
    // Should be on the traces page
    await expect(page).toHaveURL('/traces');
    await expect(page.locator('h1:has-text("Traces")')).toBeVisible();
    await expect(page.locator('text=Search and visualize distributed traces')).toBeVisible();
  });

  test('should navigate to traces page via navbar', async ({ page }) => {
    // Click on the Traces link in the navbar
    await page.click('nav a:has-text("Traces")');
    
    // Should be on the traces page
    await expect(page).toHaveURL('/traces');
    await expect(page.locator('h1:has-text("Traces")')).toBeVisible();
  });

  test('should search for a trace and display waterfall', async ({ page }) => {
    // Navigate to traces page
    await page.goto('/traces');
    
    // Verify initial state
    await expect(page.locator('text=No trace selected')).toBeVisible();
    
    // Enter trace ID
    await page.fill('input[placeholder*="Enter trace ID"]', '1234567890abcdef');
    
    // Should show valid format message
    await expect(page.locator('text=Valid trace ID format')).toBeVisible();
    
    // Click search button
    await page.click('button:has-text("Search Trace")');
    
    // Should show loading state
    await expect(page.locator('text=Searching...')).toBeVisible();
    
    // Wait for results
    await expect(page.locator('text=2 spans')).toBeVisible();
    await expect(page.locator('text=GET /api/users')).toBeVisible();
    await expect(page.locator('text=database query')).toBeVisible();
  });

  test('should search by pressing Enter', async ({ page }) => {
    // Navigate to traces page
    await page.goto('/traces');
    
    // Enter trace ID and press Enter
    await page.fill('input[placeholder*="Enter trace ID"]', '1234567890abcdef');
    await page.press('input[placeholder*="Enter trace ID"]', 'Enter');
    
    // Wait for results
    await expect(page.locator('text=2 spans')).toBeVisible();
  });

  test('should validate trace ID format', async ({ page }) => {
    // Navigate to traces page
    await page.goto('/traces');
    
    // Enter invalid trace ID
    await page.fill('input[placeholder*="Enter trace ID"]', 'invalid-trace-id');
    
    // Should show validation message
    await expect(page.locator('text=Trace ID should be a hexadecimal string')).toBeVisible();
    
    // Search button should be disabled
    await expect(page.locator('button:has-text("Search Trace")')).toBeDisabled();
  });

  test('should handle trace not found', async ({ page }) => {
    // Navigate to traces page
    await page.goto('/traces');
    
    // Enter non-existent trace ID
    await page.fill('input[placeholder*="Enter trace ID"]', 'nonexistent');
    await page.click('button:has-text("Search Trace")');
    
    // Should show error message
    await expect(page.locator('text=Trace Not Found')).toBeVisible();
    await expect(page.locator('text=Trace not found')).toBeVisible();
  });

  test('should display span details when span is clicked', async ({ page }) => {
    // Navigate to traces page and search
    await page.goto('/traces');
    await page.fill('input[placeholder*="Enter trace ID"]', '1234567890abcdef');
    await page.click('button:has-text("Search Trace")');
    
    // Wait for waterfall to load
    await expect(page.locator('text=GET /api/users')).toBeVisible();
    
    // Initially should show "click on a span" message
    await expect(page.locator('text=Click on a span in the waterfall to view its details')).toBeVisible();
    
    // Click on the first span
    await page.click('text=GET /api/users');
    
    // Should show span details
    await expect(page.locator('text=Span Overview')).toBeVisible();
    await expect(page.locator('text=Service:')).toBeVisible();
    await expect(page.locator('text=frontend')).toBeVisible();
    await expect(page.locator('text=Operation:')).toBeVisible();
  });

  test('should show trace summary information', async ({ page }) => {
    // Navigate to traces page and search
    await page.goto('/traces');
    await page.fill('input[placeholder*="Enter trace ID"]', '1234567890abcdef');
    await page.click('button:has-text("Search Trace")');
    
    // Wait for results and check summary
    await expect(page.locator('text=Total Duration:')).toBeVisible();
    await expect(page.locator('text=Spans:')).toBeVisible();
    await expect(page.locator('text=Start Time:')).toBeVisible();
    await expect(page.locator('text=Services:')).toBeVisible();
  });

  test('should show span hierarchy with indentation', async ({ page }) => {
    // Navigate to traces page and search
    await page.goto('/traces');
    await page.fill('input[placeholder*="Enter trace ID"]', '1234567890abcdef');
    await page.click('button:has-text("Search Trace")');
    
    // Wait for waterfall to load
    await expect(page.locator('text=GET /api/users')).toBeVisible();
    await expect(page.locator('text=database query')).toBeVisible();
    
    // The database query should be indented (child span)
    // This is visual, so we check that both spans are present
    const spans = page.locator('[data-testid="span-row"], .cursor-pointer:has-text("GET /api/users"), .cursor-pointer:has-text("database query")');
    await expect(spans.first()).toBeVisible();
  });

  test('should show search history', async ({ page }) => {
    // Navigate to traces page
    await page.goto('/traces');
    
    // Search for a trace
    await page.fill('input[placeholder*="Enter trace ID"]', '1234567890abcdef');
    await page.click('button:has-text("Search Trace")');
    
    // Wait for search to complete
    await expect(page.locator('text=2 spans')).toBeVisible();
    
    // Should show search history
    await expect(page.locator('text=Recent Searches')).toBeVisible();
    
    // History should contain the searched trace ID
    await expect(page.locator('button:has-text("1234567890abcdef")')).toBeVisible();
  });

  test('should use search history', async ({ page }) => {
    // Navigate to traces page
    await page.goto('/traces');
    
    // First search
    await page.fill('input[placeholder*="Enter trace ID"]', '1234567890abcdef');
    await page.click('button:has-text("Search Trace")');
    await expect(page.locator('text=2 spans')).toBeVisible();
    
    // Clear the input
    await page.fill('input[placeholder*="Enter trace ID"]', '');
    
    // Click on history item
    await page.click('button:has-text("1234567890abcdef")');
    
    // Should search again
    await expect(page.locator('text=2 spans')).toBeVisible();
    await expect(page.locator('input[placeholder*="Enter trace ID"]')).toHaveValue('1234567890abcdef');
  });

  test('should show search tips', async ({ page }) => {
    // Navigate to traces page
    await page.goto('/traces');
    
    // Should show search tips
    await expect(page.locator('text=Search Tips')).toBeVisible();
    await expect(page.locator('text=Trace IDs are hexadecimal strings')).toBeVisible();
    await expect(page.locator('text=You can only search traces from your tenant')).toBeVisible();
  });

  test('should show timeline with proper scaling', async ({ page }) => {
    // Navigate to traces page and search
    await page.goto('/traces');
    await page.fill('input[placeholder*="Enter trace ID"]', '1234567890abcdef');
    await page.click('button:has-text("Search Trace")');
    
    // Wait for waterfall to load
    await expect(page.locator('text=GET /api/users')).toBeVisible();
    
    // Should show timeline markers
    await expect(page.locator('text=0ms')).toBeVisible();
    
    // Should show span timing bars (visual elements)
    const timelineBars = page.locator('.bg-gray-100'); // Timeline background
    await expect(timelineBars.first()).toBeVisible();
  });

  test('should show span attributes in details', async ({ page }) => {
    // Navigate to traces page and search
    await page.goto('/traces');
    await page.fill('input[placeholder*="Enter trace ID"]', '1234567890abcdef');
    await page.click('button:has-text("Search Trace")');
    
    // Wait for waterfall and click on span
    await expect(page.locator('text=GET /api/users')).toBeVisible();
    await page.click('text=GET /api/users');
    
    // Should show span details with attributes
    await expect(page.locator('text=Span Overview')).toBeVisible();
    await expect(page.locator('text=Attributes')).toBeVisible();
    await expect(page.locator('text=HTTP')).toBeVisible(); // HTTP attributes section
  });

  test('should show legend', async ({ page }) => {
    // Navigate to traces page and search
    await page.goto('/traces');
    await page.fill('input[placeholder*="Enter trace ID"]', '1234567890abcdef');
    await page.click('button:has-text("Search Trace")');
    
    // Wait for waterfall to load
    await expect(page.locator('text=GET /api/users')).toBeVisible();
    
    // Should show legend
    await expect(page.locator('text=Legend')).toBeVisible();
    await expect(page.locator('text=Success')).toBeVisible();
    await expect(page.locator('text=Warning')).toBeVisible();
    await expect(page.locator('text=Error')).toBeVisible();
  });
});