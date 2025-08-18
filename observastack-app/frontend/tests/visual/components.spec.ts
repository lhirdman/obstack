import { test, expect } from '@playwright/test'

test.describe('Visual Regression Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.route('**/api/auth/me', async route => {
      await route.fulfill({
        json: {
          id: 'user-1',
          username: 'testuser',
          email: 'test@example.com',
          tenantId: 'tenant-1',
          roles: ['viewer']
        }
      })
    })
  })

  test('search form should match visual baseline', async ({ page }) => {
    await page.goto('/search')
    
    // Wait for page to load
    await page.waitForSelector('[placeholder="Search logs, metrics, and traces..."]')
    
    // Take screenshot of search form
    await expect(page.locator('[data-testid="search-form"]')).toHaveScreenshot('search-form.png')
  })

  test('search results should match visual baseline', async ({ page }) => {
    // Mock search results
    await page.route('**/api/search', async route => {
      await route.fulfill({
        json: {
          items: [
            {
              id: 'log-1',
              timestamp: '2025-08-16T07:30:00Z',
              source: 'logs',
              service: 'api-server',
              correlationId: 'trace-123',
              content: {
                message: 'Authentication failed for user john.doe',
                level: 'error',
                labels: { user_id: 'user-456' },
                fields: {}
              }
            },
            {
              id: 'metric-1',
              timestamp: '2025-08-16T07:30:00Z',
              source: 'metrics',
              service: 'api-server',
              content: {
                name: 'cpu_usage_percent',
                value: 85.5,
                labels: { instance: 'api-01' }
              }
            }
          ],
          stats: {
            matched: 2,
            scanned: 1000,
            latencyMs: 125,
            sources: { logs: 1, metrics: 1 }
          },
          facets: []
        }
      })
    })

    await page.goto('/search')
    
    // Perform search
    await page.fill('[placeholder="Search logs, metrics, and traces..."]', 'test query')
    await page.click('button:has-text("Search")')
    
    // Wait for results
    await page.waitForSelector('[data-testid="search-results"]')
    
    // Take screenshot of results
    await expect(page.locator('[data-testid="search-results"]')).toHaveScreenshot('search-results.png')
  })

  test('alert list should match visual baseline', async ({ page }) => {
    // Mock alerts
    await page.route('**/api/alerts', async route => {
      await route.fulfill({
        json: {
          alerts: [
            {
              id: 'alert-1',
              title: 'High CPU Usage',
              description: 'CPU usage is above 90% for the last 5 minutes',
              severity: 'critical',
              status: 'active',
              source: 'prometheus',
              timestamp: '2025-08-16T07:30:00Z',
              labels: { service: 'api-server', instance: 'api-01' },
              tenantId: 'tenant-1'
            },
            {
              id: 'alert-2',
              title: 'Memory Usage Warning',
              description: 'Memory usage is above 80%',
              severity: 'high',
              status: 'acknowledged',
              source: 'prometheus',
              timestamp: '2025-08-16T07:25:00Z',
              labels: { service: 'database', instance: 'db-01' },
              tenantId: 'tenant-1',
              assignee: 'john.doe'
            },
            {
              id: 'alert-3',
              title: 'Disk Space Low',
              description: 'Disk space is below 10%',
              severity: 'medium',
              status: 'resolved',
              source: 'prometheus',
              timestamp: '2025-08-16T07:20:00Z',
              labels: { service: 'storage', instance: 'storage-01' },
              tenantId: 'tenant-1'
            }
          ],
          total: 3,
          hasMore: false
        }
      })
    })

    await page.goto('/alerts')
    
    // Wait for alerts to load
    await page.waitForSelector('[data-testid="alert-list"]')
    
    // Take screenshot of alert list
    await expect(page.locator('[data-testid="alert-list"]')).toHaveScreenshot('alert-list.png')
  })

  test('cost dashboard should match visual baseline', async ({ page }) => {
    // Mock cost data
    await page.route('**/api/costs/summary', async route => {
      await route.fulfill({
        json: {
          totalCost: 1250.75,
          previousPeriodCost: 1100.50,
          trend: 'up',
          trendPercentage: 13.6,
          breakdown: {
            compute: 750.25,
            storage: 300.50,
            network: 150.00,
            other: 50.00
          },
          topNamespaces: [
            { name: 'production', cost: 800.25, percentage: 64.0 },
            { name: 'staging', cost: 250.50, percentage: 20.0 },
            { name: 'development', cost: 200.00, percentage: 16.0 }
          ],
          alerts: {
            budgetExceeded: 2,
            anomaliesDetected: 1,
            optimizationOpportunities: 5
          },
          efficiency: {
            cpuUtilization: 65.5,
            memoryUtilization: 78.2,
            storageUtilization: 82.1,
            overallScore: 75.3
          }
        }
      })
    })

    await page.goto('/insights')
    
    // Wait for cost data to load
    await page.waitForSelector('[data-testid="cost-summary-cards"]')
    
    // Take screenshot of cost dashboard
    await expect(page.locator('[data-testid="cost-summary-cards"]')).toHaveScreenshot('cost-dashboard.png')
  })

  test('embedded dashboard should match visual baseline', async ({ page }) => {
    // Mock Grafana iframe
    await page.route('**/grafana/d/**', async route => {
      await route.fulfill({
        body: `
          <html>
            <body style="background: #1f2937; color: white; padding: 20px;">
              <h1>Mock Grafana Dashboard</h1>
              <div style="background: #374151; padding: 20px; margin: 10px 0; border-radius: 8px;">
                <h3>CPU Usage</h3>
                <div style="height: 200px; background: linear-gradient(45deg, #3b82f6, #10b981); border-radius: 4px;"></div>
              </div>
              <div style="background: #374151; padding: 20px; margin: 10px 0; border-radius: 8px;">
                <h3>Memory Usage</h3>
                <div style="height: 200px; background: linear-gradient(45deg, #f59e0b, #ef4444); border-radius: 4px;"></div>
              </div>
            </body>
          </html>
        `,
        contentType: 'text/html'
      })
    })

    await page.goto('/dashboards')
    
    // Wait for dashboard to load
    await page.waitForSelector('[data-testid="embedded-dashboard"]')
    
    // Take screenshot of embedded dashboard
    await expect(page.locator('[data-testid="embedded-dashboard"]')).toHaveScreenshot('embedded-dashboard.png')
  })

  test('responsive layout on mobile should match visual baseline', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    
    await page.goto('/search')
    
    // Wait for mobile layout
    await page.waitForSelector('[data-testid="mobile-layout"]')
    
    // Take screenshot of mobile layout
    await expect(page).toHaveScreenshot('mobile-layout.png', { fullPage: true })
  })

  test('responsive layout on tablet should match visual baseline', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 })
    
    await page.goto('/search')
    
    // Wait for tablet layout
    await page.waitForSelector('[data-testid="responsive-layout"]')
    
    // Take screenshot of tablet layout
    await expect(page).toHaveScreenshot('tablet-layout.png', { fullPage: true })
  })

  test('dark mode should match visual baseline', async ({ page }) => {
    // Enable dark mode
    await page.emulateMedia({ colorScheme: 'dark' })
    
    await page.goto('/search')
    
    // Wait for dark mode styles
    await page.waitForTimeout(500)
    
    // Take screenshot in dark mode
    await expect(page).toHaveScreenshot('dark-mode.png', { fullPage: true })
  })

  test('high contrast mode should match visual baseline', async ({ page }) => {
    // Enable high contrast mode
    await page.emulateMedia({ 
      colorScheme: 'dark',
      reducedMotion: 'reduce'
    })
    
    // Add high contrast CSS
    await page.addStyleTag({
      content: `
        * {
          border-width: 2px !important;
          outline: 2px solid #fff !important;
        }
        .bg-blue-600 { background-color: #000 !important; }
        .text-gray-600 { color: #fff !important; }
      `
    })
    
    await page.goto('/search')
    
    // Take screenshot in high contrast mode
    await expect(page).toHaveScreenshot('high-contrast.png', { fullPage: true })
  })

  test('loading states should match visual baseline', async ({ page }) => {
    // Mock slow API response
    await page.route('**/api/search', async route => {
      await new Promise(resolve => setTimeout(resolve, 2000))
      await route.fulfill({
        json: { items: [], stats: { matched: 0, scanned: 0, latencyMs: 0, sources: {} }, facets: [] }
      })
    })

    await page.goto('/search')
    
    // Start search to trigger loading state
    await page.fill('[placeholder="Search logs, metrics, and traces..."]', 'loading test')
    await page.click('button:has-text("Search")')
    
    // Wait for loading state
    await page.waitForSelector('[data-testid="loading-skeleton"]')
    
    // Take screenshot of loading state
    await expect(page.locator('[data-testid="search-results"]')).toHaveScreenshot('loading-state.png')
  })

  test('error states should match visual baseline', async ({ page }) => {
    // Mock API error
    await page.route('**/api/search', async route => {
      await route.abort('failed')
    })

    await page.goto('/search')
    
    // Trigger error state
    await page.fill('[placeholder="Search logs, metrics, and traces..."]', 'error test')
    await page.click('button:has-text("Search")')
    
    // Wait for error state
    await page.waitForSelector('[data-testid="error-state"]')
    
    // Take screenshot of error state
    await expect(page.locator('[data-testid="error-state"]')).toHaveScreenshot('error-state.png')
  })

  test('empty states should match visual baseline', async ({ page }) => {
    // Mock empty response
    await page.route('**/api/search', async route => {
      await route.fulfill({
        json: {
          items: [],
          stats: { matched: 0, scanned: 1000, latencyMs: 25, sources: {} },
          facets: []
        }
      })
    })

    await page.goto('/search')
    
    // Trigger empty state
    await page.fill('[placeholder="Search logs, metrics, and traces..."]', 'empty test')
    await page.click('button:has-text("Search")')
    
    // Wait for empty state
    await page.waitForSelector('[data-testid="empty-state"]')
    
    // Take screenshot of empty state
    await expect(page.locator('[data-testid="empty-state"]')).toHaveScreenshot('empty-state.png')
  })
})

test.describe('Component Visual Tests', () => {
  test('buttons should match visual baseline', async ({ page }) => {
    await page.goto('/storybook/iframe.html?id=ui-button--all-variants')
    
    // Wait for Storybook to load
    await page.waitForSelector('[data-testid="button-variants"]')
    
    // Take screenshot of all button variants
    await expect(page.locator('[data-testid="button-variants"]')).toHaveScreenshot('button-variants.png')
  })

  test('form inputs should match visual baseline', async ({ page }) => {
    await page.goto('/storybook/iframe.html?id=ui-input--all-variants')
    
    // Wait for Storybook to load
    await page.waitForSelector('[data-testid="input-variants"]')
    
    // Take screenshot of all input variants
    await expect(page.locator('[data-testid="input-variants"]')).toHaveScreenshot('input-variants.png')
  })

  test('cards should match visual baseline', async ({ page }) => {
    await page.goto('/storybook/iframe.html?id=ui-card--all-variants')
    
    // Wait for Storybook to load
    await page.waitForSelector('[data-testid="card-variants"]')
    
    // Take screenshot of all card variants
    await expect(page.locator('[data-testid="card-variants"]')).toHaveScreenshot('card-variants.png')
  })
})