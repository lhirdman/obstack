import { test, expect } from '@playwright/test'

test.describe('Search Functionality', () => {
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

    // Mock search API
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
            }
          ],
          stats: {
            matched: 1,
            scanned: 100,
            latencyMs: 45,
            sources: { logs: 1 }
          },
          facets: []
        }
      })
    })

    await page.goto('/search')
  })

  test('should perform basic search', async ({ page }) => {
    // Enter search query
    await page.fill('[placeholder="Search logs, metrics, and traces..."]', 'authentication failed')
    
    // Click search button
    await page.click('button:has-text("Search")')
    
    // Wait for results
    await expect(page.locator('text=Authentication failed for user john.doe')).toBeVisible()
    await expect(page.locator('text=1 results')).toBeVisible()
    await expect(page.locator('text=45ms')).toBeVisible()
  })

  test('should filter search results', async ({ page }) => {
    // Open filters
    await page.click('button:has-text("Filters")')
    
    // Add filter
    await page.click('button:has-text("Add Filter")')
    
    // Configure filter
    await page.selectOption('select[name="field"]', 'level')
    await page.selectOption('select[name="operator"]', 'equals')
    await page.fill('input[name="value"]', 'error')
    
    // Apply filters
    await page.click('button:has-text("Apply")')
    
    // Perform search
    await page.fill('[placeholder="Search logs, metrics, and traces..."]', 'failed')
    await page.click('button:has-text("Search")')
    
    // Verify filtered results
    await expect(page.locator('text=Authentication failed for user john.doe')).toBeVisible()
  })

  test('should change time range', async ({ page }) => {
    // Change time range
    await page.selectOption('select[aria-label="Time range"]', 'now-24h')
    
    // Perform search
    await page.fill('[placeholder="Search logs, metrics, and traces..."]', 'error')
    await page.click('button:has-text("Search")')
    
    // Verify search was performed with new time range
    await expect(page.locator('text=Authentication failed for user john.doe')).toBeVisible()
  })

  test('should navigate to correlated traces', async ({ page }) => {
    // Perform initial search
    await page.fill('[placeholder="Search logs, metrics, and traces..."]', 'authentication')
    await page.click('button:has-text("Search")')
    
    // Wait for results
    await expect(page.locator('text=Authentication failed for user john.doe')).toBeVisible()
    
    // Click correlation link
    await page.click('text=Correlated')
    
    // Verify correlation search is triggered
    await expect(page.locator('[placeholder="Search logs, metrics, and traces..."]')).toHaveValue('trace-123')
  })

  test('should handle empty search results', async ({ page }) => {
    // Mock empty results
    await page.route('**/api/search', async route => {
      await route.fulfill({
        json: {
          items: [],
          stats: { matched: 0, scanned: 1000, latencyMs: 25, sources: {} },
          facets: []
        }
      })
    })

    // Perform search
    await page.fill('[placeholder="Search logs, metrics, and traces..."]', 'nonexistent')
    await page.click('button:has-text("Search")')
    
    // Verify empty state
    await expect(page.locator('text=No results found')).toBeVisible()
    await expect(page.locator('text=Try adjusting your search terms')).toBeVisible()
  })

  test('should handle search errors', async ({ page }) => {
    // Mock API error
    await page.route('**/api/search', async route => {
      await route.abort('failed')
    })

    // Perform search
    await page.fill('[placeholder="Search logs, metrics, and traces..."]', 'test')
    await page.click('button:has-text("Search")')
    
    // Verify error state
    await expect(page.locator('text=Search failed')).toBeVisible()
    await expect(page.locator('button:has-text("Try Again")')).toBeVisible()
  })

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    
    // Verify mobile layout
    await expect(page.locator('[data-testid="mobile-search-form"]')).toBeVisible()
    
    // Perform search on mobile
    await page.fill('[placeholder="Search logs, metrics, and traces..."]', 'mobile test')
    await page.click('button:has-text("Search")')
    
    // Verify results are displayed properly on mobile
    await expect(page.locator('text=Authentication failed for user john.doe')).toBeVisible()
  })

  test('should save and load search history', async ({ page }) => {
    // Mock search history API
    await page.route('**/api/search/history', async route => {
      await route.fulfill({
        json: [
          {
            id: 'history-1',
            query: 'previous search',
            timestamp: '2025-08-16T07:00:00Z',
            type: 'logs'
          }
        ]
      })
    })

    // Open search history
    await page.click('[aria-label="Search history"]')
    
    // Verify history is displayed
    await expect(page.locator('text=previous search')).toBeVisible()
    
    // Click on history item
    await page.click('text=previous search')
    
    // Verify search form is populated
    await expect(page.locator('[placeholder="Search logs, metrics, and traces..."]')).toHaveValue('previous search')
  })
})

test.describe('Search Accessibility', () => {
  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/search')
    
    // Tab to search input
    await page.keyboard.press('Tab')
    await expect(page.locator('[placeholder="Search logs, metrics, and traces..."]')).toBeFocused()
    
    // Type search query
    await page.keyboard.type('accessibility test')
    
    // Tab to search button and press Enter
    await page.keyboard.press('Tab')
    await expect(page.locator('button:has-text("Search")')).toBeFocused()
    await page.keyboard.press('Enter')
    
    // Verify search was performed
    await expect(page.locator('text=1 results')).toBeVisible()
  })

  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto('/search')
    
    // Check ARIA labels
    await expect(page.locator('[aria-label="Search query"]')).toBeVisible()
    await expect(page.locator('[aria-label="Search type"]')).toBeVisible()
    await expect(page.locator('[aria-label="Time range"]')).toBeVisible()
    await expect(page.locator('[aria-label="Search filters"]')).toBeVisible()
  })

  test('should announce search results to screen readers', async ({ page }) => {
    await page.goto('/search')
    
    // Perform search
    await page.fill('[placeholder="Search logs, metrics, and traces..."]', 'test')
    await page.click('button:has-text("Search")')
    
    // Check for ARIA live region updates
    await expect(page.locator('[aria-live="polite"]')).toContainText('1 results found')
  })
})