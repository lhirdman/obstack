import { test, expect } from '@playwright/test';

test.describe('Metrics Page', () => {
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

    // Mock metrics API responses
    await page.route('/api/v1/metrics/query_range', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          data: {
            resultType: 'matrix',
            result: [
              {
                metric: { __name__: 'up', job: 'prometheus' },
                values: [
                  [Date.now() / 1000 - 3600, '1'],
                  [Date.now() / 1000 - 1800, '1'],
                  [Date.now() / 1000, '1']
                ]
              }
            ]
          }
        })
      });
    });

    await page.route('/api/v1/metrics/query', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          data: {
            resultType: 'vector',
            result: [
              {
                metric: { __name__: 'up', job: 'prometheus' },
                value: [Date.now() / 1000, '1']
              }
            ]
          }
        })
      });
    });

    // Navigate to the app
    await page.goto('/');
    
    // Wait for authentication to complete
    await expect(page.locator('text=Welcome to ObservaStack')).toBeVisible();
  });

  test('should navigate to metrics page from dashboard', async ({ page }) => {
    // Click on the Metrics link in the dashboard
    await page.click('text=Open Metrics');
    
    // Should be on the metrics page
    await expect(page).toHaveURL('/metrics');
    await expect(page.locator('h1:has-text("Metrics")')).toBeVisible();
    await expect(page.locator('text=Query and visualize metrics from your observability stack')).toBeVisible();
  });

  test('should navigate to metrics page via navbar', async ({ page }) => {
    // Click on the Metrics link in the navbar
    await page.click('nav a:has-text("Metrics")');
    
    // Should be on the metrics page
    await expect(page).toHaveURL('/metrics');
    await expect(page.locator('h1:has-text("Metrics")')).toBeVisible();
  });

  test('should execute a range query and display chart', async ({ page }) => {
    // Navigate to metrics page
    await page.goto('/metrics');
    
    // Verify initial state
    await expect(page.locator('text=No query executed')).toBeVisible();
    await expect(page.locator('textarea[name="query"]')).toHaveValue('up');
    await expect(page.locator('input[value="range"]')).toBeChecked();
    
    // Execute the query
    await page.click('button:has-text("Execute Query")');
    
    // Should show loading state
    await expect(page.locator('text=Executing...')).toBeVisible();
    
    // Wait for results
    await expect(page.locator('text=Query Results Summary')).toBeVisible();
    await expect(page.locator('text=matrix')).toBeVisible(); // Result type
    await expect(page.locator('text=success')).toBeVisible(); // Status
  });

  test('should execute an instant query', async ({ page }) => {
    // Navigate to metrics page
    await page.goto('/metrics');
    
    // Switch to instant query
    await page.click('input[value="instant"]');
    await expect(page.locator('input[value="instant"]')).toBeChecked();
    
    // Execute the query
    await page.click('button:has-text("Execute Query")');
    
    // Wait for results
    await expect(page.locator('text=Query Results Summary')).toBeVisible();
    await expect(page.locator('text=vector')).toBeVisible(); // Result type
  });

  test('should allow changing the query', async ({ page }) => {
    // Navigate to metrics page
    await page.goto('/metrics');
    
    // Change the query
    await page.fill('textarea[name="query"]', 'cpu_usage');
    await expect(page.locator('textarea[name="query"]')).toHaveValue('cpu_usage');
    
    // Query ready indicator should be visible
    await expect(page.locator('text=Query ready to execute')).toBeVisible();
  });

  test('should use query examples', async ({ page }) => {
    // Navigate to metrics page
    await page.goto('/metrics');
    
    // Open examples dropdown
    await page.click('button:has-text("Examples")');
    
    // Should show example categories
    await expect(page.locator('text=System Health')).toBeVisible();
    await expect(page.locator('text=HTTP Metrics')).toBeVisible();
    
    // Click on a specific example
    await page.click('text=CPU Usage');
    
    // Query should be updated
    await expect(page.locator('textarea[name="query"]')).toHaveValue('rate(cpu_usage_total[5m])');
  });

  test('should use function helpers', async ({ page }) => {
    // Navigate to metrics page
    await page.goto('/metrics');
    
    // Clear the query first
    await page.fill('textarea[name="query"]', '');
    
    // Open functions dropdown
    await page.click('button:has-text("Functions")');
    
    // Should show functions
    await expect(page.locator('text=rate()')).toBeVisible();
    await expect(page.locator('text=sum()')).toBeVisible();
    
    // Click on a function
    await page.click('text=rate()');
    
    // Function should be inserted
    await expect(page.locator('textarea[name="query"]')).toHaveValue('rate()');
  });

  test('should change time range using quick selectors', async ({ page }) => {
    // Navigate to metrics page
    await page.goto('/metrics');
    
    // Click on a quick range button
    await page.click('button:has-text("1h")');
    
    // Duration should be updated
    await expect(page.locator('text=Duration: 60 minutes')).toBeVisible();
  });

  test('should change step/resolution', async ({ page }) => {
    // Navigate to metrics page
    await page.goto('/metrics');
    
    // Should show step selector for range queries
    await expect(page.locator('text=Resolution (Step)')).toBeVisible();
    
    // Click on a different step
    await page.click('button:has-text("1m")');
    
    // Step should be updated in the display
    await expect(page.locator('text=Step: 1m')).toBeVisible();
  });

  test('should hide step selector for instant queries', async ({ page }) => {
    // Navigate to metrics page
    await page.goto('/metrics');
    
    // Switch to instant query
    await page.click('input[value="instant"]');
    
    // Step selector should be hidden
    await expect(page.locator('text=Resolution (Step)')).not.toBeVisible();
  });

  test('should handle query errors gracefully', async ({ page }) => {
    // Mock error response
    await page.route('/api/v1/metrics/query_range', async (route) => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Invalid PromQL query'
        })
      });
    });

    // Navigate to metrics page
    await page.goto('/metrics');
    
    // Execute the query
    await page.click('button:has-text("Execute Query")');
    
    // Should show error message
    await expect(page.locator('text=Query Error')).toBeVisible();
    await expect(page.locator('text=Invalid PromQL query')).toBeVisible();
  });

  test('should execute query with Ctrl+Enter keyboard shortcut', async ({ page }) => {
    // Navigate to metrics page
    await page.goto('/metrics');
    
    // Focus on the query textarea
    await page.focus('textarea[name="query"]');
    
    // Press Ctrl+Enter (or Cmd+Enter on Mac)
    await page.keyboard.press('Control+Enter');
    
    // Should execute the query
    await expect(page.locator('text=Executing...')).toBeVisible();
  });

  test('should disable execute button when query is empty', async ({ page }) => {
    // Navigate to metrics page
    await page.goto('/metrics');
    
    // Clear the query
    await page.fill('textarea[name="query"]', '');
    
    // Execute button should be disabled
    await expect(page.locator('button:has-text("Execute Query")')).toBeDisabled();
  });
});