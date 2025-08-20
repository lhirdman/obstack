import { test, expect } from '@playwright/test'

test.describe('Alert Management', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.route('**/api/auth/me', async route => {
      await route.fulfill({
        json: {
          id: 'user-1',
          username: 'testuser',
          email: 'test@example.com',
          tenantId: 'tenant-1',
          roles: ['operator']
        }
      })
    })

    // Mock alerts API
    await page.route('**/api/alerts', async route => {
      await route.fulfill({
        json: {
          alerts: [
            {
              id: 'alert-1',
              title: 'High CPU Usage',
              description: 'CPU usage is above 90%',
              severity: 'critical',
              status: 'active',
              source: 'prometheus',
              timestamp: '2025-08-16T07:30:00Z',
              labels: { service: 'api-server' },
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
              labels: { service: 'database' },
              tenantId: 'tenant-1',
              assignee: 'john.doe'
            }
          ],
          total: 2,
          hasMore: false
        }
      })
    })

    await page.goto('/alerts')
  })

  test('should display alert list', async ({ page }) => {
    // Verify alerts are displayed
    await expect(page.locator('text=High CPU Usage')).toBeVisible()
    await expect(page.locator('text=Memory Usage Warning')).toBeVisible()
    
    // Verify alert metadata
    await expect(page.locator('text=CRITICAL')).toBeVisible()
    await expect(page.locator('text=HIGH')).toBeVisible()
    await expect(page.locator('text=prometheus')).toBeVisible()
  })

  test('should acknowledge alert', async ({ page }) => {
    // Mock acknowledge API
    await page.route('**/api/alerts/alert-1/acknowledge', async route => {
      await route.fulfill({ json: { success: true } })
    })

    // Click acknowledge button
    await page.click('button:has-text("Acknowledge"):first')
    
    // Verify success message
    await expect(page.locator('text=Alert acknowledged successfully')).toBeVisible()
  })

  test('should resolve alert', async ({ page }) => {
    // Mock resolve API
    await page.route('**/api/alerts/alert-1/resolve', async route => {
      await route.fulfill({ json: { success: true } })
    })

    // Click resolve button
    await page.click('button:has-text("Resolve"):first')
    
    // Confirm resolution in dialog
    await expect(page.locator('text=Resolve Alert')).toBeVisible()
    await page.click('button:has-text("Confirm")')
    
    // Verify success message
    await expect(page.locator('text=Alert resolved successfully')).toBeVisible()
  })

  test('should filter alerts by severity', async ({ page }) => {
    // Open filters
    await page.click('button:has-text("Filters")')
    
    // Select critical severity
    await page.selectOption('[aria-label="Severity"]', 'critical')
    
    // Apply filters
    await page.click('button:has-text("Apply Filters")')
    
    // Verify only critical alerts are shown
    await expect(page.locator('text=High CPU Usage')).toBeVisible()
    await expect(page.locator('text=Memory Usage Warning')).not.toBeVisible()
  })

  test('should sort alerts by different criteria', async ({ page }) => {
    // Change sort order
    await page.selectOption('[aria-label="Sort by"]', 'severity')
    
    // Verify alerts are reordered (critical first)
    const alertTitles = await page.locator('[data-testid="alert-title"]').allTextContents()
    expect(alertTitles[0]).toBe('High CPU Usage') // Critical first
  })

  test('should view alert details', async ({ page }) => {
    // Mock alert detail API
    await page.route('**/api/alerts/alert-1', async route => {
      await route.fulfill({
        json: {
          id: 'alert-1',
          title: 'High CPU Usage',
          description: 'CPU usage is above 90%',
          severity: 'critical',
          status: 'active',
          source: 'prometheus',
          timestamp: '2025-08-16T07:30:00Z',
          labels: { service: 'api-server' },
          tenantId: 'tenant-1',
          history: [
            {
              timestamp: '2025-08-16T07:30:00Z',
              action: 'created',
              user: 'system'
            }
          ],
          relatedAlerts: []
        }
      })
    })

    // Click on alert to view details
    await page.click('text=High CPU Usage')
    
    // Verify detail view
    await expect(page.locator('text=Alert Details')).toBeVisible()
    await expect(page.locator('text=History')).toBeVisible()
  })

  test('should perform bulk operations', async ({ page }) => {
    // Select multiple alerts
    await page.check('[data-testid="alert-checkbox"]:first')
    await page.check('[data-testid="alert-checkbox"]:nth-child(2)')
    
    // Verify bulk actions appear
    await expect(page.locator('text=2 selected')).toBeVisible()
    await expect(page.locator('button:has-text("Acknowledge Selected")')).toBeVisible()
    
    // Mock bulk acknowledge API
    await page.route('**/api/alerts/bulk/acknowledge', async route => {
      await route.fulfill({ json: { success: true } })
    })

    // Perform bulk acknowledge
    await page.click('button:has-text("Acknowledge Selected")')
    
    // Verify success message
    await expect(page.locator('text=Alerts acknowledged successfully')).toBeVisible()
  })

  test('should assign alert to user', async ({ page }) => {
    // Mock assignment API
    await page.route('**/api/alerts/alert-1/assign', async route => {
      await route.fulfill({ json: { success: true } })
    })

    // Click assign button
    await page.click('[aria-label="Assign alert"]:first')
    
    // Select assignee
    await page.selectOption('[aria-label="Assign to"]', 'jane.doe')
    
    // Confirm assignment
    await page.click('button:has-text("Assign")')
    
    // Verify success message
    await expect(page.locator('text=Alert assigned successfully')).toBeVisible()
  })

  test('should handle real-time updates', async ({ page }) => {
    // Simulate new alert via WebSocket
    await page.evaluate(() => {
      // Mock WebSocket message
      window.dispatchEvent(new CustomEvent('alert-update', {
        detail: {
          type: 'new-alert',
          alert: {
            id: 'alert-3',
            title: 'Disk Space Critical',
            severity: 'critical',
            status: 'active'
          }
        }
      }))
    })

    // Verify new alert appears
    await expect(page.locator('text=Disk Space Critical')).toBeVisible()
  })

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    
    // Verify mobile layout
    await expect(page.locator('[data-testid="mobile-alert-list"]')).toBeVisible()
    
    // Verify alerts are still accessible
    await expect(page.locator('text=High CPU Usage')).toBeVisible()
    
    // Test mobile actions
    await page.click('[data-testid="mobile-alert-menu"]:first')
    await expect(page.locator('button:has-text("Acknowledge")')).toBeVisible()
  })

  test('should handle error states', async ({ page }) => {
    // Mock API error
    await page.route('**/api/alerts/alert-1/acknowledge', async route => {
      await route.abort('failed')
    })

    // Try to acknowledge alert
    await page.click('button:has-text("Acknowledge"):first')
    
    // Verify error message
    await expect(page.locator('text=Failed to acknowledge alert')).toBeVisible()
    await expect(page.locator('button:has-text("Retry")')).toBeVisible()
  })
})

test.describe('Alert Accessibility', () => {
  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/alerts')
    
    // Tab through alert list
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')
    
    // Navigate to first alert
    await expect(page.locator('text=High CPU Usage')).toBeFocused()
    
    // Use arrow keys to navigate
    await page.keyboard.press('ArrowDown')
    await expect(page.locator('text=Memory Usage Warning')).toBeFocused()
  })

  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto('/alerts')
    
    // Check ARIA labels
    await expect(page.locator('[aria-label="Alert list"]')).toBeVisible()
    await expect(page.locator('[aria-label="Acknowledge alert"]')).toBeVisible()
    await expect(page.locator('[aria-label="Resolve alert"]')).toBeVisible()
  })

  test('should announce alert actions to screen readers', async ({ page }) => {
    await page.goto('/alerts')
    
    // Mock acknowledge API
    await page.route('**/api/alerts/alert-1/acknowledge', async route => {
      await route.fulfill({ json: { success: true } })
    })

    // Acknowledge alert
    await page.click('button:has-text("Acknowledge"):first')
    
    // Check for ARIA live region updates
    await expect(page.locator('[aria-live="polite"]')).toContainText('Alert acknowledged')
  })

  test('should support high contrast mode', async ({ page }) => {
    // Enable high contrast mode
    await page.emulateMedia({ colorScheme: 'dark', reducedMotion: 'reduce' })
    
    await page.goto('/alerts')
    
    // Verify high contrast styles are applied
    const alertCard = page.locator('[data-testid="alert-card"]:first')
    await expect(alertCard).toHaveCSS('border-width', '2px')
  })
})